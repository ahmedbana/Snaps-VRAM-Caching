import torch
import hashlib
import os
import logging
from typing import Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VRAMCache:
    """Singleton class to manage VRAM cache for models"""
    _instance = None
    _cache: Dict[str, Any] = {}
    _cache_info: Dict[str, Dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VRAMCache, cls).__new__(cls)
        return cls._instance
    
    def get_cache_key(self, model_path: str) -> str:
        """Generate a unique cache key for the model file"""
        # Use file path and modification time for cache key
        if os.path.exists(model_path):
            stat = os.stat(model_path)
            key_data = f"{model_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(key_data.encode()).hexdigest()
        return hashlib.md5(model_path.encode()).hexdigest()
    
    def is_cached(self, model_path: str) -> bool:
        """Check if model is already cached in VRAM"""
        cache_key = self.get_cache_key(model_path)
        return cache_key in self._cache
    
    def get_cached_model(self, model_path: str) -> Optional[Any]:
        """Get cached model from VRAM"""
        cache_key = self.get_cache_key(model_path)
        if cache_key in self._cache:
            logger.info(f"Retrieved model from VRAM cache: {model_path}")
            return self._cache[cache_key]
        return None
    
    def cache_model(self, model_path: str, model_data: Any) -> str:
        """Cache model in VRAM"""
        cache_key = self.get_cache_key(model_path)
        
        # Move model to GPU VRAM if CUDA is available
        if torch.cuda.is_available():
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
                    model_data = vram_model
                elif isinstance(model_data, torch.Tensor):
                    # For single tensor models
                    model_data = model_data.cuda()
                    logger.info("Moved model tensor to GPU VRAM")
            except Exception as e:
                logger.warning(f"Could not move model to GPU VRAM: {str(e)}")
        
        self._cache[cache_key] = model_data
        
        # Store cache info
        self._cache_info[cache_key] = {
            "path": model_path,
            "size": os.path.getsize(model_path) if os.path.exists(model_path) else 0,
            "cached_at": str(torch.cuda.memory_allocated() if torch.cuda.is_available() else 0)
        }
        
        logger.info(f"Cached model in VRAM: {model_path} (key: {cache_key})")
        return cache_key
    
    def get_cache_info(self) -> Dict[str, Dict]:
        """Get information about all cached models"""
        return self._cache_info
    
    def clear_cache(self):
        """Clear all cached models from VRAM"""
        self._cache.clear()
        self._cache_info.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Cleared all models from VRAM cache")

