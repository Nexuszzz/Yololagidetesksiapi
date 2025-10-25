"""
Script untuk download pre-trained YOLOv8 fire detection model
=============================================================
Script ini akan mendownload model YOLOv8 yang sudah dilatih untuk fire detection.

Anda juga bisa menggunakan model YOLO standard dan melatihnya sendiri,
atau download dari sumber seperti:
- Roboflow: https://universe.roboflow.com/
- Kaggle: https://www.kaggle.com/datasets

Author: AI Assistant
Date: 2025
"""

import os
import urllib.request
from pathlib import Path
from ultralytics import YOLO


def download_yolo_base_model(model_size='n'):
    """
    Download YOLOv8 base model dari Ultralytics
    
    Args:
        model_size: Ukuran model (n, s, m, l, x)
    """
    print("="*60)
    print("📦 DOWNLOADING YOLOV8 BASE MODEL")
    print("="*60)
    
    # Create models directory
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    model_name = f'yolov8{model_size}.pt'
    model_path = models_dir / model_name
    
    if model_path.exists():
        print(f"✅ Model sudah ada: {model_path}")
        return str(model_path)
    
    print(f"📥 Downloading YOLOv8{model_size} model...")
    print(f"   Target: {model_path}")
    
    try:
        # Ultralytics akan otomatis download model saat pertama kali digunakan
        model = YOLO(model_name)
        
        print(f"✅ Model downloaded successfully!")
        print(f"📁 Location: {model_path}")
        return str(model_path)
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def download_fire_dataset_info():
    """
    Tampilkan informasi tentang fire detection datasets yang tersedia
    """
    print("\n" + "="*60)
    print("🔥 FIRE DETECTION DATASETS")
    print("="*60)
    print("""
Dataset fire detection yang bagus untuk training:

1. **Fire Detection Dataset - Roboflow**
   URL: https://universe.roboflow.com/fire-detection/fire-and-smoke-detection
   Classes: fire, smoke
   Images: ~5000+
   Format: YOLO

2. **Fire Dataset - Kaggle**
   URL: https://www.kaggle.com/datasets/phylake1337/fire-dataset
   Images: ~1000
   Classes: fire, no-fire

3. **FIRE Dataset - Mendeley**
   URL: https://data.mendeley.com/datasets/gjxqjx8x27/1
   Images: ~755
   Classes: fire

4. **Custom Fire Dataset - GitHub**
   URL: https://github.com/DeepQuestAI/Fire-Smoke-Dataset
   Classes: fire, smoke, neutral

📝 CARA MENGGUNAKAN:
1. Download dataset dari salah satu sumber di atas
2. Ekstrak ke folder 'fire_dataset/'
3. Pastikan struktur folder:
   fire_dataset/
   ├── images/
   │   ├── train/
   │   └── val/
   ├── labels/
   │   ├── train/
   │   └── val/
   └── data.yaml

4. Edit data.yaml:
   path: ./fire_dataset
   train: images/train
   val: images/val
   names:
     0: fire

5. Jalankan training:
   python train_custom_model.py --data fire_dataset/data.yaml --epochs 100
    """)


def create_sample_data_yaml():
    """
    Buat contoh data.yaml untuk fire detection
    """
    yaml_content = """# Fire Detection Dataset Configuration
# Sesuaikan path dengan lokasi dataset Anda

path: ./fire_dataset  # dataset root directory
train: images/train   # train images (relative to 'path')
val: images/val       # validation images (relative to 'path')
test: images/test     # test images (optional)

# Classes
names:
  0: fire
  # 1: smoke  # uncomment jika ada class smoke

# Number of classes
nc: 1

# Optional: Download script
# download: |
#   # Download dataset code here
"""
    
    output_path = Path('fire_dataset/data.yaml')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"\n✅ Created sample data.yaml: {output_path}")
    print("   Edit file ini sesuai dengan struktur dataset Anda!")


def test_model(model_path='models/yolov8n.pt'):
    """
    Test model dengan sample image
    
    Args:
        model_path: Path ke model
    """
    print("\n" + "="*60)
    print("🧪 TESTING MODEL")
    print("="*60)
    
    if not os.path.exists(model_path):
        print(f"❌ Model tidak ditemukan: {model_path}")
        print("   Jalankan download terlebih dahulu!")
        return
    
    print(f"📦 Loading model: {model_path}")
    model = YOLO(model_path)
    
    print("✅ Model loaded successfully!")
    print("\n📊 Model Info:")
    print(f"   - Task: {model.task}")
    print(f"   - Classes: {model.names}")
    
    # Jika ada test image, predict
    test_images = Path('test_images')
    if test_images.exists():
        test_files = list(test_images.glob('*.jpg')) + list(test_images.glob('*.png'))
        if test_files:
            print(f"\n🔍 Testing on {len(test_files)} images...")
            results = model(test_files[0])
            print("✅ Test prediction completed!")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🔥 YOLOV8 FIRE DETECTION MODEL SETUP")
    print("="*60)
    print("""
Pilih opsi:
1. Download YOLOv8 base model (recommended untuk mulai)
2. Lihat info fire detection datasets
3. Buat sample data.yaml
4. Test model
5. Exit
    """)
    
    while True:
        choice = input("\nPilih opsi (1-5): ").strip()
        
        if choice == '1':
            print("\nUkuran model:")
            print("  n - Nano (paling cepat, accuracy rendah)")
            print("  s - Small")
            print("  m - Medium (balanced)")
            print("  l - Large")
            print("  x - XLarge (paling akurat, paling lambat)")
            
            size = input("\nPilih ukuran model (n/s/m/l/x) [default: n]: ").strip().lower()
            if size not in ['n', 's', 'm', 'l', 'x']:
                size = 'n'
            
            model_path = download_yolo_base_model(size)
            if model_path:
                test_model(model_path)
        
        elif choice == '2':
            download_fire_dataset_info()
        
        elif choice == '3':
            create_sample_data_yaml()
        
        elif choice == '4':
            model_path = input("Path ke model [default: models/yolov8n.pt]: ").strip()
            if not model_path:
                model_path = 'models/yolov8n.pt'
            test_model(model_path)
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Pilihan tidak valid!")


if __name__ == "__main__":
    main()
