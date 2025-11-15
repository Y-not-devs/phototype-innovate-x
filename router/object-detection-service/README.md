# Object Detection Service

Сервис для детекции подписей, печатей и QR-кодов в документах на базе YOLOv8/YOLOv11.

## 🎯 Основные возможности

- **Детекция 3 классов объектов:**
  - `signature` - подписи
  - `stamp` - печати
  - `qr_code` - QR-коды

- **REST API** для интеграции в pipeline обработки документов
- **Гибкая настройка** confidence и NMS порогов
- **Пакетная обработка** для многостраничных документов
- **Постобработка** с фильтрацией по размеру и aspect ratio

## 📁 Структура проекта

```
object-detection-service/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI сервис
│   ├── detector.py       # YOLO inference wrapper
│   └── config.py         # Конфигурация модели
├── scripts/
│   ├── analyze_dataset.py      # Анализ датасета
│   ├── convert_annotations.py  # Конвертация в YOLO формат
│   └── train_model.py          # Обучение модели
├── models/
│   └── best.pt           # Обученные веса (создать после обучения)
└── tests/
    └── __init__.py
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install ultralytics fastapi uvicorn pillow numpy
```

### 2. Запуск сервиса (для инференса)

```bash
cd router/object-detection-service
python -m app.main
```

API будет доступен на `http://localhost:8007`

### 3. Использование API

**Health check:**
```bash
curl http://localhost:8007/health
```

**Детекция объектов:**
```bash
curl -X POST "http://localhost:8007/detect" \
  -F "file=@document.jpg" \
  -F "page_number=0"
```

**Ответ:**
```json
{
  "success": true,
  "detections": [
    {
      "page": 0,
      "label": "signature",
      "bbox": [100.5, 200.3, 250.8, 280.1],
      "confidence": 0.8532
    },
    {
      "page": 0,
      "label": "stamp",
      "bbox": [50.2, 150.6, 180.4, 220.9],
      "confidence": 0.9241
    }
  ],
  "total_count": 2
}
```

## 📊 Подготовка датасета

### Анализ датасета

Перед обучением рекомендуется проанализировать датасет:

```bash
python scripts/analyze_dataset.py /path/to/dataset --output analysis_report.json
```

Датасет должен иметь структуру:
```
dataset/
├── images/
│   ├── doc1.jpg
│   ├── doc2.png
│   └── ...
└── labels/
    ├── doc1.txt
    ├── doc2.txt
    └── ...
```

**Анализ покажет:**
- Количество изображений
- Распределение классов
- Статистику разрешений
- Размеры объектов
- Рекомендации по улучшению

### Конвертация аннотаций в YOLO формат

Если аннотации в другом формате (COCO, Pascal VOC, LabelMe):

**COCO формат:**
```bash
python scripts/convert_annotations.py \
  --format coco \
  --input annotations.json \
  --images /path/to/images \
  --output dataset_yolo \
  --split
```

**Pascal VOC формат:**
```bash
python scripts/convert_annotations.py \
  --format voc \
  --input /path/to/annotations \
  --images /path/to/images \
  --output dataset_yolo \
  --split
```

**LabelMe формат:**
```bash
python scripts/convert_annotations.py \
  --format labelme \
  --input /path/to/labelme_dir \
  --output dataset_yolo \
  --split
```

Флаг `--split` автоматически разделит датасет на train/val/test.

## 🎓 Обучение модели

### Базовое обучение

```bash
python scripts/train_model.py \
  --train dataset_yolo/train/images \
  --val dataset_yolo/val/images \
  --model yolov8m.pt \
  --epochs 100 \
  --batch 16 \
  --imgsz 640 \
  --name document_detector
```

