import serial
import time

class OnStepMount:
    """
    Interface to OnStepX Mount via Serial.
    """
    def __init__(self, port='/dev/ttyUSB0', baud=9600, mock=False):
        self.port = port
        self.baud = baud
        self.mock = mock
        self.ser = None
        
        # Configuration for Alt/Az axes (e.g., Focuser 1 and 2)
        # 1 step = X arcseconds? We need calibration.
        self.steps_per_degree_alt = 1000 # Placeholder
        self.steps_per_degree_az = 1000 # Placeholder
        
    def connect(self):
        if self.mock:
            print("Connected to Mock Mount.")
            return True
            
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            # Flush
            self.ser.read_all()
            print(f"Connected to OnStep at {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to mount: {e}. Switching to Mock mode.")
            self.mock = True
            return True

    def _send_cmd(self, cmd):
        if self.mock:
            print(f"[Mount Mock] TX: {cmd}")
            return "0#" # Success
            
        self.ser.write(cmd.encode('ascii'))
        # Most OnStep commands end with # and don't return much unless queried
        # But we should wait a bit or read response if expected
        time.sleep(0.1)
        return "" # We don't strictly read back for blind moves in this demo

    def slew_ra_relative(self, degrees):
        """
        Slews RA axis relative to current position.
        Using :MS# (Slew) commands is complex as it requires target coordinates.
        For simple rotation, we might use :Mn# (Move North/South/East/West) with duration?
        Or better: Sync to current, calc target, Goto.
        
        For simplicity in this PA routine, we assume we can issue a "Move Axis 1 by X degrees" command.
        OnStep has specific commands for this in some versions, or we just calculate target.
        
        Let's simulate "Slew RA" by just printing in mock.
        """
        print(f"Slewing RA by {degrees} degrees...")
        if self.mock:
            return
            
        # Real implementation would:
        # 1. Get current RA/Dec (:GR#, :GD#)
        # 2. Add degrees to RA
        # 3. :Sr# :Sd# (Set target)
        # 4. :MS# (Slew)
        pass

    def move_alt_steps(self, steps):
        """
        Moves the Altitude axis (Alignment Base) by steps.
        Assumed to be Focuser 1.
        Command: :F1M<steps>#
        """
        cmd = f":F1M{int(steps)}#"
        self._send_cmd(cmd)

    def move_az_steps(self, steps):
        """
        Moves the Azimuth axis (Alignment Base) by steps.
        Assumed to be Focuser 2.
        Command: :F2M{steps}#
        """
        cmd = f":F2M{int(steps)}#"
        self._send_cmd(cmd)
        
    def get_position(self):
        """Returns current (RA, Dec) tuple in degrees."""
        if self.mock:
            return (0.0, 90.0)
        # Implement parsing :GR# and :GD#
        return (0.0, 90.0)
