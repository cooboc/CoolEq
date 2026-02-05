import sys
import os
import math
import time
import numpy as np

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Path to src/function/PolarAlignment/src
src_path = os.path.abspath(os.path.join(current_dir, "../src/function/PolarAlignment/src"))
sys.path.append(src_path)

from camera import GuideCamera
from solver import PlateSolver
from mount import OnStepMount
from aligner import PolarAligner

class MockMount(OnStepMount):
    def __init__(self):
        super().__init__(mock=True)
        self.ra_angle = 0.0 # Degrees
        self.steps_per_degree_alt = 1000
        self.steps_per_degree_az = 1000
        
    def slew_ra_relative(self, degrees):
        print(f"[MockMount] Slewing RA by {degrees} deg")
        self.ra_angle += degrees
        
    def move_alt_steps(self, steps):
        print(f"[MockMount] Moving Alt by {steps} steps ({steps/self.steps_per_degree_alt:.4f} deg)")
        
    def move_az_steps(self, steps):
        print(f"[MockMount] Moving Az by {steps} steps ({steps/self.steps_per_degree_az:.4f} deg)")

class MockSolver(PlateSolver):
    def __init__(self, mount_ref, camera_ref=None):
        self.mount = mount_ref
        self.camera = camera_ref
        
    def solve(self, image_path, search_radius=180):
        # If we have a camera reference with simulation capability, ask it where it was pointing.
        # This ensures the solution matches the visual star field.
        if self.camera and hasattr(self.camera, 'get_simulation_pointing'):
            sim_ra, sim_dec, sim_roll = self.camera.get_simulation_pointing()
            
            # Add some "solver noise" to simulate real world imperfection
            ra = sim_ra + np.random.normal(0, 0.0001)
            dec = sim_dec + np.random.normal(0, 0.0001)
            
            return {'ra': ra, 'dec': dec, 'rotation': sim_roll}
            
        # Fallback to old logic if no camera link (Legacy/Unit test without camera)
        angle_rad = math.radians(self.mount.ra_angle)
        # ... (Old logic omitted for brevity, we assume camera is linked in this demo)
        return {'ra': 0, 'dec': 90, 'rotation': 0}

def main():
    print("=== CoolEq Polar Alignment Demo ===")
    
    # Initialize Simulation Hardware
    mount = MockMount()
    camera = GuideCamera(device_id=999) # Will warn and use dummy
    
    # Configure Camera settings (Demo)
    print("Configuring camera gain and exposure...")
    camera.set_gain(10.0)
    camera.set_exposure(100.0)
    
    # Define Mechanical Axis (Simulating misalignment)
    # True Pole is 90. Mechanical Axis is at 89.0
    mech_ra = 0.0
    mech_dec = 89.0
    
    # Hook: Update camera pointing whenever we are about to capture
    # In a real app, this happens physically. Here we must drive the simulation.
    # We can't easily hook into 'aligner' internal loop without modifying it.
    # BUT, 'aligner' calls 'camera.capture_frame()'.
    # We can override capture_frame or use a property.
    
    # Better approach: We pass a "smart" camera to aligner, or we update simulation state in a background thread?
    # Simplest: Override capture_frame in this instance or subclass.
    
    original_capture = camera.capture_frame
    
    def capture_with_sim_update(filename=None, exposure_time=1.0):
        # Update simulation state based on Mount status
        # Assuming camera is fixed on mount RA axis.
        # When Mount RA rotates, Camera Rolls.
        # Center of camera = Mechanical Axis.
        
        # NOTE: If the camera is slightly off-axis (cone error), the center also moves.
        # Let's assume on-axis for simplicity as requested, 
        # BUT user wanted "solve all over region", implying general pointing.
        # For PA demo, we just assume pointing at mech_ra, mech_dec.
        
        current_roll = mount.ra_angle
        camera.set_simulation_pointing(mech_ra, mech_dec, roll=current_roll)
        
        return original_capture(filename, exposure_time)
        
    camera.capture_frame = capture_with_sim_update
    
    solver = MockSolver(mount, camera)
    
    # Initialize Aligner
    aligner = PolarAligner(camera, solver, mount)
    
    # Initialize Aligner
    # We use default location (Beijing)
    # Note: cache_dir is relative to src/function/PolarAlignment/src inside aligner.py by default
    # But we should pass the project root cache for clarity if possible.
    # The default "../../../../cache" works if running from src... 
    # Let's rely on the default which resolves to workspace/CoolEq/cache
    aligner = PolarAligner(camera, solver, mount)
    
    # Run
    success = aligner.run_alignment()
    
    if success:
        print("\nAlignment Routine Finished Successfully.")
    else:
        print("\nAlignment Routine Failed.")

if __name__ == "__main__":
    main()
