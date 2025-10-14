# mitv.py
import subprocess
import logging
import time
from env import EnvConfig

logger = logging.getLogger(__name__)

class MiTV:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._tv_ip = None
        self._load_config()
    
    def _load_config(self):
        """Load MiTV configuration from environment"""
        tv_config = self._config.get_mitv_config()
        self._tv_ip = tv_config.get('ip')
        
        if not self._tv_ip:
            logger.warning("MiTV IP address not found in environment")
        else:
            logger.info(f"MiTV configuration loaded - IP: {self._tv_ip}")
    
    def _run_adb_command(self, command):
        """
        Run ADB command using subprocess
        
        Returns:
            tuple: (success, output)
        """
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error("ADB command timeout")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"Error running ADB command: {str(e)}")
            return False, str(e)
    
    def connect(self):
        """
        Connect to TV via ADB
        """
        if not self._tv_ip:
            logger.error("TV IP not configured")
            return False
        
        # 先断开现有连接
        self._run_adb_command(f"adb disconnect {self._tv_ip}:5555")
        time.sleep(1)
        
        # 连接到设备
        success, output = self._run_adb_command(f"adb connect {self._tv_ip}:5555")
        
        if success and "connected" in output:
            logger.info(f"Successfully connected to TV: {self._tv_ip}")
            return True
        else:
            logger.error(f"Failed to connect to TV: {output}")
            return False
    
    def disconnect(self):
        """
        Disconnect from TV
        """
        if not self._tv_ip:
            return
        
        success, output = self._run_adb_command(f"adb disconnect {self._tv_ip}:5555")
        
        if success:
            logger.info("Disconnected from TV")
        else:
            logger.warning(f"Failed to disconnect: {output}")
    
    def get_screen_state(self):
        """
        Get screen state (ON/OFF)
        
        Returns:
            str: "ON", "OFF", or None if failed
        """
        if not self.connect():
            return None
        
        try:
            # 获取屏幕状态
            command = f'adb -s {self._tv_ip}:5555 shell "dumpsys power | grep \'Display Power:\'"'
            success, output = self._run_adb_command(command)
            
            if success:
                if "state=ON" in output:
                    return "ON"
                elif "state=OFF" in output:
                    return "OFF"
                else:
                    logger.warning(f"Unknown screen state: {output}")
                    return None
            else:
                logger.error(f"Failed to get screen state: {output}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting screen state: {str(e)}")
            return None
        finally:
            self.disconnect()
    
    def send_keyevent(self, keycode):
        """
        Send key event to TV
        
        Args:
            keycode (str or int): ADB keycode (e.g., 26 for POWER)
            
        Returns:
            bool: True if successful
        """
        if not self.connect():
            return False
        
        try:
            # 发送按键事件
            command = f'adb -s {self._tv_ip}:5555 shell input keyevent {keycode}'
            success, output = self._run_adb_command(command)
            
            if success:
                logger.info(f"Key event sent successfully: {keycode}")
                return True
            else:
                logger.error(f"Failed to send key event {keycode}: {output}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send key event {keycode}: {str(e)}")
            return False
        finally:
            self.disconnect()
    
    def power_toggle(self):
        """
        Toggle power (press power button)
        
        Returns:
            bool: True if successful
        """
        return self.send_keyevent(26)  # 26 = KEYCODE_POWER
    
    def smart_power_off(self):
        """
        Smart power off - only turn off if screen is on
        
        Returns:
            bool: True if successful or already off
        """
        screen_state = self.get_screen_state()
        
        if screen_state == "ON":
            logger.info("Screen is ON, turning off...")
            return self.power_toggle()
        elif screen_state == "OFF":
            logger.info("Screen is already OFF")
            return True
        else:
            logger.warning("Could not determine screen state, sending power command anyway")
            return self.power_toggle()
    
    def smart_power_on(self):
        """
        Smart power on - only turn on if screen is off
        
        Returns:
            bool: True if successful or already on
        """
        screen_state = self.get_screen_state()
        
        if screen_state == "OFF":
            logger.info("Screen is OFF, turning on...")
            return self.power_toggle()
        elif screen_state == "ON":
            logger.info("Screen is already ON")
            return True
        else:
            logger.warning("Could not determine screen state, sending power command anyway")
            return self.power_toggle()
    
    def is_connected(self):
        """
        Check if TV is connected via ADB
        
        Returns:
            bool: True if connected
        """
        if not self._tv_ip:
            return False
        
        success, output = self._run_adb_command("adb devices")
        if success:
            return f"{self._tv_ip}:5555" in output
        return False
    
    @property
    def is_configured(self):
        """Check if MiTV is properly configured"""
        return bool(self._tv_ip)
    
    @property
    def tv_ip(self):
        """Get TV IP address"""
        return self._tv_ip


# Test function
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing MiTV control...")
    
    tv = MiTV()
    
    # Check configuration
    print(f"MiTV configured: {tv.is_configured}")
    if tv.is_configured:
        print(f"TV IP: {tv.tv_ip}")
        
        # Test screen state
        print("\n1. Checking screen state...")
        state = tv.get_screen_state()
        print(f"Screen state: {state}")
        
        # Test smart power off
        print("\n2. Testing smart power off...")
        if tv.smart_power_off():
            print("Smart power off completed")
        else:
            print("Smart power off failed")
        
        # Wait and check state again
        time.sleep(2)
        state = tv.get_screen_state()
        print(f"Screen state after power off: {state}")
        
    else:
        print("MiTV not configured properly. Please check .env file")


if __name__ == "__main__":
    main()