# 🔥 Cara Menggunakan Model Fire-Specific

## ⚠️ Masalah Saat Ini

**YOLOv8n standard** yang didownload adalah model umum yang trained untuk detect 80 classes dari COCO dataset:
- person, bicycle, car, dog, cat, dll
- **TIDAK ADA class "fire"**

Itulah mengapa sistem mendeteksi "person" sebagai "fire" karena code sebelumnya menggunakan `class_id == 0` (yang adalah "person" di COCO).

## ✅ Solusi yang Sudah Dilakukan

Saya sudah update code untuk:
1. ✅ Remove logic `class_id == 0` yang salah
2. ✅ Only detect jika class name mengandung "fire"
3. ✅ Increase confidence threshold ke 0.75
4. ✅ Add size filtering untuk skip deteksi kecil

**NAMUN**, karena YOLOv8n standard tidak punya class "fire", sistem sekarang **tidak akan detect apa-apa**.

## 🎯 Solusi Jangka Panjang: Train Custom Model

Untuk fire detection yang akurat, Anda **HARUS** train model custom dengan dataset fire.

### Option 1: Train dari Scratch (RECOMMENDED)

#### Step 1: Download Fire Dataset

Pilih salah satu dataset:

**A. Roboflow Fire Detection Dataset** (Recommended)
```
URL: https://universe.roboflow.com/fire-detection/fire-and-smoke-detection
Classes: fire, smoke
Format: YOLOv8
Images: 5000+
```

**B. Fire Dataset - Kaggle**
```
URL: https://www.kaggle.com/datasets/phylake1337/fire-dataset
Images: 1000+
```

**C. Custom Fire & Smoke Dataset**
```
URL: https://universe.roboflow.com/aiotproject/fire-and-smoke-dataset
Classes: fire, smoke
```

#### Step 2: Prepare Dataset

1. Download dataset dalam format YOLO
2. Extract ke folder `fire_dataset/`
3. Structure harus seperti ini:

```
fire_dataset/
├── images/
│   ├── train/          # Training images
│   └── val/            # Validation images
├── labels/
│   ├── train/          # Training labels (.txt)
│   └── val/            # Validation labels (.txt)
└── data.yaml           # Dataset config
```

#### Step 3: Create data.yaml

```yaml
# fire_dataset/data.yaml
path: ./fire_dataset
train: images/train
val: images/val

names:
  0: fire
  # 1: smoke  # Uncomment jika dataset punya class smoke

nc: 1  # Number of classes
```

#### Step 4: Train Model

```bash
# Basic training (100 epochs)
python train_custom_model.py --data fire_dataset/data.yaml --epochs 100

# Advanced training (dengan GPU)
python train_custom_model.py \
    --data fire_dataset/data.yaml \
    --model m \
    --epochs 150 \
    --batch-size 16 \
    --img-size 640 \
    --device 0
```

**Training time:**
- CPU: 2-4 hours
- GPU (GTX 1060+): 30-60 minutes

#### Step 5: Use Trained Model

Setelah training selesai, model tersimpan di:
```
fire_detection_training/fire_yolov8/weights/best.pt
```

Update `config.json`:
```json
{
    "model_path": "fire_detection_training/fire_yolov8/weights/best.pt",
    "confidence_threshold": 0.5
}
```

Run detection:
```bash
python fire_detection.py
```

---

### Option 2: Download Pre-trained Fire Model

Jika tidak mau training sendiri, download model yang sudah dilatih:

#### A. From Roboflow (Easiest)

1. Go to: https://universe.roboflow.com/fire-detection
2. Find a fire detection model
3. Download in YOLOv8 PyTorch format
4. Extract `.pt` file ke `models/`
5. Update config.json dengan path model

#### B. From Hugging Face

1. Search "fire detection yolov8" di Hugging Face
2. Download model weights
3. Save to `models/fire-yolov8.pt`
4. Update config.json

---

### Option 3: Use Color-Based Fire Detection (Temporary)

Jika tidak bisa train model, gunakan color-based detection sebagai fallback:

