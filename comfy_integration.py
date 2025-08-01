import torch
import os
import json
import time
from typing import Dict, Any, Optional, Union, Tuple

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

# Global cache for model states
_model_cache = {}

def hook_model_loading():
    """Hook into ComfyUI's model loading system"""
    try:
        # This would need to be implemented based on ComfyUI's internal model loading
        # For now, we'll provide a framework for integration
        pass
    except Exception as e:
        print(f"Failed to hook into model loading: {e}")

def get_cached_model(model_path: str) -> Optional[Tuple[Any, Any, Any]]:
    """Get a cached model from VRAM"""
    if not os.path.exists(model_path):
        return None
    
    cached_model = cache_manager.access_model(model_path)
    if cached_model is not None:
        return (
            cached_model.get('model'),
            cached_model.get('clip'),
            cached_model.get('vae')
        )
    return None

def cache_model_state(model_path: str, model: Any, clip: Any, vae: Any):
    """Cache a complete model state in VRAM"""
    if not os.path.exists(model_path):
        return
    
    model_state = {
        'model': model,
        'clip': clip,
        'vae': vae,
        'path': model_path,
        'cached_at': time.time()
    }
    
    cache_manager.cache_model(model_path, model_state)
    print(f"Cached complete model state: {os.path.basename(model_path)}")

def load_model_with_cache(model_path: str, force_reload: bool = False) -> Tuple[Optional[Any], Optional[Any], Optional[Any], bool]:
    """Load a model with VRAM caching support"""
    
    if not os.path.exists(model_path):
        return None, None, None, False
    
    was_cached = False
    
    if not force_reload:
        # Try to load from cache first
        cached_result = get_cached_model(model_path)
        if cached_result is not None:
            model, clip, vae = cached_result
            was_cached = True
            print(f"Loaded model from VRAM cache: {os.path.basename(model_path)}")
            return model, clip, vae, was_cached
    
    # Load model normally (this would integrate with ComfyUI's actual loading)
    # For now, we'll return None to indicate normal loading should proceed
    print(f"Loading model from disk: {os.path.basename(model_path)}")
    return None, None, None, was_cached

def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    stats = cache_manager.get_cache_stats()
    
    # Add additional statistics
    stats.update({
        'cached_models': list(cache_manager.cached_models.keys()),
        'cache_hit_rate': _calculate_hit_rate(),
        'total_models_accessed': len(_model_cache),
        'session_start_time': time.time()
    })
    
    return stats

def _calculate_hit_rate() -> float:
    """Calculate cache hit rate"""
    if not hasattr(cache_manager, '_access_count'):
        return 0.0
    
    total_accesses = getattr(cache_manager, '_total_accesses', 0)
    cache_hits = getattr(cache_manager, '_cache_hits', 0)
    
    if total_accesses == 0:
        return 0.0
    
    return (cache_hits / total_accesses) * 100

def clear_all_caches():
    """Clear all caches (VRAM and metadata)"""
    cache_manager.clear_cache()
    _model_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("All caches cleared")

def optimize_cache_for_workflow(workflow_models: list):
    """Optimize cache for a specific workflow"""
    # This would analyze the workflow and pre-cache frequently used models
    for model_path in workflow_models:
        if os.path.exists(model_path) and not cache_manager.is_model_cached(model_path):
            print(f"Pre-caching model for workflow: {os.path.basename(model_path)}")
            # In a real implementation, you would load and cache the model here

class ComfyUIIntegration:
    """Integration class for ComfyUI model loading system"""
    
    def __init__(self):
        self.cache_manager = cache_manager
        self._setup_hooks()
    
    def _setup_hooks(self):
        """Setup hooks into ComfyUI's model loading system"""
        try:
            # This would hook into ComfyUI's model loading functions
            # For now, we'll provide the framework
            pass
        except Exception as e:
            print(f"Failed to setup ComfyUI hooks: {e}")
    
    def intercept_model_load(self, model_path: str, **kwargs):
        """Intercept model loading to add caching"""
        # Check if model is cached
        cached_model = self.cache_manager.access_model(model_path)
        if cached_model is not None:
            return cached_model.get('model'), cached_model.get('clip'), cached_model.get('vae')
        
        # Let normal loading proceed
        return None
    
    def intercept_model_save(self, model_path: str, model: Any, clip: Any, vae: Any):
        """Intercept model saving to add caching"""
        # Cache the model after it's loaded
        model_state = {
            'model': model,
            'clip': clip,
            'vae': vae,
            'path': model_path
        }
        self.cache_manager.cache_model(model_path, model_state)

# Global integration instance
integration = ComfyUIIntegration() 