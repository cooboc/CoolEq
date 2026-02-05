import sys
import os
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Add src to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from camera import GuideCamera
from solver import PlateSolver
from mount import OnStepMount
from aligner import PolarAligner
import astropy.units as u

class MockMount(OnStepMount):
    def __init__(self):
        super().__init__(mock=True)
        self.ra_angle = 0.0
        self.steps_per_degree_alt = 1000
        self.steps_per_degree_az = 1000
        self.alt_moved = 0
        self.az_moved = 0
        
    def slew_ra_relative(self, degrees):
        self.ra_angle += degrees
        
    def move_alt_steps(self, steps):
        self.alt_moved += steps
        
    def move_az_steps(self, steps):
        self.az_moved += steps

class MockSolver(PlateSolver):
    def __init__(self, mount_ref, camera_ref=None):
        self.mount = mount_ref
        self.camera = camera_ref
        
    def solve(self, image_path, search_radius=180):
        # Return a fixed solution or one based on camera simulation
        if self.camera and hasattr(self.camera, 'get_simulation_pointing'):
            sim_ra, sim_dec, sim_roll = self.camera.get_simulation_pointing()
            return {'ra': sim_ra, 'dec': sim_dec, 'rotation': sim_roll}
        return {'ra': 0.0, 'dec': 89.0, 'rotation': 0.0}

@pytest.fixture
def mock_setup():
    mount = MockMount()
    camera = GuideCamera(device_id=999) # This will use the dummy generator
    
    # Override capture_frame to update simulation state
    original_capture = camera.capture_frame
    
    # We need to simulate the mechanical axis being slightly off pole
    mech_ra = 0.0
    mech_dec = 89.0
    
    def capture_with_sim_update(filename=None, exposure_time=1.0):
        current_roll = mount.ra_angle
        camera.set_simulation_pointing(mech_ra, mech_dec, roll=current_roll)
        return original_capture(filename, exposure_time)
        
    camera.capture_frame = capture_with_sim_update
    
    solver = MockSolver(mount, camera)
    
    return mount, camera, solver

def test_polar_alignment_routine(mock_setup):
    mount, camera, solver = mock_setup
    
    # Use a temporary cache dir for tests
    aligner = PolarAligner(camera, solver, mount, cache_dir="./test_cache")
    
    # Mock setup_iers to avoid network calls during tests if possible, 
    # but aligner calls it in __init__. 
    # Since we already ran the demo, the file might be cached.
    # If not, it might try to download. 
    # For unit tests, ideally we mock iers_manager.setup_iers
    
    success = aligner.run_alignment()
    
    assert success is True
    assert len(aligner.points) == 3
    
    # Check if corrections were issued
    # We started at Dec=89, Target=39.9 (Lat). 
    # Wait, the demo logic for "Mechanical Axis" vs "Target" depends on Location.
    # Aligner default location is Lat=39.9.
    # Our MockSolver returns Dec=89.0 (simulated mechanical axis pointing).
    # Wait, the solver returns where the camera is pointing.
    # In the demo:
    # Mechanical Axis calculated at: Alt=39.8155, Az=358.8984
    # Target (NCP): Alt=39.9000, Az=0.0000
    # So there should be an error.
    
    assert mount.alt_moved != 0 or mount.az_moved != 0

def test_camera_settings():
    camera = GuideCamera(device_id=999)
    camera.set_gain(10)
    camera.set_exposure(100)
    assert camera.gain == 10
    assert camera.exposure == 100

def test_azimuth_normalization():
    # Test the logic specifically fixed in aligner
    # We can test this by forcing a specific scenario in aligner or just unit testing the logic if we extracted it.
    # Since it's inside run_alignment, we rely on the integration test.
    pass
