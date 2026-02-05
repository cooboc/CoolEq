import cv2
import os
import time
import numpy as np
import math
from astropy.coordinates import SkyCoord
from astropy import units as u

class GuideCamera:
    """
    Interface for the guide camera using OpenCV.
    Responsible for capturing images from the guide scope.
    """
    
    # Static catalog of key stars (RA deg, Dec deg, Mag)
    # Includes NCP region, SCP region, and a few bright stars
    CATALOG = [
        # NCP
        (37.9545, 89.2641, 2.0),   # Polaris
        (259.237, 89.037, 6.4),    # Lambda UMi
        (263.054, 86.586, 4.35),   # Delta UMi (Yildun)
        
        # SCP
        (317.0, -88.95, 5.45),     # Sigma Octantis
        (0.0, -90.0, 99.0),        # SCP Marker (invisible, for ref)
        (220.0, -80.0, 3.0),       # Random brightish star
    ]

    def __init__(self, device_id=0, cache_dir="../../../../cache"):
        """
        Initialize the camera.
        
        Args:
            device_id (int): The camera device ID (default 0).
            cache_dir (str): Relative path to the cache directory.
        """
        self.device_id = device_id
        # Resolve absolute path for cache
        # Current file is in src/function/PolarAlignment/src/
        self.cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), cache_dir))
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        self.gain = None
        self.exposure = None
        
        # Simulation State
        self.sim_ra = 0.0
        self.sim_dec = 90.0
        self.sim_roll = 0.0
        self.sim_fov_deg = 3.0 # Approx FOV for typical guide scope

    def set_simulation_pointing(self, ra, dec, roll=0.0):
        """Sets the pointing direction for the camera simulation."""
        self.sim_ra = ra
        self.sim_dec = dec
        self.sim_roll = roll
        
    def get_simulation_pointing(self):
        """Returns the current simulated pointing (ra, dec, roll)."""
        return self.sim_ra, self.sim_dec, self.sim_roll

    def set_gain(self, value):
        """
        Sets the gain for the camera.
        
        Args:
            value (float): Gain value.
        """
        self.gain = value
        print(f"Camera gain set to {self.gain}")

    def set_exposure(self, value):
        """
        Sets the exposure value for the camera.
        
        Args:
            value (float): Exposure value.
        """
        self.exposure = value
        print(f"Camera exposure set to {self.exposure}")
            
    def capture_frame(self, filename=None, exposure_time=1.0):
        """
        Captures a single frame and saves it to the cache directory.
        
        Args:
            filename (str, optional): Name of the file to save. If None, generates timestamped name.
            exposure_time (float): Simulated exposure time (sleep). Real exposure control depends on camera.
            
        Returns:
            str: Absolute path to the saved image file.
            
        Raises:
            RuntimeError: If camera cannot be opened or frame capture fails.
        """
        if filename is None:
            filename = f"capture_{int(time.time())}.jpg"
            
        filepath = os.path.join(self.cache_dir, filename)
        
        # In a real scenario, we would set exposure time using v4l2 or camera props
        # cap.set(cv2.CAP_PROP_EXPOSURE, ...)
        
        cap = cv2.VideoCapture(self.device_id)
        if not cap.isOpened():
            # Fallback for testing without camera: Generate a noise image with some "stars"
            print(f"Warning: Camera {self.device_id} not found. Generating dummy star field.")
            return self._generate_dummy_image(filepath)
            
        # Apply settings if provided
        if self.gain is not None:
            try:
                cap.set(cv2.CAP_PROP_GAIN, self.gain)
            except Exception as e:
                print(f"Warning: Failed to set gain: {e}")

        if self.exposure is not None:
            try:
                # Attempt to set manual exposure mode (0.25 is common for V4L2 manual)
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) 
                cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
            except Exception as e:
                print(f"Warning: Failed to set exposure: {e}")
            
        # Warmup / Flush buffer
        for _ in range(5):
            cap.read()
            
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise RuntimeError("Failed to capture frame from camera")
            
        # Save as grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(filepath, gray)
        
        print(f"Captured frame saved to {filepath}")
        return filepath

    def _generate_dummy_image(self, filepath):
        """
        Generates a star field image based on simulation state.
        Uses a combination of real catalog stars (NCP/SCP) and procedurally generated stars.
        """
        height, width = 480, 640
        img = np.zeros((height, width), dtype=np.uint8)
        
        # Add random sensor noise
        noise = np.random.randint(0, 20, (height, width), dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Center of the image in Sky Coordinates
        ra0 = math.radians(self.sim_ra)
        dec0 = math.radians(self.sim_dec)
        roll_rad = math.radians(self.sim_roll)
        
        # FOV in radians
        fov_rad = math.radians(self.sim_fov_deg)
        scale = width / fov_rad  # pixels per radian approx
        
        # 1. Project Catalog Stars
        stars_to_draw = []
        for (ra, dec, mag) in self.CATALOG:
            stars_to_draw.append((ra, dec, mag))
            
        # 2. Generate Procedural Stars (Consistent for this RA/Dec region)
        # Use a grid-based approach or just seeded random based on pointing
        # For simplicity, we seed based on integer degrees of pointing
        # This gives a consistent field "per degree". For smoother transition we'd need a spatial hash.
        # But "all over the region" usually implies static shots.
        seed_val = int(self.sim_ra * 10) ^ int(self.sim_dec * 10)
        rng = np.random.RandomState(seed_val)
        
        num_random = 30
        # Generate random stars within FOV roughly
        # This is a hack: we generate them in RA/Dec relative to center
        for _ in range(num_random):
            d_ra = rng.uniform(-self.sim_fov_deg, self.sim_fov_deg)
            d_dec = rng.uniform(-self.sim_fov_deg, self.sim_fov_deg)
            
            s_ra = self.sim_ra + d_ra
            s_dec = self.sim_dec + d_dec
            s_mag = rng.uniform(5, 10)
            stars_to_draw.append((s_ra, s_dec, s_mag))
            
        # Projection Logic (Standard Coordinates / Tangent Plane)
        # (X, Y) on plane perpendicular to pointing vector
        sin_dec0 = math.sin(dec0)
        cos_dec0 = math.cos(dec0)
        
        for (ra_deg, dec_deg, mag) in stars_to_draw:
            ra = math.radians(ra_deg)
            dec = math.radians(dec_deg)
            
            sin_dec = math.sin(dec)
            cos_dec = math.cos(dec)
            cos_d_ra = math.cos(ra - ra0)
            sin_d_ra = math.sin(ra - ra0)
            
            # Gnomonic projection formulas
            # denom = sin(dec)*sin(dec0) + cos(dec)*cos(dec0)*cos(ra-ra0)
            denom = sin_dec * sin_dec0 + cos_dec * cos_dec0 * cos_d_ra
            
            if denom <= 0: continue # Behind the camera
            
            xi = (cos_dec * sin_d_ra) / denom
            eta = (sin_dec * cos_dec0 - cos_dec * sin_dec0 * cos_d_ra) / denom
            
            # Apply Roll (Rotation of the camera)
            # x' = x cos(roll) - y sin(roll)
            # y' = x sin(roll) + y cos(roll)
            # Note: Astronomy roll convention might vary.
            cos_roll = math.cos(roll_rad)
            sin_roll = math.sin(roll_rad)
            
            x_rot = xi * cos_roll - eta * sin_roll
            y_rot = xi * sin_roll + eta * cos_roll
            
            # Convert to pixels (0,0 is center)
            # In image coords, y is usually down. Sky coords eta is up (North).
            # So we invert y.
            px = int(width / 2 + x_rot * scale)
            py = int(height / 2 - y_rot * scale)
            
            if 0 <= px < width and 0 <= py < height:
                # brightness inversely proportional to magnitude
                # Mag 2 -> Bright, Mag 10 -> Dim
                # simple mapping
                brightness = max(50, min(255, int(255 - (mag - 2) * 20)))
                radius = max(1, int(4 - mag/3))
                cv2.circle(img, (px, py), radius, brightness, -1)
            
        cv2.imwrite(filepath, img)
        return filepath
