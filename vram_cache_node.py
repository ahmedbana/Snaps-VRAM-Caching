import torch
import hashlib
import os
import json
from typing import Dict, Any, Optional, Union

# Import compatibility layer
try:
    import folder_paths
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from compat import folder_paths

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vram_cache_manager import cache_manager

class VRAMCacheNode:
    def __init__(self):
        self.cache_manager = cache_manager
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("STRING", {"default": "", "multiline": False}),
                "cache_enabled": ("BOOLEAN", {"default": True}),
                "clear_cache": ("BOOLEAN", {"default": False}),
                "max_cache_size_gb": ("FLOAT", {"default": 8.0, "min": 0.1, "max": 32.0, "step": 0.1}),
            },
            "optional": {
                "model_data": ("MODEL",),
            }
        }
    
    RETURN_TYPES = ("MODEL", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("model", "cache_status", "was_cached", "cache_stats")
    FUNCTION = "process_model"
    CATEGORY = "VRAM Cache"
    
    def process_model(self, model_path: str, cache_enabled: bool, clear_cache: bool, max_cache_size_gb: float, model_data: Optional[Any] = None):
        """Main processing function for the VRAM cache node"""
        
        # Update cache size limit
        self.cache_manager.set_max_cache_size(max_cache_size_gb)
        
        # Handle cache clearing
        if clear_cache:
            self.cache_manager.clear_cache()
            return (None, "Cache cleared", False, "Cache cleared")
        
        # If no model path provided, return the input model data
        if not model_path:
            stats = self.cache_manager.get_cache_stats()
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
            return (model_data, "No model path provided", False, stats_str)
        
        # Check if model exists
        if not os.path.exists(model_path):
            stats = self.cache_manager.get_cache_stats()
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
            return (model_data, f"Model not found: {model_path}", False, stats_str)
        
        was_cached = False
        
        if cache_enabled:
            # Try to load from VRAM cache first
            cached_model = self.cache_manager.access_model(model_path)
            if cached_model is not None:
                was_cached = True
                cache_status = f"Loaded from VRAM cache: {os.path.basename(model_path)}"
            else:
                # Load model normally and cache it
                if model_data is not None:
                    self.cache_manager.cache_model(model_path, model_data)
                    cache_status = f"Cached in VRAM: {os.path.basename(model_path)}"
                else:
                    cache_status = f"Model loaded but not cached (no model_data): {os.path.basename(model_path)}"
        else:
            cache_status = f"Cache disabled, loaded normally: {os.path.basename(model_path)}"
        
        # Get cache statistics
        stats = self.cache_manager.get_cache_stats()
        stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
        
        return (model_data, cache_status, was_cached, stats_str)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Return a hash to determine if the node should be re-executed"""
        return hash(str(kwargs)) 