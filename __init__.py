from .vram_cache_node import VRAMCacheNode, VRAMCacheControlNode, VRAMStatusNode
from .model_loader_cache_node import ModelLoaderCacheNode, CachedModelLoaderNode

NODE_CLASS_MAPPINGS = {
    "VRAMCacheNode": VRAMCacheNode,
    "VRAMCacheControlNode": VRAMCacheControlNode,
    "VRAMStatusNode": VRAMStatusNode,
    "ModelLoaderCacheNode": ModelLoaderCacheNode,
    "CachedModelLoaderNode": CachedModelLoaderNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VRAMCacheNode": "🤖 SNAPS VRAM Cache",
    "VRAMCacheControlNode": "🤖 SNAPS Cache Control",
    "VRAMStatusNode": "📊 SNAPS VRAM Status",
    "ModelLoaderCacheNode": "🤖 SNAPS Model Loader",
    "CachedModelLoaderNode": "📥 SNAPS Cached Model Loader",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 