# Быстрый старт: Обучение модели для детекции

## 📦 Что уже готово

✅ CV pipeline (`router/cv_pipeline.py`)  
✅ API endpoints (`router/router-service/app/main.py`)  
✅ Тестовый скрипт (`router/test_cv_endpoint.py`)  
✅ Структура датасета (`dataset/`)  
✅ Скрипт обучения (`train_model.py`)  
✅ Конвертер PDF (`convert_pdfs.py`)

## 🎯 Процесс подготовки датасета

### Шаг 1: Собрать PDF документы

Скопируйте ваши PDF файлы с печатями, подписями и QR-кодами:

```powershell
# Создайте папку для ваших PDF
New-Item -ItemType Directory -Path "dataset\raw_pdfs\train" -Force
New-Item -ItemType Directory -Path "dataset\raw_pdfs\val" -Force

# Скопируйте ваши документы
# 80% в train, 20% в val
Copy-Item "путь\к\вашим\документам\*.pdf" "dataset\raw_pdfs\train\"
```

**Где взять документы:**

- Сканы официальных документов вашей организации
- Контракты, акты, накладные с печатями и подписями
- Документы с QR-кодами
- Минимум: 300 документов (240 train + 60 val)
- Оптимально: 1000+ документов (800 train + 200 val)

### Шаг 2: Конвертировать PDF в изображения

```powershell
# Конвертация train набора
python convert_pdfs.py dataset\raw_pdfs\train dataset\images\train

# Конвертация val набора
python convert_pdfs.py dataset\raw_pdfs\val dataset\images\val
```

Это создаст JPG изображения с разрешением 300 DPI.

### Шаг 3: Разметить данные (самый важный шаг!)

#### Установить LabelImg

```powershell
pip install labelImg
```

#### Запустить разметку

```powershell
# Разметить train набор
labelImg dataset\images\train dataset\labels\train
```

#### Инструкция по работе с LabelImg

1. **Настройте LabelImg:**
   - View → Auto Save mode (включить)
   - PascalVOC → переключить на **YOLO**
   - File → Change Save Dir → выбрать `dataset\labels\train`

2. **Создайте классы:**
   - Создайте файл `dataset\classes.txt`:

     ```text
     signature
     stamp
     qr_code
     ```

   - В LabelImg: меню слева появятся классы

3. **Разметка:**
   - Нажмите `W` для создания bbox
   - Выделите подпись/печать/QR-код прямоугольником
   - Выберите класс из списка
   - Файл сохранится автоматически
   - `D` - следующее изображение
   - `A` - предыдущее изображение

4. **Советы:**
   - Bbox должен плотно обводить объект
   - Если объект частично за краем - пропустите
   - Размытые/нечеткие объекты можно пропустить
   - Размечайте последовательно, не торопитесь

5. **Повторить для val:**

   ```powershell
   labelImg dataset\images\val dataset\labels\val
   ```

### Шаг 4: Проверить датасет

```powershell
# Проверить количество файлов
$trainImages = (Get-ChildItem dataset\images\train -File).Count
$trainLabels = (Get-ChildItem dataset\labels\train -File).Count
$valImages = (Get-ChildItem dataset\images\val -File).Count
$valLabels = (Get-ChildItem dataset\labels\val -File).Count

Write-Host "Train: $trainImages изображений, $trainLabels аннотаций"
Write-Host "Val: $valImages изображений, $valLabels аннотаций"

if ($trainImages -eq $trainLabels) {
    Write-Host "✓ Train набор OK"
} else {
    Write-Host "✗ Train набор: несоответствие файлов!"
}

if ($valImages -eq $valLabels) {
    Write-Host "✓ Val набор OK"
} else {
    Write-Host "✗ Val набор: несоответствие файлов!"
}
```

### Шаг 5: Обучить модель

```powershell
# Базовое обучение (nano модель, CPU, 100 эпох)
python train_model.py

# Или с GPU (если есть CUDA)
python train_model.py --device cuda --epochs 200

# Или более крупная модель для лучшей точности
python train_model.py --model m --epochs 200
```

**Время обучения:**

- CPU: 2-4 часа (100 epochs, 1000 изображений)
- GPU: 20-40 минут

**Мониторинг:**

- Откройте `runs/detect/document_detector/results.png`
- Следите за mAP (mean Average Precision)
- Обучение остановится автоматически если нет улучшений 20 эпох

