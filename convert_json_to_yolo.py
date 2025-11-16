#!/usr/bin/env python3
"""
Конвертер аннотаций из кастомного JSON формата в YOLO формат

Конвертирует selected_annotations.json в текстовые файлы .txt для YOLO обучения
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import shutil


# Маппинг категорий в YOLO class_id
CATEGORY_MAPPING = {
    "signature": 0,
    "stamp": 1,
    "qr": 2
}


def bbox_to_yolo_format(
    bbox: Dict[str, float],
    page_width: int,
    page_height: int
) -> Tuple[float, float, float, float]:
    """
    Конвертировать bbox из абсолютных координат в YOLO формат (нормализованный)
    
    Args:
        bbox: {"x": x, "y": y, "width": w, "height": h}
        page_width: Ширина страницы
        page_height: Высота страницы
    
    Returns:
        (center_x, center_y, width, height) - все нормализованы 0-1
    """
    x = bbox["x"]
    y = bbox["y"]
    width = bbox["width"]
    height = bbox["height"]
    
    # Вычислить центр bbox
    center_x = x + width / 2
    center_y = y + height / 2
    
    # Нормализовать координаты (0-1)
    norm_center_x = center_x / page_width
    norm_center_y = center_y / page_height
    norm_width = width / page_width
    norm_height = height / page_height
    
    # Проверить границы
    norm_center_x = max(0, min(1, norm_center_x))
    norm_center_y = max(0, min(1, norm_center_y))
    norm_width = max(0, min(1, norm_width))
    norm_height = max(0, min(1, norm_height))
    
    return norm_center_x, norm_center_y, norm_width, norm_height


def convert_annotations_to_yolo(
    json_path: str,
    output_labels_dir: str,
    pdf_images_mapping: Dict[str, List[str]] = None
) -> Dict[str, int]:
    """
    Конвертировать JSON аннотации в YOLO формат
    
    Args:
        json_path: Путь к JSON файлу с аннотациями
        output_labels_dir: Папка для сохранения .txt файлов
        pdf_images_mapping: Маппинг PDF → список путей к изображениям страниц
    
    Returns:
        Статистика конвертации
    """
    # Загрузить JSON
    print(f"📂 Загрузка аннотаций из: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Создать выходную папку
    output_path = Path(output_labels_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "signature": 0,
        "stamp": 0,
        "qr": 0,
        "total_pages": 0,
        "total_annotations": 0,
        "skipped_pages": 0
    }
    
    # Обработать каждый PDF документ
    for pdf_name, pdf_data in data.items():
        print(f"\n📄 Обработка: {pdf_name}")
        
        # Обработать каждую страницу
        for page_key, page_data in pdf_data.items():
            if not isinstance(page_data, dict) or 'annotations' not in page_data:
                continue
            
            # Извлечь номер страницы
            page_num = page_key.split('_')[-1]
            
            # Определить имя файла изображения
            # Формат: document_page_1.jpg
            pdf_stem = Path(pdf_name).stem
            image_name = f"{pdf_stem}_page_{page_num}"
            
            # Получить размеры страницы
            page_size = page_data.get('page_size', {})
            page_width = page_size.get('width', 1684)  # Default размер
            page_height = page_size.get('height', 1190)
            
            # Получить аннотации
            annotations = page_data.get('annotations', [])
            
            if not annotations:
                # Страница без аннотаций
                stats["skipped_pages"] += 1
                continue
            
            # Создать YOLO аннотацию
            yolo_annotations = []
            
            for ann_dict in annotations:
                # Получить данные аннотации
                ann_key = list(ann_dict.keys())[0]
                ann_data = ann_dict[ann_key]
                
                category = ann_data.get('category')
                bbox = ann_data.get('bbox')
                
                if not category or not bbox:
                    continue
                
                # Пропустить неизвестные категории
                if category not in CATEGORY_MAPPING:
                    print(f"  ⚠️  Неизвестная категория: {category}")
                    continue
                
                # Получить class_id
                class_id = CATEGORY_MAPPING[category]
                
                # Конвертировать bbox в YOLO формат
                center_x, center_y, width, height = bbox_to_yolo_format(
                    bbox, page_width, page_height
                )
                
                # Создать строку YOLO
                yolo_line = f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}"
                yolo_annotations.append(yolo_line)
                
                # Обновить статистику
                stats[category] += 1
                stats["total_annotations"] += 1
            
            # Сохранить YOLO аннотацию
            if yolo_annotations:
                output_file = output_path / f"{image_name}.txt"
                with open(output_file, 'w') as f:
                    f.write('\n'.join(yolo_annotations))
                
                print(f"  ✓ {image_name}.txt - {len(yolo_annotations)} объектов")
                stats["total_pages"] += 1
            else:
                stats["skipped_pages"] += 1
    
    return stats


def split_train_val(
    labels_dir: str,
    train_labels_dir: str,
    val_labels_dir: str,
    train_ratio: float = 0.8
):
    """
    Разделить аннотации на train и val
    
    Args:
        labels_dir: Папка со всеми аннотациями
        train_labels_dir: Папка для train аннотаций
        val_labels_dir: Папка для val аннотаций
        train_ratio: Процент train данных (0-1)
    """
    import random
    
    labels_path = Path(labels_dir)
    train_path = Path(train_labels_dir)
    val_path = Path(val_labels_dir)
    
    train_path.mkdir(parents=True, exist_ok=True)
    val_path.mkdir(parents=True, exist_ok=True)
    
    # Получить все .txt файлы
    all_labels = list(labels_path.glob("*.txt"))
    
    if not all_labels:
        print("⚠️  Нет .txt файлов для разделения")
        return
    
    # Перемешать
    random.shuffle(all_labels)
    
    # Разделить
    split_idx = int(len(all_labels) * train_ratio)
    train_labels = all_labels[:split_idx]
    val_labels = all_labels[split_idx:]
    
    print(f"\n📊 Разделение на train/val:")
    print(f"  Train: {len(train_labels)} файлов")
    print(f"  Val: {len(val_labels)} файлов")
    
    # Копировать файлы
    for label_file in train_labels:
        shutil.copy(label_file, train_path / label_file.name)
    
    for label_file in val_labels:
        shutil.copy(label_file, val_path / label_file.name)
    
    print(f"  ✓ Файлы скопированы")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Конвертировать JSON аннотации в YOLO формат'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        default='dataset/selected_annotations.json',
        help='Путь к JSON файлу с аннотациями'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='dataset/labels_converted',
        help='Папка для сохранения YOLO аннотаций'
    )
    
    parser.add_argument(
        '--split',
        action='store_true',
        help='Разделить на train/val после конвертации'
    )
    
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.8,
        help='Процент train данных (по умолчанию 0.8)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Конвертация JSON аннотаций в YOLO формат")
    print("=" * 70)
    
    # Конвертировать
    stats = convert_annotations_to_yolo(
        json_path=args.json,
        output_labels_dir=args.output
    )
    
    # Вывести статистику
    print("\n" + "=" * 70)
    print("📊 Статистика конвертации:")
    print("=" * 70)
    print(f"Всего страниц обработано: {stats['total_pages']}")
    print(f"Всего аннотаций: {stats['total_annotations']}")
    print(f"\nПо категориям:")
    print(f"  Подписи (signature): {stats['signature']}")
    print(f"  Печати (stamp): {stats['stamp']}")
    print(f"  QR-коды (qr): {stats['qr']}")
    print(f"\nПропущено страниц: {stats['skipped_pages']}")
    print(f"\n✓ Аннотации сохранены в: {args.output}")
    
    # Разделить на train/val если нужно
    if args.split:
        print("\n" + "=" * 70)
        print("Разделение на train/val")
        print("=" * 70)
        
        split_train_val(
            labels_dir=args.output,
            train_labels_dir='dataset/labels/train',
            val_labels_dir='dataset/labels/val',
            train_ratio=args.train_ratio
        )
        
        print(f"\n✓ Train аннотации: dataset/labels/train/")
        print(f"✓ Val аннотации: dataset/labels/val/")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        print("=" * 70)
        print("Конвертация JSON аннотаций в YOLO формат")
        print("=" * 70)
        print("\n📋 Использование:")
        print("  python convert_json_to_yolo.py [options]")
        print("\n💡 Примеры:")
        print("\n  # Базовая конвертация")
        print("  python convert_json_to_yolo.py")
        print("\n  # Конвертация и разделение на train/val")
        print("  python convert_json_to_yolo.py --split")
        print("\n  # С кастомным соотношением train/val (70/30)")
        print("  python convert_json_to_yolo.py --split --train-ratio 0.7")
        print("\n📊 Опции:")
        print("  --json PATH         Путь к JSON (по умолчанию dataset/selected_annotations.json)")
        print("  --output DIR        Папка для вывода (по умолчанию dataset/labels_converted)")
        print("  --split             Разделить на train/val")
        print("  --train-ratio N     Процент train (по умолчанию 0.8)")
        print("\n🎯 Формат YOLO:")
        print("  class_id center_x center_y width height")
        print("  Все координаты нормализованы (0-1)")
        print("\n📦 Классы:")
        print("  0: signature (подписи)")
        print("  1: stamp (печати)")
        print("  2: qr (QR-коды)")
        print("\n" + "=" * 70)
        sys.exit(0)
    
    main()
