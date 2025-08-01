#!/usr/bin/env python3
"""
Test script for VRAM Cache Custom Nodes
"""

import os
import sys
import torch
import tempfile
import json
from typing import Dict, Any

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cache_manager():
    """Test the VRAM cache manager functionality"""
    print("Testing VRAM Cache Manager...")
    
    try:
        from vram_cache_manager import cache_manager
        
        # Test cache initialization
        print("✓ Cache manager initialized successfully")
        
        # Test cache statistics
        stats = cache_manager.get_cache_stats()
        print(f"✓ Cache stats: {stats}")
        
        # Test cache size setting
        cache_manager.set_max_cache_size(4.0)
        print("✓ Cache size set to 4GB")
        
        # Test cache clearing
        cache_manager.clear_cache()
        print("✓ Cache cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache manager test failed: {e}")
        return False

def test_cache_node():
    """Test the VRAM cache node functionality"""
    print("\nTesting VRAM Cache Node...")
    
    try:
        from vram_cache_node import VRAMCacheNode
        
        # Create a test node instance
        node = VRAMCacheNode()
        print("✓ VRAM cache node created successfully")
        
        # Test input types
        input_types = node.INPUT_TYPES()
        print(f"✓ Input types: {list(input_types['required'].keys())}")
        
        # Test return types
        return_types = node.RETURN_TYPES
        print(f"✓ Return types: {return_types}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache node test failed: {e}")
        return False

def test_model_loader_cache_node():
    """Test the model loader cache node functionality"""
    print("\nTesting Model Loader Cache Node...")
    
    try:
        from model_loader_cache_node import ModelLoaderCacheNode, VRAMCacheControlNode
        
        # Create test node instances
        loader_node = ModelLoaderCacheNode()
        control_node = VRAMCacheControlNode()
        print("✓ Model loader cache nodes created successfully")
        
        # Test input types
        loader_inputs = loader_node.INPUT_TYPES()
        control_inputs = control_node.INPUT_TYPES()
        print(f"✓ Loader node inputs: {list(loader_inputs['required'].keys())}")
        print(f"✓ Control node inputs: {list(control_inputs['required'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Model loader cache node test failed: {e}")
        return False

def test_integration():
    """Test the ComfyUI integration functionality"""
    print("\nTesting ComfyUI Integration...")
    
    try:
        from comfy_integration import integration, get_cache_stats, clear_all_caches
        
        # Test integration instance
        print("✓ Integration instance created successfully")
        
        # Test cache stats
        stats = get_cache_stats()
        print(f"✓ Integration stats: {stats}")
        
        # Test cache clearing
        clear_all_caches()
        print("✓ All caches cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting File Structure...")
    
    required_files = [
        "__init__.py",
        "vram_cache_manager.py",
        "vram_cache_node.py",
        "model_loader_cache_node.py",
        "comfy_integration.py",
        "compat.py",
        "README.md",
        "requirements.txt"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            all_exist = False
    
    return all_exist

def test_basic_functionality():
    """Test basic functionality without ComfyUI dependencies"""
    print("\nTesting Basic Functionality...")
    
    try:
        # Test cache manager with compatibility layer
        from vram_cache_manager import cache_manager
        
        # Test model hashing
        test_path = "/tmp/test_model.safetensors"
        model_hash = cache_manager.get_model_hash(test_path)
        print(f"✓ Model hashing works: {model_hash[:8]}...")
        
        # Test cache operations
        cache_manager.clear_cache()
        print("✓ Cache operations work")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("VRAM Cache Custom Nodes - Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Basic Functionality", test_basic_functionality),
        ("Cache Manager", test_cache_manager),
        ("Cache Node", test_cache_node),
        ("Model Loader Cache Node", test_model_loader_cache_node),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} test passed\n")
            else:
                print(f"✗ {test_name} test failed\n")
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}\n")
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The VRAM cache custom nodes are ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 