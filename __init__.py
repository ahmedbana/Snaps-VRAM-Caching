from .vram_cache_node import VRAMCacheNode
from .model_loader_cache_node import ModelLoaderCacheNode, VRAMCacheControlNode

NODE_CLASS_MAPPINGS = {
    "VRAMCacheNode": VRAMCacheNode,
    "ModelLoaderCacheNode": ModelLoaderCacheNode,
    "VRAMCacheControlNode": VRAMCacheControlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VRAMCacheNode": "🤖 SNAPS VRAM Cache",
    "ModelLoaderCacheNode": "🤖 SNAPS Model Loader Cache",
    "VRAMCacheControlNode": "🤖 SNAPS VRAM Cache Control"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 