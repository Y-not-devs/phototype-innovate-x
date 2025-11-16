#!/usr/bin/env python3
"""
Синхронизация изображений и аннотаций для YOLO датасета
Копирует изображения соответствующие аннотациям в правильные папки
"""

import os
import shutil
from pathlib import Path
from typing import Set, List, Tuple


def get_file_stems(directory: str, extensions: List[str]) -> Set[str]:
    """
    Получить stems (имена без расширений) файлов
    
    Args:
        directory: Папка для поиска
        extensions: Список расширений (напр. ['.jpg', '.png'])
    
    Returns:
        Set имен файлов без расширений
    """
    dir_path = Path(directory)
    stems = set()
    
    if dir_path.exists():
        for ext in extensions:
            stems.update(f.stem for f in dir_path.glob(f'*{ext}'))
    
    return stems


def sync_images_with_labels(
    source_images_dir: str,
    labels_train_dir: str,
    labels_val_dir: str,
    images_train_dir: str,
    images_val_dir: str,
    image_extensions: List[str] = ['.jpg', '.jpeg', '.png']
) -> Tuple[int, int, int]:
    """
    Синхронизировать изображения с аннотациями
    
    Args:
        source_images_dir: Папка с исходными изображениями
        labels_train_dir: Папка с train аннотациями
        labels_val_dir: Папка с val аннотациями
        images_train_dir: Целевая папка для train изображений
        images_val_dir: Целевая папка для val изображений
        image_extensions: Список поддерживаемых расширений
    
    Returns:
        (train_copied, val_copied, not_found)
    """
    # Создать выходные папки
    Path(images_train_dir).mkdir(parents=True, exist_ok=True)
    Path(images_val_dir).mkdir(parents=True, exist_ok=True)
    
    # Получить stems аннотаций
    train_labels = get_file_stems(labels_train_dir, ['.txt'])
    val_labels = get_file_stems(labels_val_dir, ['.txt'])
    
    print(f"📊 Найдено аннотаций:")
    print(f"  Train: {len(train_labels)}")
    print(f"  Val: {len(val_labels)}")
    
    # Получить stems изображений
    source_images = {}
    source_path = Path(source_images_dir)
    
    for ext in image_extensions:
        for img_file in source_path.glob(f'*{ext}'):
            source_images[img_file.stem] = img_file
    
    print(f"\n📂 Найдено изображений: {len(source_images)}")
    
    # Копировать train изображения
    train_copied = 0
    train_not_found = []
    
    print(f"\n📥 Копирование train изображений...")
    for label_stem in train_labels:
        if label_stem in source_images:
            src = source_images[label_stem]
            dst = Path(images_train_dir) / src.name
            
            # Пропустить если файл уже в целевой папке
            if src.resolve() != dst.resolve():
                shutil.copy(src, dst)
            
            train_copied += 1
            print(f"  ✓ {src.name}")
        else:
            train_not_found.append(label_stem)
            print(f"  ✗ {label_stem} - изображение не найдено")
    
    # Копировать val изображения
    val_copied = 0
    val_not_found = []
    
    print(f"\n📥 Копирование val изображений...")
    for label_stem in val_labels:
        if label_stem in source_images:
            src = source_images[label_stem]
            dst = Path(images_val_dir) / src.name
            
            # Пропустить если файл уже в целевой папке
            if src.resolve() != dst.resolve():
                shutil.copy(src, dst)
            
            val_copied += 1
            print(f"  ✓ {src.name}")
        else:
            val_not_found.append(label_stem)
            print(f"  ✗ {label_stem} - изображение не найдено")
    
    not_found = len(train_not_found) + len(val_not_found)
    
    return train_copied, val_copied, not_found