### Параметры обучения

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--model` | Базовая модель (yolov8n/s/m/l/x.pt) | yolov8m.pt |
| `--epochs` | Количество эпох | 100 |
| `--batch` | Размер батча | 16 |
| `--imgsz` | Размер входного изображения | 640 |
| `--device` | Устройство (0 для GPU, cpu) | 0 |
| `--patience` | Early stopping patience | 50 |
| `--conf` | Confidence threshold | 0.25 |
| `--iou` | NMS IoU threshold | 0.7 |

### Выбор размера модели

- **YOLOv8n** (nano): Быстрая, но менее точная. Для embedded/mobile.
- **YOLOv8s** (small): Баланс скорость/точность для CPU.
- **YOLOv8m** (medium): **Рекомендуется** - хороший баланс.
- **YOLOv8l** (large): Высокая точность, требует GPU.
- **YOLOv8x** (xlarge): Максимальная точность, медленная.

### Дообучение (fine-tuning)

Для дообучения существующей модели:

```bash
python scripts/train_model.py \
  --train dataset_yolo/train/images \
  --val dataset_yolo/val/images \
  --model runs/detect/document_detector/weights/best.pt \
  --epochs 50 \
  --name document_detector_v2
```

### Результаты обучения

После обучения веса сохраняются в:
```
runs/detect/document_detector/
├── weights/
│   ├── best.pt      # Лучшие веса (использовать для инференса)
│   └── last.pt      # Последние веса
├── results.png      # График метрик
├── confusion_matrix.png
└── ...
```

**Скопируйте веса в models/:**
```bash
cp runs/detect/document_detector/weights/best.pt models/
```

## ⚙️ Настройка конфигурации

Параметры модели настраиваются в `app/config.py`:

### Пороги детекции

```python
MODEL_CONFIG = {
    "confidence_threshold": 0.35,  # Основной порог уверенности
    "nms_threshold": 0.4,          # Порог NMS (перекрытие боксов)
    "max_detections": 100,
    "imgsz": 640,
}

# Индивидуальные пороги для классов
CLASS_THRESHOLDS = {
    "signature": 0.35,  # Подписи (вариативны)
    "stamp": 0.40,      # Печати (более консистентны)
    "qr_code": 0.45     # QR-коды (четкие паттерны)
}
```

### Постобработка

```python
POST_PROCESS_CONFIG = {
    "min_bbox_area": 100,        # Минимальная площадь (пиксели)
    "max_bbox_ratio": 0.8,       # Макс размер относительно изображения
    "min_aspect_ratio": 0.1,     # Минимальное соотношение сторон
    "max_aspect_ratio": 10.0     # Максимальное соотношение сторон
}
```

## 🔧 Использование в Python

### Быстрый инференс

```python
from router.object_detection_service.app.detector import detect_objects

# Детекция на одном изображении
detections = detect_objects("document.jpg")

for det in detections:
    print(f"{det['label']}: {det['confidence']:.2f} at {det['bbox']}")
```

### Использование класса ObjectDetector

```python
from router.object_detection_service.app.detector import ObjectDetector
from PIL import Image

# Инициализация детектора
detector = ObjectDetector(
    model_path="models/best.pt",
    confidence_threshold=0.4,
    device="cuda"  # или "cpu"
)

# Детекция на изображении
image = Image.open("document.jpg")
detections = detector.detect(image, page_number=0)

# Пакетная обработка
images = [Image.open(f"page_{i}.jpg") for i in range(5)]
all_detections = detector.batch_detect(images)
```

### Интеграция с FastAPI

```python
import requests

# Загрузка файла
with open("document.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8007/detect",
        files={"file": f},
        params={"page_number": 0}
    )

result = response.json()
print(f"Найдено объектов: {result['total_count']}")
```

## 📈 Оптимизация производительности

### 1. Подбор порогов

Начните с базовых значений и корректируйте:

```python
# Низкий Recall (пропускает объекты)
→ Уменьшите confidence_threshold (0.35 → 0.25)

# Высокий False Positive (ложные срабатывания)
→ Увеличьте confidence_threshold (0.35 → 0.45)

