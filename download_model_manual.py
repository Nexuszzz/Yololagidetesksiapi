"""
Manual YOLOv8 Model Downloader
================================
Script ini akan download model YOLOv8 secara manual jika auto-download gagal.

Author: AI Assistant
Date: 2025
"""

import os
import urllib.request
from pathlib import Path
import sys


def download_file(url, destination, filename):
    """
    Download file dengan progress bar
    
    Args:
        url: URL file yang akan didownload
        destination: Folder tujuan
        filename: Nama file
    """
    filepath = os.path.join(destination, filename)
    
    if os.path.exists(filepath):
        print(f"✅ File sudah ada: {filepath}")
        return True
    
    print(f"📥 Downloading {filename}...")
    print(f"   URL: {url}")
    print(f"   Destination: {filepath}")
    print()
    
    try:
        def progress_hook(count, block_size, total_size):
            """Show download progress"""
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                downloaded_mb = count * block_size / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                
                # Progress bar
                bar_length = 40
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                sys.stdout.write(f"\r   [{bar}] {percent}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
                sys.stdout.flush()
        
        urllib.request.urlretrieve(url, filepath, progress_hook)
        print("\n✅ Download completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def download_yolov8_models():
    """Download YOLOv8 models"""
    print("="*70)
    print("📦 YOLOV8 MODEL DOWNLOADER")
    print("="*70)
    print()
    
    # Create models directory
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    # YOLOv8 models with URLs
    models = {
        'yolov8n.pt': {
            'url': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt',
            'size': '6.2 MB',
            'description': 'Nano - Fastest, lowest accuracy'
        },
        'yolov8s.pt': {
            'url': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt',
            'size': '22 MB',
            'description': 'Small - Fast, good accuracy'
        },
        'yolov8m.pt': {
            'url': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt',
            'size': '52 MB',
            'description': 'Medium - Balanced'
        },
        'yolov8l.pt': {
            'url': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt',
            'size': '88 MB',
            'description': 'Large - Slow, high accuracy'
        },
        'yolov8x.pt': {
            'url': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x.pt',
            'size': '131 MB',
            'description': 'XLarge - Slowest, highest accuracy'
        }
    }
    
    print("Available models:")
    print()
    for i, (model_name, info) in enumerate(models.items(), 1):
        print(f"{i}. {model_name:<15} ({info['size']:<8}) - {info['description']}")
    print()
    
    # Ask user which model to download
    while True:
        choice = input("Pilih model untuk download (1-5, atau 'all' untuk semua) [1]: ").strip().lower()
        
        if choice == '':
            choice = '1'
        
        if choice == 'all':
            selected_models = list(models.keys())
            break
        elif choice in ['1', '2', '3', '4', '5']:
            selected_models = [list(models.keys())[int(choice) - 1]]
            break
        else:
            print("❌ Pilihan tidak valid. Coba lagi.")
    
    print()
    print("="*70)
    print("Starting downloads...")
    print("="*70)
    print()
    
    success_count = 0
    for model_name in selected_models:
        info = models[model_name]
        if download_file(info['url'], 'models', model_name):
            success_count += 1
        print()
    
    print("="*70)
    print(f"✅ Downloaded {success_count}/{len(selected_models)} models successfully")
    print("="*70)
    print()
    
    # Show next steps
    if success_count > 0:
        print("📝 Next Steps:")
        print()
        print("1. Update config.json:")
        print('   "model_path": "models/yolov8n.pt"')
        print()
        print("2. Run fire detection:")
        print("   python fire_detection.py")
        print()


def verify_models():
    """Verify downloaded models"""
    print("="*70)
    print("🔍 VERIFYING MODELS")
    print("="*70)
    print()
    
    models_dir = Path('models')
    if not models_dir.exists():
        print("❌ models/ directory not found")
        return
    
    pt_files = list(models_dir.glob('*.pt'))
    
    if not pt_files:
        print("❌ No model files found in models/")
        print("   Run download first!")
    else:
        print(f"✅ Found {len(pt_files)} model(s):")
        print()
        for model_file in pt_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"   ✓ {model_file.name:<15} ({size_mb:.1f} MB)")
    
    print()


def main():
    """Main function"""
    print()
    print("="*70)
    print("🔥 YOLOV8 MODEL DOWNLOADER")
    print("="*70)
    print()
    print("Gunakan script ini jika auto-download gagal.")
    print()
    print("Options:")
    print("1. Download models")
    print("2. Verify downloaded models")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Pilih option (1-3) [1]: ").strip()
        
        if choice == '' or choice == '1':
            download_yolov8_models()
            break
        elif choice == '2':
            verify_models()
            break
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise
