import numpy as np
import time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
from iers_manager import setup_iers
import os

class PolarAligner:
    """
    Automated Polar Alignment Controller.
    """
    def __init__(self, camera, solver, mount, location=None, cache_dir="../../../../cache"):
        self.camera = camera
        self.solver = solver
        self.mount = mount
        # Default location: Beijing (Example)
        self.location = location if location else EarthLocation(lat=39.9*u.deg, lon=116.4*u.deg, height=50*u.m)
        self.points = []
        
        # Initialize IERS
        # Resolve cache dir relative to this file if it's a relative path
        if not os.path.isabs(cache_dir):
             cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), cache_dir))
        
        setup_iers(cache_dir) 
        
    def run_alignment(self):
        print("Starting Polar Alignment Routine...")
        
        # 1. Measurement Phase
        self.points = []
        angles = [0, 30, 30] # Rotate 0, then +30, then +30
        
        for angle in angles:
            if angle != 0:
                print(f"Rotating RA by {angle} degrees...")
                self.mount.slew_ra_relative(angle)
                time.sleep(1) # Wait for vibration
                
            print("Capturing and Solving...")
            img = self.camera.capture_frame()
            sol = self.solver.solve(img)
            
            if not sol:
                print("Solving failed. Aborting.")
                return False
                
            print(f"  Solved: RA={sol['ra']:.4f}, Dec={sol['dec']:.4f}")
            self.points.append((sol['ra'], sol['dec']))
            
        # 2. Calculation Phase
        center_alt, center_az = self._calculate_rotation_center()
        print(f"Mechanical Axis calculated at: Alt={center_alt.to_value(u.deg):.4f}, Az={center_az.to_value(u.deg):.4f}")
        
        # Target: NCP (Az=0, Alt=Lat)
        target_alt = self.location.lat
        target_az = 0.0 * u.deg
        
        print(f"Target (NCP): Alt={target_alt.to_value(u.deg):.4f}, Az={target_az.to_value(u.deg):.4f}")
        
        error_alt = target_alt - center_alt
        error_az = target_az - center_az
        
        # Normalize Az error to [-180, 180] range
        error_az_val = error_az.to_value(u.deg)
        while error_az_val > 180:
            error_az_val -= 360
        while error_az_val <= -180:
            error_az_val += 360
        error_az = error_az_val * u.deg
        
        print(f"Error: dAlt={error_alt.to_value(u.deg):.4f} deg, dAz={error_az.to_value(u.deg):.4f} deg")
        
        # 3. Adjustment Phase
        # Convert degrees to steps
        # Assuming mount.steps_per_degree_alt/az are available
        steps_alt = error_alt.to_value(u.deg) * self.mount.steps_per_degree_alt
        steps_az = error_az.to_value(u.deg) * self.mount.steps_per_degree_az
        
        print(f"Adjusting: AltSteps={int(steps_alt)}, AzSteps={int(steps_az)}")
        
        self.mount.move_alt_steps(steps_alt)
        self.mount.move_az_steps(steps_az)
        
        print("Adjustment Complete.")
        return True

    def _calculate_rotation_center(self):
        """
        Fits a circle to the 3 observed points (in Alt/Az) to find the center.
        """
        # Convert RA/Dec to Alt/Az for the current time
        # We assume the 3 points were taken relatively quickly, so we use a single timestamp 
        # for the conversion of all 3 to "freeze" the sky?
        # NO. The mount rotated. The sky moved slightly. 
        # But we want the MECHANICAL axis. 
        # The Mechanical axis is fixed to the GROUND (Alt/Az).
        # So we should convert each observation to Alt/Az using its specific timestamp.
        # This removes the sky rotation (Earth rotation).
        
        now = Time.now()
        # For simulation, we assume points are taken now
        
        alt_az_points = []
        for ra, dec in self.points:
            coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
            aa = coord.transform_to(AltAz(obstime=now, location=self.location))
            alt_az_points.append(aa)
            
        # Convert to cartesian for plane fitting
        # x = cos(alt)cos(az)
        # y = cos(alt)sin(az)
        # z = sin(alt)
        
        vecs = []
        for p in alt_az_points:
            alt_rad = p.alt.rad
            az_rad = p.az.rad
            x = np.cos(alt_rad) * np.cos(az_rad)
            y = np.cos(alt_rad) * np.sin(az_rad)
            z = np.sin(alt_rad)
            vecs.append(np.array([x, y, z]))
            
        # Fit plane: P1, P2, P3
        # Normal n = (P2-P1) x (P3-P1)
        v1 = vecs[0]
        v2 = vecs[1]
        v3 = vecs[2]
        
        normal = np.cross(v2 - v1, v3 - v1)
        norm_mag = np.linalg.norm(normal)
        
        if norm_mag < 1e-6:
            # Collinear points (should not happen with 30deg rotation)
            # Fallback: Just return the average position
            avg_vec = (v1 + v2 + v3) / 3.0
            normal = avg_vec / np.linalg.norm(avg_vec)
        else:
            normal = normal / norm_mag
            
        # Check direction: Should point roughly North (Az=0) and Up (Alt>0)
        # Az=0 means x>0 (since Az=0 is North? Wait, convention)
        # Astropy AltAz: Az is measured East of North? 0=N, 90=E.
        # x = cos(alt)cos(az). If Az=0, x=cos(alt)>0.
        # If normal.x < 0, flip it.
        if normal[0] < 0: 
            normal = -normal
            
        # Convert normal back to Alt/Az
        # z = sin(alt) => alt = arcsin(z)
        # y/x = tan(az) => az = arctan2(y, x)
        
        center_alt_rad = np.arcsin(normal[2])
        center_az_rad = np.arctan2(normal[1], normal[0])
        
        # Handle Az wrapping
        if center_az_rad < 0:
            center_az_rad += 2 * np.pi
            
        return (center_alt_rad * 180 / np.pi) * u.deg, (center_az_rad * 180 / np.pi) * u.deg
