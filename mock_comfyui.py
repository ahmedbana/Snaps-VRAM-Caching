"""
Mock ComfyUI modules for testing purposes
"""

import os
import tempfile

class MockFolderPaths:
    """Mock folder_paths module"""
    
    @staticmethod
    def get_temp_directory():
        return tempfile.gettempdir()
    
    @staticmethod
    def get_filename_list(folder_type):
        return ["test_model.safetensors", "another_model.safetensors"]
    
    @staticmethod
    def get_full_path(folder_type, filename):
        return os.path.join("/tmp", filename)

# Create mock modules
folder_paths = MockFolderPaths() 