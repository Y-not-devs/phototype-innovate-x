# Примеры ответов CV API

## Пример 1: Анализ однострочного изображения с подписью

### Запрос

```bash
curl -X POST "http://127.0.0.1:8000/analyze-document-cv" \
  -F "file=@contract_signature.jpg" \
  -F "return_annotated=true"
```

### Ответ

```json
{
  "success": true,
  "filename": "contract_signature.jpg",
  "file_type": "image",
  "total_pages": 1,
  "total_detections": 1,
  "summary": {
    "signature": 1,
    "stamp": 0,
    "qr_code": 0
  },
  "pages": [
    {
      "page": 1,
      "detections": [
        {
          "class_id": 0,
          "class_name": "signature",
          "confidence": 0.89,
          "bbox": [120, 450, 280, 520]
        }
      ]
    }
  ],
  "annotated_images": [
    "contract_signature_annotated.png"
  ],
  "output_directory": "/tmp/cv_analysis_abc123"
}
```

---

## Пример 2: Анализ PDF с множественными объектами

### Запрос

```bash
curl -X POST "http://127.0.0.1:8000/analyze-document-cv" \
  -F "file=@official_document.pdf" \
  -F "return_annotated=true"
```

### Ответ

```json
{
  "success": true,
  "filename": "official_document.pdf",
  "file_type": "pdf",
  "total_pages": 3,
  "total_detections": 7,
  "summary": {
    "signature": 3,
    "stamp": 3,
    "qr_code": 1
  },
  "pages": [
    {
      "page": 1,
      "detections": [
        {
          "class_id": 1,
          "class_name": "stamp",
          "confidence": 0.94,
          "bbox": [350, 430, 480, 560]
        },
        {
          "class_id": 0,
          "class_name": "signature",
          "confidence": 0.87,
          "bbox": [120, 600, 280, 670]
        }
      ]
    },
    {
      "page": 2,
      "detections": [
        {
          "class_id": 2,
          "class_name": "qr_code",
          "confidence": 0.97,
          "bbox": [50, 50, 150, 150]
        },
        {
          "class_id": 0,
          "class_name": "signature",
          "confidence": 0.85,
          "bbox": [140, 460, 300, 530]
        },
        {
          "class_id": 1,
          "class_name": "stamp",
          "confidence": 0.92,
          "bbox": [360, 440, 490, 570]
        }
      ]
    },
    {
      "page": 3,
      "detections": [
        {
          "class_id": 0,
          "class_name": "signature",
          "confidence": 0.91,
          "bbox": [130, 620, 290, 690]
        },
        {
          "class_id": 1,
          "class_name": "stamp",
          "confidence": 0.96,
          "bbox": [370, 600, 500, 730]
        }
      ]
    }
  ],
  "annotated_images": [
    "official_document_page_1_annotated.png",
    "official_document_page_2_annotated.png",
    "official_document_page_3_annotated.png"
  ],
  "output_directory": "/tmp/cv_analysis_xyz789"
}
```

---

## Пример 3: Анализ без аннотированных изображений

### Запрос

```bash
curl -X POST "http://127.0.0.1:8000/analyze-document-cv" \
  -F "file=@invoice.jpg" \
  -F "return_annotated=false"
```

### Ответ

```json
{
  "success": true,
  "filename": "invoice.jpg",
  "file_type": "image",
  "total_pages": 1,
  "total_detections": 2,
  "summary": {
    "signature": 1,
    "stamp": 1,
    "qr_code": 0
  },
  "pages": [
    {
      "page": 1,
      "detections": [
        {
          "class_id": 0,
          "class_name": "signature",
          "confidence": 0.88,
          "bbox": [145, 480, 295, 545]
        },
        {
          "class_id": 1,
          "class_name": "stamp",
          "confidence": 0.91,
          "bbox": [340, 450, 470, 580]
        }
      ]
    }
  ]
}
```

**Примечание**: `annotated_images` и `output_directory` отсутствуют, т.к. `return_annotated=false`.

---

## Пример 4: Документ без найденных объектов

### Запрос

```bash
curl -X POST "http://127.0.0.1:8000/analyze-document-cv" \
  -F "file=@blank_page.jpg" \
  -F "return_annotated=false"
```

### Ответ

