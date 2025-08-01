# ComfyUI VRAM Cache Custom Nodes

This custom node package provides VRAM caching functionality for ComfyUI, allowing models to be cached in GPU memory for faster subsequent loads.

## Features

- **VRAM Caching**: Cache models in GPU memory to avoid repeated disk loading
- **LRU Eviction**: Automatically evict least recently used models when cache is full
- **Cache Statistics**: Monitor cache usage and performance
- **Configurable Cache Size**: Set maximum cache size in GB
- **Cache Control**: Clear cache and manage settings through UI nodes

## Installation

1. Clone or download this repository to your ComfyUI `custom_nodes` directory:
   ```
   cd ComfyUI/custom_nodes
   git clone https://github.com/your-username/Snaps-VRAM-Cache.git
   ```

2. Restart ComfyUI to load the custom nodes

## Nodes

### 1. VRAM Cache Node
A general-purpose caching node that can cache any model data.

**Inputs:**
- `model_path` (STRING): Path to the model file
- `cache_enabled` (BOOLEAN): Enable/disable caching (default: True)
- `clear_cache` (BOOLEAN): Clear all cached models (default: False)
- `max_cache_size_gb` (FLOAT): Maximum cache size in GB (default: 8.0)
- `model_data` (MODEL, optional): Model data to cache

**Outputs:**
- `model` (MODEL): The model data
- `cache_status` (STRING): Status message about caching
- `was_cached` (BOOLEAN): Whether the model was loaded from cache
- `cache_stats` (STRING): Current cache statistics

### 2. Model Loader Cache Node
A specialized node that integrates with ComfyUI's model loading system.

**Inputs:**
- `model_name` (CHECKPOINT): Model name from ComfyUI's checkpoint list
- `cache_enabled` (BOOLEAN): Enable/disable caching (default: True)
- `clear_cache` (BOOLEAN): Clear all cached models (default: False)
- `max_cache_size_gb` (FLOAT): Maximum cache size in GB (default: 8.0)
- `force_reload` (BOOLEAN): Force reload from disk (default: False)

**Outputs:**
- `model` (MODEL): The loaded model
- `clip` (CLIP): The CLIP model
- `vae` (VAE): The VAE model
- `cache_status` (STRING): Status message about caching
- `was_cached` (BOOLEAN): Whether the model was loaded from cache
- `cache_stats` (STRING): Current cache statistics

### 3. VRAM Cache Control Node
A control node for managing cache settings and operations.

**Inputs:**
- `action` (SELECT): Action to perform (get_stats, clear_cache, set_size)
- `max_cache_size_gb` (FLOAT): Maximum cache size in GB (default: 8.0)

**Outputs:**
- `action_result` (STRING): Result of the performed action
- `cache_stats` (STRING): Current cache statistics

## Usage Examples

### Basic Caching
1. Add a "VRAM Cache" node to your workflow
2. Connect your model loader to the `model_data` input
3. Set the `model_path` to the path of your model file
4. Enable caching by setting `cache_enabled` to True
5. The node will cache the model on first load and load from cache on subsequent runs

### Model Loader Integration
1. Add a "Model Loader Cache" node to your workflow
2. Select your model from the `model_name` dropdown
3. Enable caching and set your desired cache size
4. Connect the outputs to your workflow as needed

### Cache Management
1. Add a "VRAM Cache Control" node to your workflow
2. Use the `action` dropdown to:
   - `get_stats`: View current cache statistics
   - `clear_cache`: Clear all cached models
   - `set_size`: Set the maximum cache size

## Cache Behavior

- **First Load**: Model is loaded from disk and cached in VRAM
- **Subsequent Loads**: Model is loaded directly from VRAM cache
- **Cache Full**: Least recently used models are automatically evicted
- **Cache Statistics**: Monitor usage with the cache_stats output

## Configuration

The cache uses a JSON file to persist cache metadata between ComfyUI sessions. The cache index is stored in:
```
ComfyUI/temp/vram_cache/cache_index.json
```

## Performance Benefits

- **Faster Model Loading**: Cached models load instantly from VRAM
- **Reduced Disk I/O**: Avoid repeated disk reads for the same models
- **Memory Management**: Automatic eviction prevents VRAM overflow
- **Session Persistence**: Cache metadata persists between ComfyUI restarts

## Limitations

- Models must be identical (same file) to use cache
- Cache is cleared when ComfyUI is restarted
- Large models may consume significant VRAM
- Cache size should be set based on available GPU memory

## Troubleshooting

### Cache Not Working
1. Check that `cache_enabled` is set to True
2. Verify the model path is correct
3. Ensure you have sufficient VRAM available
4. Check the cache_status output for error messages

### Memory Issues
1. Reduce the `max_cache_size_gb` setting
2. Use the "VRAM Cache Control" node to clear cache
3. Restart ComfyUI to clear all cached models

### Performance Issues
1. Monitor cache statistics to ensure models are being cached
2. Check that models are being loaded from cache (was_cached = True)
3. Adjust cache size based on your GPU memory

## Technical Details

The cache system uses:
- **MD5 Hashing**: For model file identification
- **LRU Eviction**: For memory management
- **JSON Metadata**: For cache persistence
- **Torch CUDA Events**: For GPU synchronization

## License

This project is licensed under the MIT License - see the LICENSE file for details. 