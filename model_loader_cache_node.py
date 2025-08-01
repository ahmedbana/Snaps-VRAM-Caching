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
                "model_name": ("STRING", {"default": "model", "multiline": False}),
                "model_type": (["auto", "checkpoint", "lora", "vae", "controlnet", "clip", "diffusion"], {"default": "auto"}),
                "force_reload": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "checkpoint": ("CHECKPOINT",),
                "lora": ("LORA",),
                "controlnet": ("CONTROL_NET",),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "CHECKPOINT", "LORA", "CONTROL_NET", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "checkpoint", "lora", "controlnet", "cache_status", "model_type")
    FUNCTION = "load_model"
    CATEGORY = "VRAM Cache"
    
    def move_model_to_vram(self, model_data: Any) -> Any:
        """Move model data to GPU VRAM"""
        if not torch.cuda.is_available():
            logger.warning("CUDA not available, model will stay in CPU memory")
            return model_data
        
        try:
            # Handle different model data types
            if isinstance(model_data, dict):
                # For state_dict style models
                vram_model = {}
                for key, value in model_data.items():
                    if isinstance(value, torch.Tensor):
                        # Check if tensor is already on GPU
                        if value.device.type != 'cuda':
                            vram_model[key] = value.cuda()
                            logger.info(f"Moved tensor {key} to GPU VRAM")
                        else:
                            vram_model[key] = value
                            logger.info(f"Tensor {key} already on GPU")
                    else:
                        vram_model[key] = value
                logger.info("Moved model state_dict to GPU VRAM")
                return vram_model
            elif isinstance(model_data, torch.Tensor):
                # For single tensor models
                if model_data.device.type != 'cuda':
                    vram_model = model_data.cuda()
                    logger.info("Moved model tensor to GPU VRAM")
                else:
                    vram_model = model_data
                    logger.info("Model tensor already on GPU")
                return vram_model
            elif hasattr(model_data, 'state_dict'):
                # For model objects with state_dict method (like FLUX models)
                logger.info("Detected model object with state_dict, moving to GPU")
                model_data = model_data.cuda()
                logger.info("Moved model object to GPU VRAM")
                return model_data
            elif hasattr(model_data, 'to'):
                # For model objects with .to() method
                logger.info("Detected model object with .to() method, moving to GPU")
                model_data = model_data.cuda()
                logger.info("Moved model object to GPU VRAM")
                return model_data
            elif hasattr(model_data, 'parameters'):
                # For model objects with parameters
                logger.info("Detected model object with parameters, moving to GPU")
                model_data = model_data.cuda()
                logger.info("Moved model object to GPU VRAM")
                return model_data
            elif hasattr(model_data, 'model') and hasattr(model_data.model, 'cuda'):
                # For ComfyUI ModelPatcher objects
                logger.info("Detected ComfyUI ModelPatcher, moving underlying model to GPU")
                model_data.model = model_data.model.cuda()
                logger.info("Moved ModelPatcher underlying model to GPU VRAM")
                return model_data
            elif hasattr(model_data, 'model'):
                # For objects with model attribute
                logger.info("Detected object with model attribute, attempting to move model to GPU")
                if hasattr(model_data.model, 'cuda'):
                    model_data.model = model_data.model.cuda()
                    logger.info("Moved model attribute to GPU VRAM")
                return model_data
            else:
                # Try to inspect the object and move any tensors found
                logger.info("Attempting to move unknown model type to GPU")
                try:
                    # Try to move the entire object to GPU
                    if hasattr(model_data, 'cuda'):
                        vram_model = model_data.cuda()
                        logger.info("Successfully moved model object to GPU VRAM")
                        return vram_model
                    else:
                        logger.warning(f"Model object type {type(model_data)} has no cuda method")
                        # For ComfyUI objects, try to move to GPU using their internal methods
                        if hasattr(model_data, 'to'):
                            vram_model = model_data.to('cuda')
                            logger.info("Moved model object to GPU using .to() method")
                            return vram_model
                        return model_data
                except Exception as e:
                    logger.warning(f"Could not move model object to GPU: {str(e)}")
                    return model_data
        except Exception as e:
            logger.warning(f"Could not move model to GPU VRAM: {str(e)}")
            return model_data
    
    def load_model(self, model=None, clip=None, vae=None, checkpoint=None, lora=None, controlnet=None, model_name: str = "model", model_type: str = "auto", force_reload: bool = False):
        """Load model data and cache it in VRAM by name"""
        cache = VRAMCache()
        
        # Determine which model input is provided
        model_data = None
        actual_model_type = model_type
        
        if model is not None:
            model_data = model
            actual_model_type = "model"
        elif clip is not None:
            model_data = clip
            actual_model_type = "clip"
        elif vae is not None:
            model_data = vae
            actual_model_type = "vae"
        elif checkpoint is not None:
            model_data = checkpoint
            actual_model_type = "checkpoint"
        elif lora is not None:
            model_data = lora
            actual_model_type = "lora"
        elif controlnet is not None:
            model_data = controlnet
            actual_model_type = "controlnet"
        else:
            logger.error("No model input provided")
            return (None, None, None, None, None, None, "ERROR: No model input provided", model_type)
        
        if model_data is None:
            logger.error(f"Model data is None for model: {model_name}")
            return (None, None, None, None, None, None, "ERROR: Model data is None", model_type)
        
        # Debug logging to identify model type
        logger.info(f"Processing {actual_model_type} model: {model_name}")
        logger.info(f"Model type: {type(model_data)}")
        logger.info(f"Model attributes: {[attr for attr in dir(model_data) if not attr.startswith('_')]}")
        
        # Check if model is already cached by name
        if not force_reload and model_name in cache._cache:
            logger.info(f"{actual_model_type} model already cached in VRAM: {model_name}")
            cached_model = cache._cache[model_name]
            
            # Return the cached model in the appropriate output
            if actual_model_type == "model":
                return (cached_model, None, None, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "clip":
                return (None, cached_model, None, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "vae":
                return (None, None, cached_model, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "checkpoint":
                return (None, None, None, cached_model, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "lora":
                return (None, None, None, None, cached_model, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "controlnet":
                return (None, None, None, None, None, cached_model, "LOADED_FROM_CACHE", actual_model_type)
        
        # Cache the model data directly in VRAM by name
        try:
            logger.info(f"Caching {actual_model_type} model in VRAM: {model_name}")
            
            # Move model to GPU VRAM
            vram_model = self.move_model_to_vram(model_data)
            
            # Store the model data directly in cache by name
            cache._cache[model_name] = vram_model
            
            # Store cache info by name
            cache._cache_info[model_name] = {
                "name": model_name,
                "type": actual_model_type,
                "cached_at": str(torch.cuda.memory_allocated() if torch.cuda.is_available() else 0)
            }
            
            logger.info(f"Successfully cached {actual_model_type} model in VRAM: {model_name}")
            
            # Return the cached model in the appropriate output
            if actual_model_type == "model":
                return (vram_model, None, None, None, None, None, "LOADED_AND_CACHED", actual_model_type)
            elif actual_model_type == "clip":
                return (None, vram_model, None, None, None, None, "LOADED_AND_CACHED", actual_model_type)
            elif actual_model_type == "vae":
                return (None, None, vram_model, None, None, None, "LOADED_AND_CACHED", actual_model_type)
            elif actual_model_type == "checkpoint":
                return (None, None, None, vram_model, None, None, "LOADED_AND_CACHED", actual_model_type)
            elif actual_model_type == "lora":
                return (None, None, None, None, vram_model, None, "LOADED_AND_CACHED", actual_model_type)
            elif actual_model_type == "controlnet":
                return (None, None, None, None, None, vram_model, "LOADED_AND_CACHED", actual_model_type)
            
        except Exception as e:
            logger.error(f"Error caching {actual_model_type} model {model_name}: {str(e)}")
            return (None, None, None, None, None, None, f"ERROR: {str(e)}", model_type)

class CachedModelLoaderNode:
    """ComfyUI node for loading cached models by name without original model file"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "model_type": (["auto", "checkpoint", "lora", "vae", "controlnet", "clip", "diffusion"], {"default": "auto"}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "CHECKPOINT", "LORA", "CONTROL_NET", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "checkpoint", "lora", "controlnet", "cache_status", "model_type")
    FUNCTION = "load_cached_model"
    CATEGORY = "VRAM Cache"
    
    def load_cached_model(self, model_name: str, model_type: str = "auto"):
        """Load cached model by name without original file"""
        cache = VRAMCache()
        
        if not model_name or not model_name.strip():
            logger.error("Model name is required")
            return (None, None, None, None, None, None, "ERROR: Model name is required", model_type)
        
        logger.info(f"Attempting to load cached model by name: {model_name}")
        
        # Check if model is cached by name
        if model_name in cache._cache:
            logger.info(f"Found cached model in VRAM: {model_name}")
            cached_model = cache._cache[model_name]
            
            # Get cache info
            cache_info = cache._cache_info.get(model_name, {})
            actual_model_type = cache_info.get("type", model_type)
            
            logger.info(f"Successfully loaded cached {actual_model_type} model: {model_name}")
            
            # Return the cached model in the appropriate output
            if actual_model_type == "model":
                return (cached_model, None, None, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "clip":
                return (None, cached_model, None, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "vae":
                return (None, None, cached_model, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "checkpoint":
                return (None, None, None, cached_model, None, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "lora":
                return (None, None, None, None, cached_model, None, "LOADED_FROM_CACHE", actual_model_type)
            elif actual_model_type == "controlnet":
                return (None, None, None, None, None, cached_model, "LOADED_FROM_CACHE", actual_model_type)
            else:
                # Default to model output for unknown types
                return (cached_model, None, None, None, None, None, "LOADED_FROM_CACHE", actual_model_type)
        else:
            logger.error(f"Model '{model_name}' not found in VRAM cache")
            return (None, None, None, None, None, None, f"ERROR: Model '{model_name}' not found in cache", model_type) 

class ModelCacheCheckerNode:
    """ComfyUI node for checking if a model is cached in VRAM"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_name": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("success_output", "not_found_output")
    FUNCTION = "check_model_cache"
    CATEGORY = "VRAM Cache"
    
    def check_model_cache(self, model_name: str):
        """Check if model is cached in VRAM"""
        cache = VRAMCache()
        
        if not model_name or not model_name.strip():
            logger.error("Model name is required")
            return ("", "")
        
        logger.info(f"Checking if model is cached in VRAM: {model_name}")
        
        # Check if model is cached by name
        if model_name in cache._cache:
            logger.info(f"Model '{model_name}' found in VRAM cache")
            cache_info = cache._cache_info.get(model_name, {})
            model_type = cache_info.get("type", "unknown")
            success_message = f"Model '{model_name}' ({model_type}) is available in VRAM cache"
            return (success_message, "false")
        else:
            logger.info(f"Model '{model_name}' not found in VRAM cache")
            return ("", model_name) 