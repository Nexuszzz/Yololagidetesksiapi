"""
Quick Model Download - No prompt version
=========================================
Download YOLOv8n model langsung tanpa prompt.

Usage: python quick_download.py
"""

import os
import sys
from pathlib import Path


def download_yolov8n():
    """Download YOLOv8n model using ultralytics"""
    print("="*60)
    print("📦 DOWNLOADING YOLOV8N MODEL")
    print("="*60)
    print()
    
    # Create models directory
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    print(f"✅ Models directory: {models_dir.absolute()}")
    print()
    
    model_path = models_dir / 'yolov8n.pt'
    
    # Check if already exists
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ Model already exists: {model_path}")
        print(f"   Size: {size_mb:.1f} MB")
        print()
        return True
    
    print("📥 Downloading YOLOv8n model...")
    print("   This may take a few minutes...")
    print()
    
    try:
        # Method 1: Using ultralytics YOLO
        print("   Method: Using Ultralytics YOLO library")
        from ultralytics import YOLO
        
        # Change to models directory
        original_dir = os.getcwd()
        os.chdir('models')
        
        try:
            # This will auto-download to current directory
            print("   Loading YOLO('yolov8n.pt')...")
            model = YOLO('yolov8n.pt')
            print()
            print("✅ Model downloaded successfully!")
            
        finally:
            os.chdir(original_dir)
        
        # Verify
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ Model saved: {model_path}")
            print(f"   Size: {size_mb:.1f} MB")
            print()
            return True
        else:
            print("⚠️  Model downloaded but not found in expected location")
            # Check if it's in root
            if Path('yolov8n.pt').exists():
                print("   Found in root directory, moving to models/")
                Path('yolov8n.pt').rename(model_path)
                return True
            return False
            
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check internet connection")
        print("   2. Try manual download:")
        print("      URL: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt")
        print("      Save to: models/yolov8n.pt")
        print("   3. Or use browser to download:")
        print("      - Open URL in browser")
        print("      - Save as 'yolov8n.pt' in 'models' folder")
        print()
        return False


def verify_installation():
    """Verify model and dependencies"""
    print("="*60)
    print("🔍 VERIFICATION")
    print("="*60)
    print()
    
    # Check model file
    model_path = Path('models/yolov8n.pt')
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ Model found: {model_path}")
        print(f"   Size: {size_mb:.1f} MB")
        
        # Verify it's a valid model
        if size_mb < 5:
            print("   ⚠️  Warning: File size too small, may be corrupted")
            return False
        elif size_mb > 7:
            print("   ⚠️  Warning: File size too large, may be wrong file")
            return False
        else:
            print("   ✅ Size looks correct (~6 MB)")
    else:
        print(f"❌ Model not found: {model_path}")
        return False
    
    print()
    
    # Test loading model
    try:
        print("🧪 Testing model load...")
        from ultralytics import YOLO
        model = YOLO(str(model_path))
        print("✅ Model loads successfully!")
        print(f"   Task: {model.task}")
        print(f"   Classes: {len(model.names)}")
        print()
        return True
    except Exception as e:
        print(f"❌ Model load failed: {e}")
        return False


def main():
    """Main function"""
    print()
    
    # Download model
    success = download_yolov8n()
    
    if success:
        print()
        # Verify
        if verify_installation():
            print("="*60)
            print("✅ SETUP COMPLETE!")
            print("="*60)
            print()
            print("📝 Next Steps:")
            print("   1. Run fire detection:")
            print("      python fire_detection.py")
            print()
            print("   2. Or test ESP32-CAM stream first:")
            print("      python test_esp32_stream.py")
            print()
        else:
            print("="*60)
            print("⚠️  VERIFICATION FAILED")
            print("="*60)
            print()
            print("Model downloaded but verification failed.")
            print("Try downloading again or manual download.")
    else:
        print("="*60)
        print("❌ DOWNLOAD FAILED")
        print("="*60)
        print()
        print("Please try manual download:")
        print("1. Open: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt")
        print("2. Save to: d:\\zakaiot\\models\\yolov8n.pt")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