class VRAMCacheNode:
    """ComfyUI node for loading and caching models in VRAM"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("STRING", {"default": "", "multiline": False}),
                "model_name": ("STRING", {"default": "", "multiline": False}),
                "force_reload": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("model", "cache_status", "cache_key")
    FUNCTION = "load_model"
    CATEGORY = "VRAM Cache"
    
    def load_model(self, model_path: str, model_name: str = "", force_reload: bool = False):
        """Load model and cache it in VRAM"""
        cache = VRAMCache()
        
        # If model_name is provided, use name-based caching
        if model_name and model_name.strip():
            logger.info(f"Using name-based caching for: {model_name}")
            
            if not model_path or not os.path.exists(model_path):
                logger.error(f"Model path does not exist: {model_path}")
                return (None, "ERROR: Model path does not exist", "")
            
            # Check if model is already cached by name
            if not force_reload and model_name in cache._cache:
                logger.info(f"Model already cached in VRAM by name: {model_name}")
                cached_model = cache._cache[model_name]
                return (cached_model, "LOADED_FROM_CACHE", model_name)
            
            # Load model into VRAM
            try:
                logger.info(f"Loading model into VRAM by name: {model_name}")
                
                # Try to load the model using torch
                if model_path.endswith('.safetensors'):
                    from safetensors.torch import load_file
                    model_data = load_file(model_path)
                    logger.info(f"Loaded safetensors model: {model_path}")
                else:
                    model_data = torch.load(model_path, map_location='cpu')
                    logger.info(f"Loaded torch model: {model_path}")
                
                # Move to GPU VRAM
                if torch.cuda.is_available():
                    try:
                        if isinstance(model_data, dict):
                            vram_model = {}
                            for key, value in model_data.items():
                                if isinstance(value, torch.Tensor):
                                    vram_model[key] = value.cuda()
                                else:
                                    vram_model[key] = value
                            logger.info("Moved model state_dict to GPU VRAM")
                            model_data = vram_model
                        elif isinstance(model_data, torch.Tensor):
                            model_data = model_data.cuda()
                            logger.info("Moved model tensor to GPU VRAM")
                    except Exception as e:
                        logger.warning(f"Could not move model to GPU VRAM: {str(e)}")
                
                # Cache the model by name
                cache._cache[model_name] = model_data
                cache._cache_info[model_name] = {
                    "name": model_name,
                    "path": model_path,
                    "size": os.path.getsize(model_path) if os.path.exists(model_path) else 0,
                    "cached_at": str(torch.cuda.memory_allocated() if torch.cuda.is_available() else 0)
                }
                
                logger.info(f"Successfully cached model in VRAM by name: {model_name}")
                return (model_data, "LOADED_AND_CACHED", model_name)
                
            except Exception as e:
                logger.error(f"Error loading model {model_path}: {str(e)}")
                return (None, f"ERROR: {str(e)}", "")
        
        # Fallback to path-based caching
        if not model_path or not os.path.exists(model_path):
            logger.error(f"Model path does not exist: {model_path}")
            return (None, "ERROR: Model path does not exist", "")
        
        logger.info(f"Processing model: {model_path}")
        
        # Check if model is already cached
        if not force_reload and cache.is_cached(model_path):
            logger.info(f"Model already cached in VRAM: {model_path}")
            cached_model = cache.get_cached_model(model_path)
            cache_key = cache.get_cache_key(model_path)
            return (cached_model, "LOADED_FROM_CACHE", cache_key)
        
        # Load model into VRAM
        try:
            logger.info(f"Loading model into VRAM: {model_path}")
            
            # Try to load the model using torch
            if model_path.endswith('.safetensors'):
                from safetensors.torch import load_file
                model_data = load_file(model_path)
                logger.info(f"Loaded safetensors model: {model_path}")
            else:
                model_data = torch.load(model_path, map_location='cpu')
                logger.info(f"Loaded torch model: {model_path}")
            
            # Cache the model
            cache_key = cache.cache_model(model_path, model_data)
            
            logger.info(f"Successfully cached model in VRAM: {model_path}")
            return (model_data, "LOADED_AND_CACHED", cache_key)
            
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {str(e)}")
            return (None, f"ERROR: {str(e)}", "")

class VRAMCacheControlNode:
    """ComfyUI node for controlling VRAM cache"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["list_cache", "clear_cache"], {"default": "list_cache"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("cache_info",)
    FUNCTION = "control_cache"
    CATEGORY = "VRAM Cache"
    
    def control_cache(self, action: str):
        """Control VRAM cache operations"""
        cache = VRAMCache()
        
        if action == "list_cache":
            cache_info = cache.get_cache_info()
            if not cache_info:
                return ("No models cached in VRAM",)
            
            info_lines = ["Cached Models in VRAM:"]
            for key, info in cache_info.items():
                if "path" in info:
                    # File-based cache (from VRAMCacheNode path-based caching)
                    size_mb = info.get("size", 0) / (1024 * 1024)
                    info_lines.append(f"- {info.get('path', 'Unknown')} ({size_mb:.2f} MB)")
                elif "name" in info:
                    # Name-based cache (from ModelLoaderCacheNode or VRAMCacheNode name-based caching)
                    model_type = info.get("type", "unknown")
                    if "path" in info:
                        size_mb = info.get("size", 0) / (1024 * 1024)
                        info_lines.append(f"- {info.get('name', 'Unknown')} ({model_type}) - {info.get('path', 'Unknown')} ({size_mb:.2f} MB)")
                    else:
                        info_lines.append(f"- {info.get('name', 'Unknown')} ({model_type})")
            
            logger.info("Listed cached models")
            return ("\n".join(info_lines),)
        
        elif action == "clear_cache":
            cache.clear_cache()
            return ("Cache cleared successfully",)
        
        return ("Unknown action",) 