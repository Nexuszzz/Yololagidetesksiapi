"""
Setup script untuk ESP32-CAM Fire Detection System
==================================================
Script ini akan membantu setup environment dan download dependencies.

Author: AI Assistant
Date: 2025
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    """Print banner"""
    print("\n" + "="*70)
    print("🔥 ESP32-CAM FIRE DETECTION SYSTEM - SETUP")
    print("="*70 + "\n")


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    dirs = [
        'models',
        'logs',
        'recordings',
        'detections',
        'fire_dataset/images/train',
        'fire_dataset/images/val',
        'fire_dataset/labels/train',
        'fire_dataset/labels/val',
        'test_images'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}")
    
    print("✅ Directories created")


def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python packages...")
    print("   This may take a few minutes...\n")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installation failed: {e}")
        return False


def download_yolo_model():
    """Download YOLOv8 base model"""
    print("\n🤖 Downloading YOLOv8 model...")
    
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # Will auto-download
        print("✅ YOLOv8n model downloaded")
        return True
    except Exception as e:
        print(f"❌ Model download failed: {e}")
        return False


def create_sample_config():
    """Create sample configuration files"""
    print("\n⚙️  Creating configuration files...")
    
    # Check if config.json already exists
    if not os.path.exists('config.json'):
        import json
        config = {
            "esp32_cam_url": "http://192.168.2.100:81/stream",
            "model_path": "models/yolov8n.pt",
            "confidence_threshold": 0.5,
            "alert_cooldown": 5,
            "enable_sound_alert": True,
            "enable_video_recording": True,
            "max_recording_duration": 60,
            "log_dir": "logs",
            "recordings_dir": "recordings",
            "display_window": True,
            "save_detection_images": True
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        print("   ✓ config.json")
    else:
        print("   ✓ config.json (already exists)")
    
    # Create sample data.yaml for training
    if not os.path.exists('fire_dataset/data.yaml'):
        yaml_content = """# Fire Detection Dataset Configuration
path: ./fire_dataset
train: images/train
val: images/val

names:
  0: fire

nc: 1
"""
        with open('fire_dataset/data.yaml', 'w') as f:
            f.write(yaml_content)
        print("   ✓ fire_dataset/data.yaml")
    else:
        print("   ✓ fire_dataset/data.yaml (already exists)")
    
    print("✅ Configuration files created")


def print_next_steps():
    """Print next steps"""
    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print("\n📋 Next Steps:\n")
    print("1️⃣  Setup ESP32-CAM:")
    print("   - Upload esp32_cam_stream/esp32_cam_stream.ino ke ESP32-CAM")
    print("   - Update WiFi credentials di code")
    print("   - Catat IP address dari Serial Monitor\n")
    
    print("2️⃣  Update Configuration:")
    print("   - Edit config.json")
    print("   - Update esp32_cam_url dengan IP ESP32-CAM Anda\n")
    
    print("3️⃣  Test Connection:")
    print("   python test_esp32_stream.py --ping\n")
    
    print("4️⃣  Run Fire Detection:")
    print("   python fire_detection.py\n")
    
    print("5️⃣  (Optional) Train Custom Model:")
    print("   - Download fire dataset")
    print("   - Place in fire_dataset/ folder")
    print("   - Run: python train_custom_model.py\n")
    
    print("="*70)
    print("\n📚 For detailed instructions, read README.md")
    print("🐛 For issues, check Troubleshooting section in README.md\n")


def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = ['cv2', 'numpy', 'ultralytics', 'requests', 'torch']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed")
        return True


def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create directories
    create_directories()
    
    # Ask user if they want to install packages
    print("\n" + "="*70)
    response = input("\n📦 Install Python packages now? (y/n) [y]: ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        if install_requirements():
            # Download model
            download_yolo_model()
    else:
        print("\n⚠️  Skipping package installation")
        print("   Run later: pip install -r requirements.txt")
    
    # Create config files
    create_sample_config()
    
    # Check if everything is ready
    print("\n" + "="*70)
    print("🧪 SYSTEM CHECK")
    print("="*70)
    
    check_dependencies()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Setup error: {e}")
        raise
