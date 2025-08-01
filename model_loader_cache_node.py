import torch
import os
import logging
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
                "model_type": (["auto", "checkpoint", "lora", "vae", "controlnet", "clip", "diffusion"], {"default": "auto"}),
                "force_reload": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("model", "cache_status", "model_type")
    FUNCTION = "load_model"
    CATEGORY = "VRAM Cache"
    
    def move_model_to_vram(self, model_data: Any) -> Any:
        """Move model data to GPU VRAM"""
        if not torch.cuda.is_available():
            logger.warning("CUDA not available, model will stay in CPU memory")
            return model_data
        
        try:
            if isinstance(model_data, dict):
                # For state_dict style models
                vram_model = {}
                for key, value in model_data.items():
                    if isinstance(value, torch.Tensor):
                        vram_model[key] = value.cuda()
                    else:
                        vram_model[key] = value
                logger.info("Moved model state_dict to GPU VRAM")
                return vram_model
            elif isinstance(model_data, torch.Tensor):
                # For single tensor models
                vram_model = model_data.cuda()
                logger.info("Moved model tensor to GPU VRAM")
                return vram_model
            else:
                # For other model types, try to move to GPU if possible
                logger.info("Model data type not directly movable to GPU, keeping as-is")
                return model_data
        except Exception as e:
            logger.warning(f"Could not move model to GPU VRAM: {str(e)}")
            return model_data
    
    def load_model(self, model, model_name: str = "model", model_type: str = "auto", force_reload: bool = False):
        """Load model data and cache it in VRAM by name"""
        cache = VRAMCache()
        
        if model is None:
            logger.error(f"Model data is None for model: {model_name}")
            return (None, "ERROR: Model data is None", model_type)
        
        logger.info(f"Processing {model_type} model: {model_name}")
        
        # Check if model is already cached by name
        if not force_reload and model_name in cache._cache:
            logger.info(f"{model_type} model already cached in VRAM: {model_name}")
            cached_model = cache._cache[model_name]
            return (cached_model, "LOADED_FROM_CACHE", model_type)
        
        # Cache the model data directly in VRAM by name
        try:
            logger.info(f"Caching {model_type} model in VRAM: {model_name}")
            
            # Move model to GPU VRAM
            vram_model = self.move_model_to_vram(model)
            
            # Store the model data directly in cache by name
            cache._cache[model_name] = vram_model
            
            # Store cache info by name
            cache._cache_info[model_name] = {
                "name": model_name,
                "type": model_type,
                "cached_at": str(torch.cuda.memory_allocated() if torch.cuda.is_available() else 0)
            }
            
            logger.info(f"Successfully cached {model_type} model in VRAM: {model_name}")
            return (vram_model, "LOADED_AND_CACHED", model_type)
            
        except Exception as e:
            logger.error(f"Error caching {model_type} model {model_name}: {str(e)}")
            return (None, f"ERROR: {str(e)}", model_type) 