```python
# fire_detection_color.py
import cv2
import numpy as np

def detect_fire_by_color(frame):
    """Simple fire detection using color"""
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define fire color range in HSV
    # Fire is typically: Red-Orange-Yellow
    lower_fire1 = np.array([0, 50, 50])      # Red
    upper_fire1 = np.array([30, 255, 255])
    
    lower_fire2 = np.array([160, 50, 50])    # Red (wrap around)
    upper_fire2 = np.array([180, 255, 255])
    
    # Create masks
    mask1 = cv2.inRange(hsv, lower_fire1, upper_fire1)
    mask2 = cv2.inRange(hsv, lower_fire2, upper_fire2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # Minimum area threshold
            x, y, w, h = cv2.boundingRect(contour)
            detections.append({
                'bbox': (x, y, x+w, y+h),
                'confidence': 0.8,
                'class': 'fire (color-based)'
            })
    
    return detections
```

**Note:** Color-based detection kurang akurat dan banyak false positive, tapi bisa jadi temporary solution.

---

## 📊 Expected Accuracy

### YOLOv8n Standard (COCO)
- ❌ Fire Detection: 0% (no fire class)
- ❌ False Positives: Very High

### YOLOv8 Custom Trained
- ✅ Fire Detection: 85-95%
- ✅ False Positives: Low
- ✅ Real-time: 15-30 FPS

### Color-Based Detection
- ⚠️ Fire Detection: 60-70%
- ❌ False Positives: High (detects red objects)
- ✅ Real-time: 30+ FPS

---

## 🚀 Quick Start Guide

### Jika ingin akurasi terbaik:

```bash
# 1. Download fire dataset
# Go to: https://universe.roboflow.com/fire-detection/fire-and-smoke-detection
# Download in YOLOv8 format
# Extract to fire_dataset/

# 2. Train model
python train_custom_model.py --data fire_dataset/data.yaml --epochs 100

# 3. Update config
# Edit config.json, set model_path ke trained model

# 4. Run detection
python fire_detection.py
```

### Jika ingin cepat (tapi kurang akurat):

```bash
# 1. Download pre-trained model dari Roboflow
# Save to models/fire-pretrained.pt

# 2. Update config.json
{
    "model_path": "models/fire-pretrained.pt",
    "confidence_threshold": 0.5
}

# 3. Run detection
python fire_detection.py
```

---

## 💡 Tips untuk Akurasi Terbaik

1. **Dataset Quality**
   - Use minimum 1000 fire images
   - Diverse conditions (indoor, outdoor, day, night)
   - Multiple fire types (small, large, smoke)

2. **Training Parameters**
   - More epochs = better (100-200)
   - Use data augmentation
   - Validate on diverse test set

3. **Detection Tuning**
   - Adjust confidence threshold (0.4-0.7)
   - Use NMS (Non-Maximum Suppression)
   - Filter by size and aspect ratio

4. **Camera Setup**
   - Good lighting
   - Stable mounting
   - Clear view of monitored area

---

## 🔧 Troubleshooting

**Q: Model masih detect person sebagai fire?**
A: Pastikan sudah update code dan config. Run `python fire_detection.py` dengan code terbaru.

**Q: Model tidak detect api sama sekali?**
A: Ini normal jika pakai YOLOv8n standard. Anda perlu train custom model.

**Q: Training too slow?**
A: Use GPU, reduce batch size, atau use smaller model (yolov8n).

**Q: Out of memory saat training?**
A: Reduce batch size (`--batch-size 8` atau `4`)

---

## 📚 Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com/
- **Fire Datasets**: https://universe.roboflow.com/search?q=fire
- **Training Guide**: https://docs.ultralytics.com/modes/train/
- **Custom Dataset**: https://docs.ultralytics.com/datasets/

---

**🔥 Bottom Line:**

Untuk fire detection yang akurat, **HARUS train custom model** dengan fire dataset. Model YOLOv8 standard tidak punya class "fire".

Estimated time: 2-4 hours (download dataset + training)
Result: 85-95% accuracy untuk fire detection

---

Made with ❤️ | 2025
