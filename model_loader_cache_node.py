import torch
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

class ModelLoaderCacheNode:
    """Node that integrates with ComfyUI's model loading system for VRAM caching"""
    
    def __init__(self):
        self.cache_manager = cache_manager
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("checkpoints"), ),
                "cache_enabled": ("BOOLEAN", {"default": True}),
                "clear_cache": ("BOOLEAN", {"default": False}),
                "unlimited_cache": ("BOOLEAN", {"default": False}),
                "max_cache_size_gb": ("FLOAT", {"default": 8.0, "min": 0.1, "max": 32.0, "step": 0.1}),
                "force_reload": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "cache_status", "was_cached", "cache_stats")
    FUNCTION = "load_model"
    CATEGORY = "VRAM Cache"
    
    def load_model(self, model_name: str, cache_enabled: bool, clear_cache: bool, unlimited_cache: bool, max_cache_size_gb: float, force_reload: bool):
        """Load a model with VRAM caching support"""
        
        # Handle unlimited cache setting
        if unlimited_cache:
            self.cache_manager.set_unlimited_cache(True)
        else:
            self.cache_manager.set_max_cache_size(max_cache_size_gb)
        
        # Handle cache clearing
        if clear_cache:
            self.cache_manager.clear_cache()
            return (None, None, None, "Cache cleared", False, "Cache cleared")
        
        # Get the full model path
        model_path = folder_paths.get_full_path("checkpoints", model_name)
        
        if not os.path.exists(model_path):
            stats = self.cache_manager.get_cache_stats()
            if stats.get('unlimited_cache', False):
                stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
            else:
                stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
            return (None, None, None, f"Model not found: {model_name}", False, stats_str)
        
        was_cached = False
        
        if cache_enabled and not force_reload:
            # Try to load from VRAM cache first
            cached_model = self.cache_manager.access_model(model_path)
            if cached_model is not None:
                was_cached = True
                cache_status = f"Loaded from VRAM cache: {model_name}"
                
                # Return cached model components
                model, clip, vae = self._extract_model_components(cached_model)
            else:
                # Load model normally and cache it
                model, clip, vae = self._load_model_components(model_path)
                if model is not None:
                    # Cache the entire model state
                    model_state = {
                        'model': model,
                        'clip': clip,
                        'vae': vae,
                        'path': model_path
                    }
                    self.cache_manager.cache_model(model_path, model_state)
                    cache_status = f"Cached in VRAM: {model_name}"
                else:
                    cache_status = f"Failed to load model: {model_name}"
        else:
            # Load model normally (cache disabled or force reload)
            model, clip, vae = self._load_model_components(model_path)
            if model is not None and cache_enabled:
                # Cache the model even if force reload was used
                model_state = {
                    'model': model,
                    'clip': clip,
                    'vae': vae,
                    'path': model_path
                }
                self.cache_manager.cache_model(model_path, model_state)
                cache_status = f"Loaded and cached: {model_name}"
            else:
                cache_status = f"Loaded normally: {model_name}"
        
        # Get cache statistics
        stats = self.cache_manager.get_cache_stats()
        if stats.get('unlimited_cache', False):
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
        else:
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
        
        return (model, clip, vae, cache_status, was_cached, stats_str)
    
    def _load_model_components(self, model_path: str) -> tuple:
        """Load model components using ComfyUI's model loading system"""
        try:
            # This is a simplified version - in practice, you'd use ComfyUI's actual model loading
            # For now, we'll return None to indicate that the model needs to be loaded normally
            return (None, None, None)
        except Exception as e:
            print(f"Error loading model: {e}")
            return (None, None, None)
    
    def _extract_model_components(self, cached_model: Dict[str, Any]) -> tuple:
        """Extract model components from cached model state"""
        if isinstance(cached_model, dict):
            return (
                cached_model.get('model'),
                cached_model.get('clip'),
                cached_model.get('vae')
            )
        return (None, None, None)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Return a hash to determine if the node should be re-executed"""
        return hash(str(kwargs))

class VRAMCacheControlNode:
    """Control node for managing VRAM cache settings"""
    
    def __init__(self):
        self.cache_manager = cache_manager
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["get_stats", "clear_cache", "set_size", "set_unlimited"], ),
                "unlimited_cache": ("BOOLEAN", {"default": False}),
                "max_cache_size_gb": ("FLOAT", {"default": 8.0, "min": 0.1, "max": 32.0, "step": 0.1}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("action_result", "cache_stats")
    FUNCTION = "control_cache"
    CATEGORY = "VRAM Cache"
    
    def control_cache(self, action: str, unlimited_cache: bool, max_cache_size_gb: float):
        """Control VRAM cache operations"""
        
        if action == "clear_cache":
            self.cache_manager.clear_cache()
            result = "Cache cleared successfully"
        elif action == "set_size":
            if unlimited_cache:
                self.cache_manager.set_unlimited_cache(True)
                result = "Cache size set to unlimited"
            else:
                self.cache_manager.set_max_cache_size(max_cache_size_gb)
                result = f"Cache size set to {max_cache_size_gb} GB"
        elif action == "set_unlimited":
            self.cache_manager.set_unlimited_cache(unlimited_cache)
            if unlimited_cache:
                result = "Cache size set to unlimited"
            else:
                result = f"Cache size set to {max_cache_size_gb} GB"
        else:  # get_stats
            result = "Cache statistics retrieved"
        
        # Get current cache statistics
        stats = self.cache_manager.get_cache_stats()
        if stats.get('unlimited_cache', False):
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB (Unlimited)"
        else:
            stats_str = f"Models: {stats['total_models']}, Size: {stats['current_size_mb']:.1f}MB/{stats['max_size_mb']:.1f}MB ({stats['cache_usage_percent']:.1f}%)"
        
        return (result, stats_str)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Return a hash to determine if the node should be re-executed"""
        return hash(str(kwargs)) 