#!/usr/bin/env python3
"""
Simple deployment verification script for Render
"""
import sys
import importlib.util

def check_main_module():
    """Check if main.py can be imported successfully"""
    try:
        spec = importlib.util.spec_from_file_location("main", "main.py")
        if spec is None:
            print("❌ Could not load main.py")
            return False
        
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        # Check if app is available
        if hasattr(main_module, 'app'):
            print("✅ main.py loaded successfully")
            print(f"✅ FastAPI app found: {main_module.app}")
            return True
        else:
            print("❌ FastAPI app not found in main.py")
            return False
            
    except Exception as e:
        print(f"❌ Error loading main.py: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking deployment readiness...")
    
    if check_main_module():
        print("🎉 Deployment verification passed!")
        sys.exit(0)
    else:
        print("💥 Deployment verification failed!")
        sys.exit(1)