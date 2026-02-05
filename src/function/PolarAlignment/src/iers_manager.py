import os
import requests
import time
import shutil
from astropy.utils import iers
from astropy import units as u
import astropy_iers_data

def setup_iers(cache_dir, download_if_missing=True, max_age_days=7):
    """
    Configures Astropy to use a local IERS 'finals2000A.all' file.
    Downloads the file if it's missing or outdated.
    """
    filename = "finals2000A.all"
    url = "https://datacenter.iers.org/data/9/finals2000A.all"
    file_path = os.path.join(cache_dir, filename)
    
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    should_download = False
    if not os.path.exists(file_path):
        should_download = True
        print(f"IERS file missing: {file_path}")
    else:
        # Check age
        mtime = os.path.getmtime(file_path)
        age_days = (time.time() - mtime) / (24 * 3600)
        if age_days > max_age_days:
            should_download = True
            print(f"IERS file outdated ({age_days:.1f} days old).")
            
    if should_download and download_if_missing:
        print(f"Downloading IERS data from {url}...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"IERS data saved to {file_path}")
        except Exception as e:
            print(f"Failed to download IERS data: {e}")
            
            # Fallback: Copy from astropy_iers_data if available
            bundled_path = os.path.join(os.path.dirname(astropy_iers_data.__file__), 'data', 'finals2000A.all')
            if os.path.exists(bundled_path):
                print(f"Falling back to bundled IERS data from {bundled_path}")
                shutil.copy(bundled_path, file_path)
            else:
                if not os.path.exists(file_path):
                    raise RuntimeError("Critical: IERS file missing, download failed, and no bundled backup found.")
    
    # Configure Astropy
    print(f"Loading IERS table from {file_path}...")
    try:
        iers_table = iers.IERS_A.open(file_path)
        iers.earth_orientation_table.set(iers_table)
        iers.conf.auto_download = False
        print("Astropy IERS configuration updated.")
    except Exception as e:
        print(f"Error loading IERS table: {e}")
        raise
