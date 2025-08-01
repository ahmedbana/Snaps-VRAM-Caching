import torch
import os
import logging
import hashlib
from typing import Dict, Any, Optional
from .vram_cache_node import VRAMCache

logger = logging.getLogger(__name__)

class ModelLoaderCacheNode:
    """ComfyUI node for loading specific types of models and caching them in VRAM"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "model_name": ("STRING", {"default": "model", "multiline": False}),
                "model_type": (["auto", "checkpoint", "lora", "vae", "controlnet", "clip"], {"default": "auto"}),
                "force_reload": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("model", "cache_status", "model_type")
    FUNCTION = "load_model"
    CATEGORY = "VRAM Cache"
    
    def get_cache_key(self, model_name: str, model_data: Any) -> str:
        """Generate a unique cache key for the model data"""
        # Create a hash based on model name and data structure
        try:
            # Try to create a hash from the model data
            if hasattr(model_data, 'keys'):
                # For dict-like objects (like state_dict)
                data_str = str(sorted(model_data.keys()))
            else:
                # For other objects, use string representation
                data_str = str(model_data)
            
            key_data = f"{model_name}_{data_str}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except:
            # Fallback to just the model name
            return hashlib.md5(model_name.encode()).hexdigest()
    
    def load_model(self, model, model_name: str = "model", model_type: str = "auto", force_reload: bool = False):
        """Load model data and cache it in VRAM"""
        cache = VRAMCache()
        
        if model is None:
            logger.error(f"Model data is None for model: {model_name}")
            return (None, "ERROR: Model data is None", model_type)
        
        logger.info(f"Processing {model_type} model: {model_name}")
        
        # Generate cache key for this model data
        cache_key = self.get_cache_key(model_name, model)
        
        # Check if model is already cached
        if not force_reload and cache_key in cache._cache:
            logger.info(f"{model_type} model already cached in VRAM: {model_name}")
            cached_model = cache._cache[cache_key]
            return (cached_model, "LOADED_FROM_CACHE", model_type)
        
        # Cache the model data directly
        try:
            logger.info(f"Caching {model_type} model in VRAM: {model_name}")
            
            # Store the model data directly in cache
            cache._cache[cache_key] = model
            
            # Store cache info
            cache._cache_info[cache_key] = {
                "name": model_name,
                "type": model_type,
                "cached_at": str(torch.cuda.memory_allocated() if torch.cuda.is_available() else 0)
            }
            
            logger.info(f"Successfully cached {model_type} model in VRAM: {model_name} (key: {cache_key})")
            return (model, "LOADED_AND_CACHED", model_type)
            
        except Exception as e:
            logger.error(f"Error caching {model_type} model {model_name}: {str(e)}")
            return (None, f"ERROR: {str(e)}", model_type) 