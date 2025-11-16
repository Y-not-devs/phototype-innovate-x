#!/usr/bin/env python3
"""
Скрипт обучения YOLO модели для детекции печатей, подписей и QR-кодов
"""

import argparse
from pathlib import Path
from ultralytics import YOLO  # type: ignore


def train_model(
    model_size: str = 'n',
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = 'cpu',
    patience: int = 20,
    name: str = 'document_detector'
):
    """
    Обучить YOLO модель на датасете
    
    Args:
        model_size: Размер модели (n/s/m/l/x)
        epochs: Количество эпох
        batch: Размер batch
        imgsz: Размер входного изображения
        device: Устройство (cpu/cuda/0/1/...)
        patience: Early stopping patience
        name: Имя эксперимента
    """
    # Путь к конфигурации датасета
    dataset_yaml = Path('dataset/dataset.yaml')
    
    if not dataset_yaml.exists():
        print(f"❌ Ошибка: Файл {dataset_yaml} не найден!")
        print("Создайте файл dataset/dataset.yaml согласно инструкции")
        return
    
    print("=" * 70)
    print("🚀 Обучение YOLO модели для детекции документов")
    print("=" * 70)
    print(f"📦 Модель: YOLOv8{model_size}")
    print(f"📊 Датасет: {dataset_yaml}")
    print(f"🔄 Эпох: {epochs}")
    print(f"📦 Batch size: {batch}")
    print(f"📐 Размер изображения: {imgsz}x{imgsz}")
    print(f"💻 Устройство: {device}")
    print(f"⏱️  Patience: {patience}")
    print("=" * 70)
    print()
    
    # Загрузить предобученную модель
    model_weights = f'yolov8{model_size}.pt'
    print(f"📥 Загрузка предобученной модели: {model_weights}")
    
    try:
        model = YOLO(model_weights)
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {str(e)}")
        print("Убедитесь что ultralytics установлен: pip install ultralytics")
        return
    
    print("✓ Модель загружена\n")
    
    # Обучение
    print("🎓 Начало обучения...\n")
    
    try:
        results = model.train(
            # Основные параметры
            data=str(dataset_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            
            # Сохранение
            project='runs/detect',
            name=name,
            exist_ok=True,
            
            # Early stopping
            patience=patience,
            
            # Оптимизация
            optimizer='AdamW',
            lr0=0.01,
            lrf=0.01,
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3.0,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            
            # Аугментации (data augmentation)
            degrees=5.0,        # Поворот ±5 градусов
            translate=0.1,      # Сдвиг 10%
            scale=0.2,          # Масштабирование ±20%
            shear=2.0,          # Shear ±2 градуса
            perspective=0.0,    # Perspective transform (0 = отключено)
            flipud=0.0,         # Не переворачивать вверх-вниз (документы обычно правильно ориентированы)
            fliplr=0.5,         # Переворачивать влево-вправо 50%
            mosaic=1.0,         # Mosaic augmentation
            mixup=0.0,          # Mixup augmentation (0 = отключено)
            
            # Валидация
            val=True,
            plots=True,
            save=True,
            save_period=-1,
            
            # Логирование
            verbose=True,
        )
        
        print("\n" + "=" * 70)
        print("✅ Обучение завершено успешно!")
        print("=" * 70)
        print(f"\n📊 Результаты сохранены в: runs/detect/{name}/")
        print(f"🏆 Лучшая модель: runs/detect/{name}/weights/best.pt")
        print(f"📈 Последняя модель: runs/detect/{name}/weights/last.pt")
        print(f"\n📉 Графики обучения:")
        print(f"  • runs/detect/{name}/results.png")
        print(f"  • runs/detect/{name}/confusion_matrix.png")
        print(f"  • runs/detect/{name}/F1_curve.png")
        print(f"  • runs/detect/{name}/P_curve.png")
        print(f"  • runs/detect/{name}/R_curve.png")
        print(f"\n🧪 Тестирование модели:")
        print(f"  python -c \"from ultralytics import YOLO; model = YOLO('runs/detect/{name}/weights/best.pt'); model.val()\"")
        print(f"\n🚀 Использование в cv_pipeline:")
        print(f"  pipeline = DocumentAnalysisPipeline(")
        print(f"      model_path='runs/detect/{name}/weights/best.pt',")
        print(f"      use_gpu={'True' if device != 'cpu' else 'False'}")
        print(f"  )")
        
    except KeyboardInterrupt:
        print("\n⚠️  Обучение прервано пользователем")
        print(f"Последняя модель сохранена в: runs/detect/{name}/weights/last.pt")
    
    except Exception as e:
        print(f"\n❌ Ошибка во время обучения: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Обучение YOLO модели для детекции печатей, подписей и QR-кодов'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=['n', 's', 'm', 'l', 'x'],
        default='n',
        help='Размер модели: n (nano), s (small), m (medium), l (large), x (xlarge). По умолчанию: n'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Количество эпох обучения (по умолчанию 100)'
    )
    
    parser.add_argument(
        '--batch',
        type=int,
        default=16,
        help='Размер batch (по умолчанию 16, уменьшите если не хватает памяти)'
    )
    
    parser.add_argument(
        '--imgsz',
        type=int,
        default=640,
        help='Размер входного изображения (по умолчанию 640)'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Устройство: cpu, cuda, 0, 1, ... (по умолчанию cpu)'
    )
    
    parser.add_argument(
        '--patience',
        type=int,
        default=20,
        help='Early stopping patience (по умолчанию 20)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default='document_detector',
        help='Имя эксперимента (по умолчанию document_detector)'
    )
    
    args = parser.parse_args()
    
    train_model(
        model_size=args.model,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        patience=args.patience,
        name=args.name
    )


if __name__ == "__main__":
    import sys
    
    # Показать помощь если запущен без аргументов
    if len(sys.argv) == 1:
        print("=" * 70)
        print("Обучение YOLO модели для детекции документов")
        print("=" * 70)
        print("\n🎯 Классы детекции:")
        print("  0: signature (подписи)")
        print("  1: stamp (печати)")
        print("  2: qr_code (QR-коды)")
        print("\n📋 Использование:")
        print("  python train_model.py [options]")
        print("\n💡 Примеры:")
        print("\n  # Базовое обучение (nano модель, CPU, 100 эпох)")
        print("  python train_model.py")
        print("\n  # Обучение на GPU с большей моделью")
        print("  python train_model.py --model m --device cuda --epochs 200")
        print("\n  # Быстрое тестирование (10 эпох)")
        print("  python train_model.py --epochs 10 --batch 8")
        print("\n  # Продолжить обучение с другим именем")
        print("  python train_model.py --name document_detector_v2 --epochs 150")
        print("\n📊 Опции:")
        print("  --model {n,s,m,l,x}  Размер модели (по умолчанию n)")
        print("  --epochs N           Количество эпох (по умолчанию 100)")
        print("  --batch N            Размер batch (по умолчанию 16)")
        print("  --imgsz N            Размер изображения (по умолчанию 640)")
        print("  --device DEV         Устройство: cpu/cuda (по умолчанию cpu)")
        print("  --patience N         Early stopping (по умолчанию 20)")
        print("  --name NAME          Имя эксперимента")
        print("\n💻 Размеры моделей:")
        print("  n (nano)   - Самая быстрая, точность средняя")
        print("  s (small)  - Баланс скорости и точности")
        print("  m (medium) - Лучше точность, медленнее")
        print("  l (large)  - Высокая точность, требует GPU")
        print("  x (xlarge) - Максимальная точность, только GPU")
        print("\n⚠️  Перед обучением убедитесь:")
        print("  ✓ Датасет подготовлен в dataset/images/")
        print("  ✓ Разметка готова в dataset/labels/")
        print("  ✓ Файл dataset/dataset.yaml существует")
        print("  ✓ Установлен ultralytics: pip install ultralytics")
        print("\n" + "=" * 70)
        sys.exit(0)
    
    main()