```json
{
  "success": true,
  "filename": "blank_page.jpg",
  "file_type": "image",
  "total_pages": 1,
  "total_detections": 0,
  "summary": {
    "signature": 0,
    "stamp": 0,
    "qr_code": 0
  },
  "pages": [
    {
      "page": 1,
      "detections": []
    }
  ]
}
```

---

## Пример 5: Ошибка - неподдерживаемый формат

### Запрос

```bash
curl -X POST "http://127.0.0.1:8000/analyze-document-cv" \
  -F "file=@document.docx"
```

### Ответ

```json
{
  "detail": "Unsupported file type. Allowed: .png, .jpg, .jpeg, .pdf"
}
```

**HTTP Status**: 400 Bad Request

---

## Структура bbox (Bounding Box)

Формат: `[x1, y1, x2, y2]`

- `x1, y1` - координаты верхнего левого угла
- `x2, y2` - координаты нижнего правого угла
- Единицы: пиксели

### Визуализация

```
(x1, y1) ●─────────┐
         │         │
         │ Object  │
         │         │
         └─────────● (x2, y2)
```

### Вычисление размеров

- Ширина: `width = x2 - x1`
- Высота: `height = y2 - y1`
- Площадь: `area = width * height`

---

## Интерпретация confidence (уверенности)

| Диапазон | Интерпретация | Рекомендация |
|----------|---------------|--------------|
| 0.90 - 1.00 | Очень высокая уверенность | Принять детекцию |
| 0.70 - 0.89 | Высокая уверенность | Скорее всего правильно |
| 0.50 - 0.69 | Средняя уверенность | Требует проверки |
| 0.35 - 0.49 | Низкая уверенность | Рекомендуется проверка |
| < 0.35 | Очень низкая | Отфильтровано |

**Пороги по умолчанию:**

- Signature: 0.35 (принимаются даже нечеткие подписи)
- Stamp: 0.40 (немного выше из-за более четких контуров)
- QR Code: 0.45 (QR коды обычно четкие)

---

## Использование в Python

### Базовый анализ

```python
import requests

def analyze_document(file_path):
    """Анализ документа и вывод статистики"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:8000/analyze-document-cv',
            files={'file': f},
            params={'return_annotated': False}
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Файл: {result['filename']}")
        print(f"Всего объектов: {result['total_detections']}")
        print(f"  Подписей: {result['summary']['signature']}")
        print(f"  Печатей: {result['summary']['stamp']}")
        print(f"  QR кодов: {result['summary']['qr_code']}")
        return result
    else:
        print(f"Ошибка: {response.status_code}")
        return None

# Использование
result = analyze_document('contract.pdf')
```

### Проверка наличия подписи

```python
def has_signature(file_path):
    """Проверить наличие подписи в документе"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:8000/analyze-document-cv',
            files={'file': f},
            params={'return_annotated': False}
        )
    
    if response.status_code == 200:
        result = response.json()
        return result['summary']['signature'] > 0
    return False

# Использование
if has_signature('contract.pdf'):
    print("✓ Документ подписан")
else:
    print("✗ Подпись не найдена")
```

### Получение координат всех объектов

```python
def get_all_detections(file_path):
    """Получить координаты всех найденных объектов"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:8000/analyze-document-cv',
            files={'file': f},
            params={'return_annotated': False}
        )
    
    if response.status_code == 200:
        result = response.json()
        all_detections = []
        
        for page in result['pages']:
            for det in page['detections']:
                all_detections.append({
                    'page': page['page'],
                    'type': det['class_name'],
                    'confidence': det['confidence'],
                    'bbox': det['bbox']
                })
        
        return all_detections
    return []

# Использование
detections = get_all_detections('document.pdf')
for det in detections:
    print(f"Страница {det['page']}: {det['type']} "
          f"({det['confidence']:.2f}) at {det['bbox']}")
```

### Скачивание аннотированных изображений

