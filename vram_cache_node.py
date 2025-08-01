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
                "load_path": ("STRING", {"default": "", "multiline": False}),
                "cache_enabled": ("BOOLEAN", {"default": True}),
                "clear_cache": ("BOOLEAN", {"default": False}),
                "unlimited_cache": ("BOOLEAN", {"default": False}),
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
    
    def process_model(self, load_path: str, cache_enabled: bool, clear_cache: bool, unlimited_cache: bool, max_cache_size_gb: float, model_data: Optional[Any] = None):
        """Main processing function for the VRAM cache node"""
        
        # Handle unlimited cache setting
        if unlimited_cache:
            self.cache_manager.set_unlimited_cache(True)
        else:
            self.cache_manager.set_max_cache_size(max_cache_size_gb)
        
        # Handle cache clearing
        if clear_cache:
            self.cache_manager.clear_cache()
            return (None, "Cache cleared", False, "Cache cleared")
        
        # If no load path provided, return the input model data
        if not load_path:
            stats = self.cache_manager.get_cache_stats()
            if stats.get('unlimited_cache', False):
                stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
            else:
                stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
            return (model_data, "No load path provided", False, stats_str)
        
        # Get the actual model path from the load path
        model_path = self._get_model_path_from_load_path(load_path)
        
        # Check if model exists
        if not os.path.exists(model_path):
            stats = self.cache_manager.get_cache_stats()
            if stats.get('unlimited_cache', False):
                stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
            else:
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
        if stats.get('unlimited_cache', False):
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
        else:
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
        
        return (model_data, cache_status, was_cached, stats_str)
    
    def _get_model_path_from_load_path(self, load_path: str) -> str:
        """Extract the actual model path from the load path input"""
        # Handle different load path formats
        if load_path.startswith('"') and load_path.endswith('"'):
            # Remove quotes if present
            load_path = load_path[1:-1]
        
        # If it's already a full path, return it
        if os.path.isabs(load_path):
            return load_path
        
        # Try to get the full path using ComfyUI's folder_paths
        try:
            # Check if it's a checkpoint
            if load_path.endswith(('.safetensors', '.ckpt', '.pt')):
                return folder_paths.get_full_path("checkpoints", load_path)
            # Check if it's a VAE
            elif 'vae' in load_path.lower():
                return folder_paths.get_full_path("vae", load_path)
            # Check if it's a LoRA
            elif 'lora' in load_path.lower():
                return folder_paths.get_full_path("loras", load_path)
            # Default to checkpoints
            else:
                return folder_paths.get_full_path("checkpoints", load_path)
        except:
            # If folder_paths fails, try to construct the path
            return os.path.join(folder_paths.get_folder_paths("checkpoints")[0], load_path)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Return a hash to determine if the node should be re-executed"""
        return hash(str(kwargs)) 