# Дублирующиеся боксы
→ Уменьшите nms_threshold (0.4 → 0.3)
```

### 2. Аугментация данных

При обучении YOLO автоматически применяет аугментации:
- Мозаика (mosaic)
- MixUp
- Изменение яркости/контраста
- Афинные трансформации

Для усиления аугментации создайте `hyp.yaml`:
```yaml
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 10.0
translate: 0.1
scale: 0.5
shear: 5.0
```

И обучите с кастомной конфигурацией:
```bash
python scripts/train_model.py ... --cfg hyp.yaml
```

### 3. Увеличение датасета

**Рекомендации:**
- Минимум **300-500 изображений** на класс
- Минимум **1000-2000 примеров** каждого класса
- Сбалансированное распределение классов

**Методы увеличения:**
- Фотографирование дополнительных документов
- Аугментация через `albumentations` или `imgaug`
- Synthetic data generation (если применимо)

## 🧪 Тестирование модели

### Создание теста

```python
# tests/test_detector.py
import pytest
from app.detector import ObjectDetector
from PIL import Image

def test_signature_detection():
    detector = ObjectDetector()
    image = Image.open("test_data/doc_with_signature.jpg")
    detections = detector.detect(image)
    
    # Проверка, что подпись найдена
    signatures = [d for d in detections if d['label'] == 'signature']
    assert len(signatures) > 0
    assert signatures[0]['confidence'] > 0.5

def test_batch_processing():
    detector = ObjectDetector()
    images = [Image.open(f"test_data/page{i}.jpg") for i in range(3)]
    detections = detector.batch_detect(images)
    
    assert len(detections) > 0
```

Запуск тестов:
```bash
pytest tests/
```

## 📝 Рекомендации по разметке

### Разметка подписей
- Включайте **всю подпись**, включая росчерк
- Не размечайте инициалы без подписи
- Учитывайте цифровые подписи отдельно (если требуется)

### Разметка печатей
- Включайте **весь круг/овал** печати
- Захватывайте текст на границе
- Не размечайте размытые/частично видимые печати (< 50%)

### Разметка QR-кодов
- Включайте **только сам QR-код**
- Не включайте окружающий текст
- Учитывайте DataMatrix как отдельный класс (если нужно)

## 🔍 Отладка

### Визуализация детекций

```python
from PIL import Image, ImageDraw

image = Image.open("document.jpg")
detections = detector.detect(image)

draw = ImageDraw.Draw(image)
for det in detections:
    bbox = det['bbox']
    label = det['label']
    conf = det['confidence']
    
    # Рисуем бокс
    draw.rectangle(bbox, outline='red', width=2)
    draw.text((bbox[0], bbox[1] - 15), f"{label}: {conf:.2f}", fill='red')

image.save("output_with_detections.jpg")
```

### Логирование

Включите подробное логирование:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Дополнительные материалы

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [YOLO Dataset Format](https://docs.ultralytics.com/datasets/)
- [Model Training Tips](https://docs.ultralytics.com/modes/train/)

## 🤝 Интеграция с существующими сервисами

### Добавление в router-service

```python
# router/router-service/app/main.py
import requests

OBJECT_DETECTION_SERVICE_URL = "http://localhost:8007"

@app.post("/process_document")
async def process_document(file: UploadFile):
    # ... preprocessing ...
    
    # Детекция объектов
    response = requests.post(
        f"{OBJECT_DETECTION_SERVICE_URL}/detect",
        files={"file": processed_image}
    )
    detections = response.json()["detections"]
    
    # ... дальнейшая обработка ...
    return {"ocr_result": ocr_text, "objects": detections}
```

## 🎯 Метрики качества

После обучения проверьте метрики:

- **mAP@0.5**: > 0.85 (хорошо), > 0.90 (отлично)
- **Precision**: > 0.85
- **Recall**: > 0.80
- **F1-Score**: > 0.80

Если метрики низкие:
1. Увеличьте датасет
2. Улучшите качество разметки
3. Попробуйте больший размер модели
4. Увеличьте epochs
5. Настройте аугментации

---

**Примечание:** Модель обучается на вашем датасете. Файл `models/best.pt` должен быть создан после обучения. Для начала работы обучите модель на размеченном датасете документов.
