"""
Settings management for the pattern nesting application.
Handles saving and loading application settings.
"""
import os
import json


class SettingsManager:
    """Manages application settings like file paths and preferences"""
    
    def __init__(self):
        """Initialize the settings manager with default settings location"""
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".pattern_nesting")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.settings = {}
        
        # Create settings directory if it doesn't exist
        os.makedirs(self.settings_dir, exist_ok=True)
        
        # Load existing settings if available
        self.load_settings()
    
    def save_settings(self, settings_dict=None):
        """
        Save settings to file
        
        Args:
            settings_dict (dict, optional): Dictionary of settings to save.
                If None, saves the current settings
        """
        try:
            if settings_dict is not None:
                self.settings.update(settings_dict)
                
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
            print(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"Failed to save settings: {str(e)}")
            return False
    
    def load_settings(self):
        """
        Load settings from file
        
        Returns:
            dict: The loaded settings
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                print(f"Settings loaded from {self.settings_file}")
            else:
                # Initialize with default settings
                self.settings = {
                    "nesting_program": "",
                    "recent_files": [],
                    "default_width": 50,
                    "default_efficiency": 80,
                    "default_time_limit": 1
                }
            return self.settings
        except Exception as e:
            print(f"Failed to load settings: {str(e)}")
            # Initialize with default settings on error
            self.settings = {
                "nesting_program": "",
                "recent_files": [],
                "default_width": 50,
                "default_efficiency": 80,
                "default_time_limit": 1
            }
            return self.settings
    
    def get(self, key, default=None):
        """
        Get a specific setting value
        
        Args:
            key (str): The setting key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            The setting value or default if not found
        """
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """
        Set a specific setting value
        
        Args:
            key (str): The setting key to set
            value: The value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.settings[key] = value
        return self.save_settings()
    
    def add_recent_file(self, file_path):
        """
        Add a file to the recent files list
        
        Args:
            file_path (str): Path to the file to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        recent_files = self.settings.get("recent_files", [])
        
        # Remove if already exists (to move it to the top)
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add to the beginning of the list
        recent_files.insert(0, file_path)
        
        # Keep only the 10 most recent files
        self.settings["recent_files"] = recent_files[:10]
        
        return self.save_settings()