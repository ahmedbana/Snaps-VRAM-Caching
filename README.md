# SNAPS VRAM Cache for ComfyUI

A simple VRAM cache system for ComfyUI that allows you to cache models and files directly in GPU VRAM for faster loading and reuse.

## Features

- **No size limits**: Cache models of any size in VRAM
- **Multiple model types**: Supports checkpoints, LoRAs, VAEs, ControlNets, and CLIP models
- **Automatic detection**: Automatically detects model types based on file paths
- **Debug logging**: Comprehensive logging for debugging and monitoring
- **Cache management**: List and clear cached models

## Nodes

### 1. 🤖 SNAPS VRAM Cache (VRAMCacheNode)

**Main node for loading and caching models in VRAM**

**Inputs:**
- `model_path` (STRING): Path to the model file
- `force_reload` (BOOLEAN): Force reload even if already cached (default: False)

**Outputs:**
- `model`: The loaded model data
- `cache_status`: Status message ("LOADED_FROM_CACHE", "LOADED_AND_CACHED", or error)
- `cache_key`: Unique cache key for the model

**Usage:**
- Connect a model path to load and cache the model
- The node will check if the model is already cached in VRAM
- If cached, it returns the cached model instantly
- If not cached, it loads the model and stores it in VRAM for future use

### 2. 🤖 SNAPS Model Loader (ModelLoaderCacheNode)

**Specialized node for caching model data directly in VRAM**

**Inputs:**
- `model` (MODEL): The model data to cache
- `model_name` (STRING): Name/identifier for the model (default: "model")
- `model_type` (SELECT): Type of model ("auto", "checkpoint", "lora", "vae", "controlnet", "clip")
- `force_reload` (BOOLEAN): Force reload even if already cached (default: False)

**Outputs:**
- `model`: The model data (same as input)
- `cache_status`: Status message
- `model_type`: The detected/selected model type

**Usage:**
- Takes model data as input (not file path)
- Caches the model data directly in VRAM
- If the same model data is already cached, returns it instantly
- Useful for caching models that are already loaded in your workflow

### 3. 📋 SNAPS Cache Control (VRAMCacheControlNode)

**Node for managing the VRAM cache**

**Inputs:**
- `action` (SELECT): Action to perform ("list_cache", "clear_cache")

**Outputs:**
- `cache_info` (STRING): Information about cached models or status message

**Usage:**
- **list_cache**: Lists all models currently cached in VRAM with their file sizes
- **clear_cache**: Clears all cached models from VRAM

## How It Works

1. **Cache Key Generation**: Each model gets a unique cache key based on file path, modification time, and file size
2. **VRAM Storage**: Models are stored directly in GPU VRAM using PyTorch tensors
3. **Singleton Pattern**: Uses a singleton cache manager to ensure consistent state across nodes
4. **Automatic Detection**: Supports both `.safetensors` and regular PyTorch model files
5. **Comprehensive Logging**: All operations are logged for debugging

## Logging

The nodes provide detailed logging for debugging:
- Model loading operations
- Cache hits and misses
- Error messages
- Cache management operations

Logs will appear in your ComfyUI console output.

## Installation

1. Place this folder in your ComfyUI `custom_nodes` directory
2. Restart ComfyUI
3. The nodes will appear in the "VRAM Cache" category

## Example Workflow

1. Use **SNAPS VRAM Cache** to load your first model - it will be cached in VRAM
2. Use the same node again with the same model path - it will load instantly from cache
3. Use **SNAPS Cache Control** with "list_cache" to see all cached models
4. Use **SNAPS Cache Control** with "clear_cache" to free VRAM when done

## Notes

- Models are cached in GPU VRAM, so they consume GPU memory
- The cache persists until manually cleared or ComfyUI is restarted
- No size limits are enforced - cache as many models as your VRAM allows
- All model types are supported (checkpoints, LoRAs, VAEs, etc.) 