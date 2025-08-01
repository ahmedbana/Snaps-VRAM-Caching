"""
Compatibility layer for ComfyUI dependencies
"""

import os
import tempfile

try:
    import folder_paths
except ImportError:
    # Create a mock folder_paths if not available
    class MockFolderPaths:
        @staticmethod
        def get_temp_directory():
            return tempfile.gettempdir()
        
        @staticmethod
        def get_filename_list(folder_type):
            return ["test_model.safetensors", "another_model.safetensors"]
        
        @staticmethod
        def get_full_path(folder_type, filename):
            return os.path.join("/tmp", filename)
    
    folder_paths = MockFolderPaths() 