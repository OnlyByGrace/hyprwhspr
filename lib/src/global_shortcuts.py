"""
Global shortcuts handler for hyprwhspr
Manages system-wide keyboard shortcuts for dictation control via D-Bus
"""

import threading
from typing import Callable, Optional
from gi.repository import GLib
from pydbus import SessionBus


class DictationService:
    """
    <node>
      <interface name='com.hyprwhspr.Dictation'>
        <method name='Trigger'/>
      </interface>
    </node>
    """
    
    def __init__(self, handler):
        self.handler = handler
    
    def Trigger(self):
        print("D-Bus trigger received")
        if self.handler:
            # Run callback in a separate thread to avoid blocking D-Bus
            callback_thread = threading.Thread(target=self.handler, daemon=True)
            callback_thread.start()


class GlobalShortcuts:
    """Handles global keyboard shortcuts via D-Bus integration with Hyprland"""
    
    def __init__(self, primary_key: str = '<f12>', callback: Optional[Callable] = None, device_path: Optional[str] = None):
        self.primary_key = primary_key
        self.callback = callback
        
        # D-Bus components
        self.dbus_service = None
        self.dbus_loop = None
        self.listener_thread = None
        self.is_running = False
        
        print(f"Global shortcuts initialized with key: {primary_key}")
        print("Using D-Bus for shortcut handling")
    
    def _dbus_loop_thread(self):
        """Run the D-Bus main loop in a separate thread"""
        try:
            bus = SessionBus()
            self.dbus_service = DictationService(self.callback)
            # Publish with the correct path
            bus.publish("com.hyprwhspr.Dictation", ("/com/hyprwhspr/Dictation", self.dbus_service))
            
            self.dbus_loop = GLib.MainLoop()
            print("D-Bus service started: com.hyprwhspr.Dictation at /com/hyprwhspr/Dictation")
            self.dbus_loop.run()
        except Exception as e:
            print(f"Error in D-Bus loop: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
    
    def start(self) -> bool:
        """Start listening for global shortcuts via D-Bus"""
        if self.is_running:
            return True
            
        try:
            self.listener_thread = threading.Thread(target=self._dbus_loop_thread, daemon=True)
            self.listener_thread.start()
            self.is_running = True
            
            print(f"Global shortcuts started, listening for {self.primary_key} via D-Bus")
            return True
            
        except Exception as e:
            print(f"Failed to start global shortcuts: {e}")
            return False
    
    def stop(self):
        """Stop listening for global shortcuts"""
        if not self.is_running:
            return
            
        try:
            if self.dbus_loop:
                self.dbus_loop.quit()
            
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=1.0)
            
            self.is_running = False
            print("Global shortcuts stopped")
            
        except Exception as e:
            print(f"Error stopping global shortcuts: {e}")
    
    def is_active(self) -> bool:
        """Check if global shortcuts are currently active"""
        return self.is_running and self.listener_thread and self.listener_thread.is_alive()
    
    def set_callback(self, callback: Callable):
        """Set the callback function for shortcut activation"""
        self.callback = callback
        if self.dbus_service:
            self.dbus_service.handler = callback
    
    def update_shortcut(self, new_key: str) -> bool:
        """Update the shortcut key combination (update Hyprland config manually)"""
        self.primary_key = new_key
        print(f"Updated shortcut to: {new_key}")
        print("Remember to update your Hyprland bindings.conf accordingly")
        return True
    
    def get_status(self) -> dict:
        """Get the current status of global shortcuts"""
        return {
            'is_running': self.is_running,
            'is_active': self.is_active(),
            'primary_key': self.primary_key,
            'method': 'dbus'
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.stop()
        except:
            pass


if __name__ == "__main__":
    # Simple test when run directly
    def test_callback():
        print("Global shortcut activated via D-Bus!")
    
    shortcuts = GlobalShortcuts('SUPER+D', test_callback)
    
    if shortcuts.start():
        import time
        time.sleep(0.5)  # Give D-Bus time to register
        print("\nD-Bus service running. Test with:")
        print("  dbus-send --session --type=method_call --dest=com.hyprwhspr.Dictation /com/hyprwhspr/Dictation com.hyprwhspr.Dictation.Trigger")
        print("\nOr press Ctrl+C to exit...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
    
    shortcuts.stop()