### Шаг 6: Использовать обученную модель

После обучения модель сохранится в `runs/detect/document_detector/weights/best.pt`.

**Обновить router-service:**

```python
# В router/router-service/app/main.py
# Строка ~301, измените model_path:

pipeline = DocumentAnalysisPipeline(
    model_path='runs/detect/document_detector/weights/best.pt',  # Ваша модель!
    use_gpu=False  # True если используете GPU
)
```

**Перезапустить сервисы:**

```powershell
cd router
python run.py
```

**Тестировать:**

```powershell
python router\test_cv_endpoint.py test_document.pdf
```

## 📊 Минимальные требования

| Параметр | Минимум | Оптимально |
|----------|---------|------------|
| Train изображений | 300 | 1000+ |
| Val изображений | 75 | 250+ |
| Примеров signature | 100 | 300+ |
| Примеров stamp | 100 | 300+ |
| Примеров qr_code | 100 | 300+ |
| Epochs | 50 | 100-200 |
| Разрешение | 640x640 | 1024x1024+ |

## 🎓 Модели YOLO

```powershell
# yolov8n.pt - Nano (самая быстрая, средняя точность)
python train_model.py --model n

# yolov8s.pt - Small (баланс)
python train_model.py --model s

# yolov8m.pt - Medium (лучше точность, медленнее)
python train_model.py --model m --device cuda

# yolov8l.pt - Large (требует GPU)
python train_model.py --model l --device cuda --epochs 200

# yolov8x.pt - XLarge (максимальная точность, только GPU)
python train_model.py --model x --device cuda --epochs 300
```

## 🐛 Частые проблемы

### "No labels found"

```powershell
# Проверьте что файлы существуют
Get-ChildItem dataset\labels\train
Get-ChildItem dataset\labels\val

# Имена должны совпадать с изображениями
# doc_001.jpg → doc_001.txt
```

### "Invalid YOLO format"

Откройте .txt файл, проверьте формат:

```text
0 0.5 0.7 0.15 0.1
1 0.3 0.8 0.12 0.12
```

Должно быть 5 чисел через пробел, все в диапазоне 0-1.

### "Out of memory"

```powershell
# Уменьшите batch size
python train_model.py --batch 8

# Или используйте меньшую модель
python train_model.py --model n --batch 8
```

### "Poppler not found" при конвертации PDF

**Windows:**

1. Скачать poppler: <https://github.com/oschwartz10612/poppler-windows/releases>
2. Распаковать в `C:\poppler`
3. Добавить в PATH: `C:\poppler\Library\bin`

### Низкая точность (mAP < 0.5)

1. Соберите больше данных (1000+)
2. Проверьте качество разметки
3. Увеличьте epochs (200-300)
4. Используйте более крупную модель (yolov8m)
5. Добавьте разнообразия в датасет

## 📝 Checklist подготовки

- [ ] Собрано минимум 300 документов (PDF/изображения)
- [ ] Документы разделены на train (80%) и val (20%)
- [ ] PDF конвертированы в JPG (300 DPI)
- [ ] Данные размечены в LabelImg (формат YOLO)
- [ ] Количество изображений = количество аннотаций
- [ ] Файл `dataset/dataset.yaml` существует
- [ ] Установлен ultralytics (`pip install ultralytics`)
- [ ] Запущено обучение (`python train_model.py`)
- [ ] Модель обучена (best.pt создан)
- [ ] Путь к модели обновлен в router-service
- [ ] Сервисы перезапущены
- [ ] Тестирование выполнено

## 🚀 Резюме команд

```powershell
# 1. Подготовка
pip install labelImg ultralytics pdf2image pillow

# 2. Конвертация PDF
python convert_pdfs.py dataset\raw_pdfs\train dataset\images\train
python convert_pdfs.py dataset\raw_pdfs\val dataset\images\val

# 3. Разметка
labelImg dataset\images\train dataset\labels\train

# 4. Обучение
python train_model.py

# 5. Использование
cd router
python run.py
# В другом терминале:
python router\test_cv_endpoint.py test.pdf
```

## 📞 Поддержка

- **Полная инструкция**: `DATASET_GUIDE.md`
- **О датасете**: `dataset/README.md`
- **CV технология**: `router/CV_TECHNOLOGY.md`
- **API примеры**: `router/API_EXAMPLES.md`

---

**Следующий шаг**: Соберите ваши PDF документы и начните с Шага 1! 🚀
