"""
Script untuk melatih YOLOv8 model custom untuk fire detection
============================================================
Script ini membantu Anda melatih model YOLOv8 khusus untuk deteksi api
menggunakan dataset custom.

Langkah-langkah:
1. Siapkan dataset dalam format YOLO (images + labels)
2. Buat file data.yaml dengan konfigurasi dataset
3. Jalankan script ini
4. Model hasil training akan disimpan di runs/detect/train/weights/

Author: AI Assistant
Date: 2025
"""

from ultralytics import YOLO
import os
from datetime import datetime


def train_fire_detection_model(
    data_yaml='fire_dataset/data.yaml',
    model_size='n',  # n, s, m, l, x
    epochs=100,
    img_size=640,
    batch_size=16,
    device='0',  # '0' untuk GPU, 'cpu' untuk CPU
    project='fire_detection_training',
    name='fire_yolov8'
):
    """
    Train YOLOv8 model untuk fire detection
    
    Args:
        data_yaml: Path ke file data.yaml yang berisi konfigurasi dataset
        model_size: Ukuran model (n=nano, s=small, m=medium, l=large, x=xlarge)
        epochs: Jumlah epoch training
        img_size: Ukuran input image
        batch_size: Batch size untuk training
        device: Device untuk training ('0' untuk GPU, 'cpu' untuk CPU)
        project: Nama project directory
        name: Nama experiment
    """
    
    print("="*60)
    print("🔥 YOLOv8 FIRE DETECTION MODEL TRAINING")
    print("="*60)
    print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 Model Size: YOLOv8{model_size}")
    print(f"📊 Dataset: {data_yaml}")
    print(f"🔄 Epochs: {epochs}")
    print(f"🖼️  Image Size: {img_size}")
    print(f"📦 Batch Size: {batch_size}")
    print(f"💻 Device: {device}")
    print("="*60 + "\n")
    
    # Check if data.yaml exists
    if not os.path.exists(data_yaml):
        print(f"❌ Error: Data file '{data_yaml}' tidak ditemukan!")
        print("\n📝 Buat file data.yaml dengan format berikut:")
        print("""
# data.yaml
path: ./fire_dataset  # dataset root directory
train: images/train   # train images (relative to 'path')
val: images/val       # val images (relative to 'path')

# Classes
names:
  0: fire
        """)
        return
    
    # Load YOLOv8 model
    model_name = f'yolov8{model_size}.pt'
    print(f"📦 Loading YOLOv8{model_size} pretrained model...")
    model = YOLO(model_name)
    print("✅ Model loaded successfully\n")
    
    # Train model
    print("🚀 Starting training...")
    try:
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=device,
            project=project,
            name=name,
            pretrained=True,
            optimizer='Adam',
            verbose=True,
            patience=50,  # early stopping patience
            save=True,
            save_period=10,  # save checkpoint every 10 epochs
            cache=False,
            rect=False,
            cos_lr=True,  # cosine learning rate scheduler
            close_mosaic=10,  # disable mosaic augmentation for final 10 epochs
            resume=False,  # resume from last checkpoint
            amp=True,  # Automatic Mixed Precision training
            fraction=1.0,  # dataset fraction to train on
            profile=False,
            # Augmentation settings
            hsv_h=0.015,  # hue augmentation
            hsv_s=0.7,    # saturation augmentation
            hsv_v=0.4,    # value augmentation
            degrees=0.0,  # rotation augmentation
            translate=0.1,  # translation augmentation
            scale=0.5,    # scale augmentation
            shear=0.0,    # shear augmentation
            perspective=0.0,  # perspective augmentation
            flipud=0.0,   # flip up-down augmentation
            fliplr=0.5,   # flip left-right augmentation
            mosaic=1.0,   # mosaic augmentation
            mixup=0.0,    # mixup augmentation
            copy_paste=0.0,  # copy-paste augmentation
        )
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETED!")
        print("="*60)
        print(f"📅 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Results saved to: {project}/{name}/")
        print(f"🏆 Best model: {project}/{name}/weights/best.pt")
        print(f"📊 Last model: {project}/{name}/weights/last.pt")
        print("="*60 + "\n")
        
        # Show training metrics
        print("📊 Training Metrics:")
        print(f"   - mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
        print(f"   - mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
        print(f"   - Precision: {results.results_dict.get('metrics/precision(B)', 'N/A')}")
        print(f"   - Recall: {results.results_dict.get('metrics/recall(B)', 'N/A')}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        raise


def validate_model(model_path, data_yaml):
    """
    Validate trained model
    
    Args:
        model_path: Path ke model weights (.pt file)
        data_yaml: Path ke data.yaml
    """
    print("\n" + "="*60)
    print("🧪 VALIDATING MODEL")
    print("="*60)
    
    model = YOLO(model_path)
    results = model.val(data=data_yaml)
    
    print("\n✅ Validation complete!")
    print(f"   - mAP50: {results.box.map50}")
    print(f"   - mAP50-95: {results.box.map}")
    print(f"   - Precision: {results.box.mp}")
    print(f"   - Recall: {results.box.mr}")


def export_model(model_path, export_format='onnx'):
    """
    Export model ke format lain
    
    Args:
        model_path: Path ke model weights
        export_format: Format export (onnx, torchscript, tflite, etc.)
    """
    print(f"\n📦 Exporting model to {export_format.upper()}...")
    model = YOLO(model_path)
    model.export(format=export_format)
    print(f"✅ Model exported successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLOv8 Fire Detection Model')
    parser.add_argument('--data', type=str, default='fire_dataset/data.yaml',
                       help='Path to data.yaml')
    parser.add_argument('--model', type=str, default='n',
                       choices=['n', 's', 'm', 'l', 'x'],
                       help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--img-size', type=int, default=640,
                       help='Input image size')
    parser.add_argument('--batch-size', type=int, default=16,
                       help='Batch size')
    parser.add_argument('--device', type=str, default='0',
                       help='Device to use (0 for GPU, cpu for CPU)')
    parser.add_argument('--validate', action='store_true',
                       help='Validate model after training')
    parser.add_argument('--export', type=str, default=None,
                       help='Export format (onnx, torchscript, tflite, etc.)')
    
    args = parser.parse_args()
    
    # Train model
    train_fire_detection_model(
        data_yaml=args.data,
        model_size=args.model,
        epochs=args.epochs,
        img_size=args.img_size,
        batch_size=args.batch_size,
        device=args.device
    )
    
    # Validate if requested
    if args.validate:
        best_model = f"fire_detection_training/fire_yolov8/weights/best.pt"
        if os.path.exists(best_model):
            validate_model(best_model, args.data)
    
    # Export if requested
    if args.export:
        best_model = f"fire_detection_training/fire_yolov8/weights/best.pt"
        if os.path.exists(best_model):
            export_model(best_model, args.export)
