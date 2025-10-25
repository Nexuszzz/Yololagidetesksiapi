"""
Get fire.pt Model for YOLOv10 Fire Detection
=============================================
Script untuk mendapatkan fire.pt model dari GitHub repo original.

Author: AI Assistant  
Date: 2025
"""

import os
import subprocess
from pathlib import Path
import shutil


def print_banner():
    """Print banner"""
    print("\n" + "="*70)
    print("🔥 FIRE.PT MODEL DOWNLOADER")
    print("="*70 + "\n")


def check_git():
    """Check if git is installed"""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        return True
    except:
        return False


def clone_repo():
    """Clone original repository"""
    repo_url = "https://github.com/Nexuszzz/Pblyoloiot"
    clone_dir = "Pblyoloiot_temp"
    
    print(f"📥 Cloning repository: {repo_url}")
    print("   This may take a minute...\n")
    
    try:
        # Remove if exists
        if os.path.exists(clone_dir):
            print(f"   Removing existing {clone_dir}/...")
            shutil.rmtree(clone_dir)
        
        # Clone repo
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, clone_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Repository cloned successfully!")
            return clone_dir
        else:
            print(f"❌ Clone failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Clone timeout (slow connection)")
        return None
    except Exception as e:
        print(f"❌ Clone error: {e}")
        return None


def copy_fire_model(clone_dir):
    """Copy fire.pt from cloned repo"""
    source = os.path.join(clone_dir, 'fire.pt')
    dest = 'models/fire.pt'
    
    # Create models directory
    Path('models').mkdir(exist_ok=True)
    
    if not os.path.exists(source):
        print(f"❌ fire.pt not found in repository: {source}")
        print("\n💡 Manual steps:")
        print("   1. Go to: https://github.com/Nexuszzz/Pblyoloiot")
        print("   2. Download fire.pt manually")
        print("   3. Save to: d:\\zakaiot\\models\\fire.pt")
        return False
    
    print(f"\n📦 Copying fire.pt...")
    print(f"   From: {source}")
    print(f"   To: {dest}")
    
    try:
        shutil.copy2(source, dest)
        
        # Check file size
        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"\n✅ fire.pt copied successfully!")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   Location: {os.path.abspath(dest)}")
        return True
        
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        return False


def cleanup(clone_dir):
    """Cleanup cloned repository"""
    if clone_dir and os.path.exists(clone_dir):
        print(f"\n🧹 Cleaning up...")
        try:
            shutil.rmtree(clone_dir)
            print(f"   Removed {clone_dir}/")
        except Exception as e:
            print(f"   Warning: Could not remove {clone_dir}: {e}")


def verify_model():
    """Verify fire.pt model"""
    model_path = 'models/fire.pt'
    
    print("\n" + "="*70)
    print("🔍 VERIFICATION")
    print("="*70 + "\n")
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return False
    
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"✅ Model found: {model_path}")
    print(f"   Size: {size_mb:.1f} MB")
    
    # Test loading model
    try:
        print("\n🧪 Testing model load...")
        from ultralytics import YOLO
        model = YOLO(model_path)
        print("✅ Model loads successfully!")
        print(f"   Task: {model.task}")
        print(f"   Classes: {model.names}")
        return True
    except ImportError:
        print("⚠️  Ultralytics not installed. Install with:")
        print("   pip install ultralytics")
        return True  # Model exists, just can't test
    except Exception as e:
        print(f"❌ Model load failed: {e}")
        print("\n💡 Model might be corrupted. Try:")
        print("   1. Delete models/fire.pt")
        print("   2. Run this script again")
        return False


def manual_download_instructions():
    """Show manual download instructions"""
    print("\n" + "="*70)
    print("📋 MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("If automatic download fails, download manually:\n")
    
    print("Option 1 - From GitHub:")
    print("  1. Go to: https://github.com/Nexuszzz/Pblyoloiot")
    print("  2. Click 'Code' → 'Download ZIP'")
    print("  3. Extract ZIP file")
    print("  4. Copy fire.pt to: d:\\zakaiot\\models\\fire.pt\n")
    
    print("Option 2 - Clone with Git:")
    print("  git clone https://github.com/Nexuszzz/Pblyoloiot")
    print("  copy Pblyoloiot\\fire.pt models\\fire.pt\n")
    
    print("Option 3 - From Roboflow:")
    print("  1. Go to: https://universe.roboflow.com/")
    print("  2. Search: 'fire detection yolo'")
    print("  3. Download trained model (.pt file)")
    print("  4. Rename to fire.pt")
    print("  5. Save to: d:\\zakaiot\\models\\fire.pt\n")


def main():
    """Main function"""
    print_banner()
    
    # Check if model already exists
    if os.path.exists('models/fire.pt'):
        size_mb = os.path.getsize('models/fire.pt') / (1024 * 1024)
        print(f"✅ fire.pt already exists!")
        print(f"   Location: {os.path.abspath('models/fire.pt')}")
        print(f"   Size: {size_mb:.1f} MB\n")
        
        response = input("Download again? (y/n) [n]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("\n✅ Using existing model")
            verify_model()
            return
        
        print("\n🔄 Re-downloading...")
    
    # Check git
    if not check_git():
        print("❌ Git not installed or not in PATH")
        print("\n💡 Install Git:")
        print("   Download from: https://git-scm.com/downloads")
        print("   Or use manual download method below\n")
        manual_download_instructions()
        return
    
    print("✅ Git is available\n")
    
    # Clone repository
    clone_dir = clone_repo()
    
    if clone_dir:
        # Copy fire.pt
        success = copy_fire_model(clone_dir)
        
        # Cleanup
        cleanup(clone_dir)
        
        if success:
            # Verify
            if verify_model():
                print("\n" + "="*70)
                print("✅ SETUP COMPLETE!")
                print("="*70)
                print("\n📝 Next Steps:")
                print("   1. Update config_yolov10.json with ESP32-CAM IP")
                print("   2. Run: python fire_detection_yolov10.py")
                print("   3. Test with lighter or candle\n")
            else:
                print("\n⚠️  Model downloaded but verification failed")
                print("   Try running anyway: python fire_detection_yolov10.py\n")
        else:
            print("\n❌ Failed to get fire.pt model")
            manual_download_instructions()
    else:
        print("\n❌ Failed to clone repository")
        manual_download_instructions()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