```python
def download_annotated_images(file_path, output_folder='./results'):
    """Анализ и скачивание аннотированных изображений"""
    import os
    from pathlib import Path
    
    # Создать папку для результатов
    Path(output_folder).mkdir(exist_ok=True)
    
    # Анализ с аннотацией
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:8000/analyze-document-cv',
            files={'file': f},
            params={'return_annotated': True}
        )
    
    if response.status_code == 200:
        result = response.json()
        output_dir = result['output_directory']
        
        # Скачать каждое изображение
        for img_name in result['annotated_images']:
            r = requests.get(
                f'http://127.0.0.1:8000/download-annotated/{img_name}',
                params={'output_dir': output_dir}
            )
            
            if r.status_code == 200:
                save_path = os.path.join(output_folder, img_name)
                with open(save_path, 'wb') as f:
                    f.write(r.content)
                print(f"✓ Сохранено: {save_path}")
        
        # Очистить временные файлы на сервере
        from urllib.parse import quote
        encoded_dir = quote(output_dir, safe='')
        requests.post(f'http://127.0.0.1:8000/cleanup-temp/{encoded_dir}')
        
        return result
    return None

# Использование
result = download_annotated_images('contract.pdf', './my_results')
```

---

## JavaScript/Fetch примеры

### Базовый анализ

```javascript
async function analyzeDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    'http://127.0.0.1:8000/analyze-document-cv?return_annotated=false',
    {
      method: 'POST',
      body: formData
    }
  );
  
  if (response.ok) {
    const result = await response.json();
    console.log(`Найдено объектов: ${result.total_detections}`);
    console.log(`Подписей: ${result.summary.signature}`);
    console.log(`Печатей: ${result.summary.stamp}`);
    console.log(`QR кодов: ${result.summary.qr_code}`);
    return result;
  }
  
  throw new Error(`Analysis failed: ${response.status}`);
}

// Использование с input[type="file"]
const fileInput = document.querySelector('#fileInput');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const result = await analyzeDocument(file);
  displayResults(result);
});
```

### Проверка валидности документа

```javascript
async function validateDocument(file, requiredSignatures = 1, requiredStamps = 1) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    'http://127.0.0.1:8000/analyze-document-cv?return_annotated=false',
    {
      method: 'POST',
      body: formData
    }
  );
  
  if (response.ok) {
    const result = await response.json();
    const hasEnoughSignatures = result.summary.signature >= requiredSignatures;
    const hasEnoughStamps = result.summary.stamp >= requiredStamps;
    
    return {
      valid: hasEnoughSignatures && hasEnoughStamps,
      signatures: result.summary.signature,
      stamps: result.summary.stamp,
      qr_codes: result.summary.qr_code
    };
  }
  
  throw new Error('Validation failed');
}

// Использование
const validation = await validateDocument(file, 2, 1);
if (validation.valid) {
  console.log('✓ Документ валиден');
} else {
  console.log(`✗ Документ невалиден: ${validation.signatures} подписей, ${validation.stamps} печатей`);
}
```

---

## Возможные ошибки

### 400 Bad Request - Неподдерживаемый формат

```json
{
  "detail": "Unsupported file type. Allowed: .png, .jpg, .jpeg, .pdf"
}
```

**Решение**: Проверьте формат файла.

### 400 Bad Request - Отсутствует имя файла

```json
{
  "detail": "Filename is required"
}
```

**Решение**: Убедитесь, что файл правильно загружен.

### 404 Not Found - Аннотация не найдена

```json
{
  "detail": "Annotated image not found"
}
```

**Решение**: Проверьте имя файла и output_dir.

### 500 Internal Server Error - CV pipeline недоступен

```json
{
  "detail": "CV pipeline not available"
}
```

**Решение**: Убедитесь, что `cv_pipeline.py` находится в папке `router/`.

### 500 Internal Server Error - Анализ не удался

```json
{
  "detail": "Analysis failed: <error message>"
}
```

**Решение**: Проверьте логи сервиса для подробностей.

---

## Performance Tips

1. **Используйте return_annotated=false** если аннотации не нужны - это ускорит обработку в 2-3 раза.

2. **Batch processing**: Обрабатывайте несколько файлов параллельно:

```python
import concurrent.futures
import requests

def analyze_file(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:8000/analyze-document-cv',
            files={'file': f},
            params={'return_annotated': False}
        )
    return response.json()

# Параллельная обработка
files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(analyze_file, files))
```

3. **Сжимайте изображения** перед отправкой если они очень большие (>4000x4000px).

4. **Используйте GPU** на сервере для ускорения inference (настраивается в `cv_pipeline.py`).
