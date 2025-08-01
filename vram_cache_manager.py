import torch
import hashlib
import os
import json
import time
from typing import Dict, Any, Optional, Union, Tuple
from collections import OrderedDict

# Import compatibility layer
try:
    import folder_paths
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from compat import folder_paths

class VRAMCacheManager:
    """Singleton class to manage VRAM caching across the entire ComfyUI session"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VRAMCacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.cache_dir = os.path.join(folder_paths.get_temp_directory(), "vram_cache")
        self.cache_index_file = os.path.join(self.cache_dir, "cache_index.json")
        self.cached_models = OrderedDict()  # Use OrderedDict for LRU behavior
        self.max_cache_size = 8 * 1024 * 1024 * 1024  # 8GB default
        self.current_cache_size = 0
        self.load_cache_index()
        self._initialized = True
    
    def load_cache_index(self):
        """Load the cache index from disk"""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    data = json.load(f)
                    self.cached_models = OrderedDict(data.get('models', {}))
                    self.current_cache_size = data.get('current_size', 0)
            except:
                self.cached_models = OrderedDict()
                self.current_cache_size = 0
        else:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.cached_models = OrderedDict()
            self.current_cache_size = 0
    
    def save_cache_index(self):
        """Save the cache index to disk"""
        data = {
            'models': dict(self.cached_models),
            'current_size': self.current_cache_size,
            'max_size': self.max_cache_size,
            'last_updated': time.time()
        }
        with open(self.cache_index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_model_hash(self, model_path: str) -> str:
        """Generate a hash for the model file"""
        if not os.path.exists(model_path):
            return ""
        
        # Use file modification time and size for quick hash
        stat = os.stat(model_path)
        hash_input = f"{model_path}:{stat.st_mtime}:{stat.st_size}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def is_model_cached(self, model_path: str) -> bool:
        """Check if a model is cached in VRAM"""
        model_hash = self.get_model_hash(model_path)
        return model_hash in self.cached_models and self.cached_models[model_hash].get('in_vram', False)
    
    def get_model_size(self, model_data: Any) -> int:
        """Estimate the size of a model in bytes"""
        if hasattr(model_data, 'numel'):
            return model_data.numel() * model_data.element_size()
        elif isinstance(model_data, dict):
            total_size = 0
            for key, value in model_data.items():
                if hasattr(value, 'numel'):
                    total_size += value.numel() * value.element_size()
            return total_size
        return 0
    
    def cache_model(self, model_path: str, model_data: Any) -> str:
        """Cache a model in VRAM and store metadata"""
        model_hash = self.get_model_hash(model_path)
        model_size = self.get_model_size(model_data)
        
        # Check if we need to evict models to make space
        while self.current_cache_size + model_size > self.max_cache_size and self.cached_models:
            self._evict_oldest_model()
        
        # Store model in VRAM cache
        self.cached_models[model_hash] = {
            'path': model_path,
            'in_vram': True,
            'size': model_size,
            'cached_at': time.time(),
            'access_count': 0,
            'last_accessed': time.time()
        }
        
        self.current_cache_size += model_size
        self.save_cache_index()
        print(f"Cached model in VRAM: {model_path} ({model_size / (1024*1024):.2f} MB)")
        return model_hash
    
    def _evict_oldest_model(self):
        """Evict the least recently used model from cache"""
        if not self.cached_models:
            return
        
        # Remove the oldest entry (first in OrderedDict)
        oldest_hash = next(iter(self.cached_models))
        oldest_model = self.cached_models[oldest_hash]
        
        self.current_cache_size -= oldest_model['size']
        del self.cached_models[oldest_hash]
        
        print(f"Evicted model from VRAM cache: {oldest_model['path']}")
    
    def access_model(self, model_path: str) -> Optional[Any]:
        """Access a cached model and update its access statistics"""
        model_hash = self.get_model_hash(model_path)
        
        if model_hash in self.cached_models:
            # Update access statistics
            self.cached_models[model_hash]['access_count'] += 1
            self.cached_models[model_hash]['last_accessed'] = time.time()
            
            # Move to end (most recently used)
            self.cached_models.move_to_end(model_hash)
            
            print(f"Accessed cached model: {model_path}")
            return self.cached_models[model_hash].get('model_data', None)
        
        return None
    
    def clear_cache(self):
        """Clear all cached models from VRAM"""
        self.cached_models.clear()
        self.current_cache_size = 0
        self.save_cache_index()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("VRAM cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        return {
            'total_models': len(self.cached_models),
            'current_size_mb': self.current_cache_size / (1024 * 1024),
            'max_size_mb': self.max_cache_size / (1024 * 1024),
            'cache_usage_percent': (self.current_cache_size / self.max_cache_size) * 100 if self.max_cache_size > 0 else 0
        }
    
    def set_max_cache_size(self, size_gb: float):
        """Set the maximum cache size in GB"""
        self.max_cache_size = int(size_gb * 1024 * 1024 * 1024)
        self.save_cache_index()
        print(f"Max cache size set to {size_gb} GB")

# Global instance
cache_manager = VRAMCacheManager() 