def check_dataset_consistency(
    images_train_dir: str,
    images_val_dir: str,
    labels_train_dir: str,
    labels_val_dir: str
):
    """
    Проверить соответствие изображений и аннотаций
    
    Args:
        images_train_dir: Папка train изображений
        images_val_dir: Папка val изображений
        labels_train_dir: Папка train аннотаций
        labels_val_dir: Папка val аннотаций
    """
    print("\n" + "="*70)
    print("🔍 Проверка целостности датасета")
    print("="*70)
    
    for split, images_dir, labels_dir in [
        ("TRAIN", images_train_dir, labels_train_dir),
        ("VAL", images_val_dir, labels_val_dir)
    ]:
        images = get_file_stems(images_dir, ['.jpg', '.jpeg', '.png'])
        labels = get_file_stems(labels_dir, ['.txt'])
        
        print(f"\n{split}:")
        print(f"  Изображений: {len(images)}")
        print(f"  Аннотаций: {len(labels)}")
        
        # Проверить соответствие
        missing_labels = images - labels
        missing_images = labels - images
        
        if missing_labels:
            print(f"  ⚠️  Нет аннотаций для {len(missing_labels)} изображений:")
            for stem in list(missing_labels)[:5]:
                print(f"    - {stem}")
            if len(missing_labels) > 5:
                print(f"    ... и еще {len(missing_labels) - 5}")
        
        if missing_images:
            print(f"  ⚠️  Нет изображений для {len(missing_images)} аннотаций:")
            for stem in list(missing_images)[:5]:
                print(f"    - {stem}")
            if len(missing_images) > 5:
                print(f"    ... и еще {len(missing_images) - 5}")
        
        if not missing_labels and not missing_images:
            print(f"  ✓ Все файлы соответствуют!")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Синхронизация изображений и аннотаций'
    )
    
    parser.add_argument(
        '--source-images',
        type=str,
        default='dataset/images/train',
        help='Папка с исходными изображениями'
    )
    
    parser.add_argument(
        '--labels-train',
        type=str,
        default='dataset/labels/train',
        help='Папка с train аннотациями'
    )
    
    parser.add_argument(
        '--labels-val',
        type=str,
        default='dataset/labels/val',
        help='Папка с val аннотациями'
    )
    
    parser.add_argument(
        '--images-train',
        type=str,
        default='dataset/images/train',
        help='Целевая папка для train изображений'
    )
    
    parser.add_argument(
        '--images-val',
        type=str,
        default='dataset/images/val',
        help='Целевая папка для val изображений'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Синхронизация изображений и аннотаций")
    print("=" * 70)
    
    # Синхронизировать
    train_copied, val_copied, not_found = sync_images_with_labels(
        source_images_dir=args.source_images,
        labels_train_dir=args.labels_train,
        labels_val_dir=args.labels_val,
        images_train_dir=args.images_train,
        images_val_dir=args.images_val
    )
    
    # Статистика
    print("\n" + "=" * 70)
    print("📊 Результаты синхронизации")
    print("=" * 70)
    print(f"Train изображений скопировано: {train_copied}")
    print(f"Val изображений скопировано: {val_copied}")
    print(f"Не найдено изображений: {not_found}")
    
    # Проверить целостность
    check_dataset_consistency(
        images_train_dir=args.images_train,
        images_val_dir=args.images_val,
        labels_train_dir=args.labels_train,
        labels_val_dir=args.labels_val
    )
    
    print("\n" + "=" * 70)
    print("✓ Датасет готов к обучению!")
    print("=" * 70)
    print("\nСледующий шаг:")
    print("  python train_model.py")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        print("=" * 70)
        print("Синхронизация изображений и аннотаций для YOLO")
        print("=" * 70)
        print("\n📋 Использование:")
        print("  python sync_dataset.py [options]")
        print("\n💡 Пример:")
        print("  python sync_dataset.py")
        print("\n📊 Опции:")
        print("  --source-images DIR   Папка с исходными изображениями")
        print("  --labels-train DIR    Папка с train аннотациями")
        print("  --labels-val DIR      Папка с val аннотациями")
        print("  --images-train DIR    Целевая папка train")
        print("  --images-val DIR      Целевая папка val")
        print("\n🎯 Что делает скрипт:")
        print("  1. Находит все аннотации (.txt) в train и val")
        print("  2. Копирует соответствующие изображения")
        print("  3. Проверяет целостность датасета")
        print("\n" + "=" * 70)
        sys.exit(0)
    
    main()
