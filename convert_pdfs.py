#!/usr/bin/env python3
"""
Скрипт для конвертации PDF файлов в изображения для датасета YOLO
"""

import os
import sys
from pathlib import Path
from pdf2image import convert_from_path
import argparse


def convert_pdfs_to_images(
    input_folder: str,
    output_folder: str,
    dpi: int = 300,
    format: str = 'JPEG',
    quality: int = 95
):
    """
    Конвертировать все PDF файлы в папке в изображения
    
    Args:
        input_folder: Папка с PDF файлами
        output_folder: Папка для сохранения изображений
        dpi: Разрешение (300 рекомендуется для документов)
        format: Формат выходных файлов (JPEG или PNG)
        quality: Качество JPEG (1-100, используется только для JPEG)
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Проверить существование входной папки
    if not input_path.exists():
        print(f"❌ Ошибка: Папка {input_folder} не найдена!")
        return
    
    # Создать выходную папку
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Найти все PDF файлы
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  В папке {input_folder} не найдено PDF файлов")
        return
    
    print(f"📁 Найдено PDF файлов: {len(pdf_files)}")
    print(f"📤 Конвертация в {format} с DPI={dpi}")
    print(f"💾 Сохранение в: {output_folder}\n")
    
    total_pages = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
        
        try:
            # Конвертировать PDF в изображения
            images = convert_from_path(
                str(pdf_file),
                dpi=dpi,
                fmt=format.lower()
            )
            
            # Сохранить каждую страницу
            base_name = pdf_file.stem
            
            for page_num, image in enumerate(images, 1):
                if len(images) == 1:
                    # Если одна страница, не добавляем номер
                    output_name = f"{base_name}.jpg"
                else:
                    # Если несколько страниц, добавляем номер
                    output_name = f"{base_name}_page_{page_num}.jpg"
                
                output_file = output_path / output_name
                
                # Сохранить изображение
                if format.upper() == 'JPEG':
                    image.save(output_file, 'JPEG', quality=quality)
                else:
                    image.save(output_file, format.upper())
                
                total_pages += 1
                print(f"  ✓ {output_name}")
        
        except Exception as e:
            print(f"  ❌ Ошибка при конвертации {pdf_file.name}: {str(e)}")
            continue
    
    print(f"\n✅ Конвертация завершена!")
    print(f"📊 Обработано PDF файлов: {len(pdf_files)}")
    print(f"📄 Создано изображений: {total_pages}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Конвертация PDF файлов в изображения для YOLO датасета'
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Папка с PDF файлами'
    )
    
    parser.add_argument(
        'output',
        type=str,
        help='Папка для сохранения изображений'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Разрешение DPI (по умолчанию 300)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['JPEG', 'PNG'],
        default='JPEG',
        help='Формат выходных файлов (по умолчанию JPEG)'
    )
    
    parser.add_argument(
        '--quality',
        type=int,
        default=95,
        help='Качество JPEG 1-100 (по умолчанию 95)'
    )
    
    args = parser.parse_args()
    
    convert_pdfs_to_images(
        input_folder=args.input,
        output_folder=args.output,
        dpi=args.dpi,
        format=args.format,
        quality=args.quality
    )


if __name__ == "__main__":
    # Примеры использования если запущен без аргументов
    if len(sys.argv) == 1:
        print("=" * 60)
        print("Конвертация PDF в изображения для YOLO датасета")
        print("=" * 60)
        print("\nИспользование:")
        print("  python convert_pdfs.py <input_folder> <output_folder> [options]")
        print("\nПримеры:")
        print("  # Базовая конвертация")
        print("  python convert_pdfs.py dataset/raw_pdfs/train dataset/images/train")
        print()
        print("  # С настройками DPI и качества")
        print("  python convert_pdfs.py dataset/raw_pdfs/train dataset/images/train --dpi 400 --quality 100")
        print()
        print("  # В формат PNG")
        print("  python convert_pdfs.py dataset/raw_pdfs/train dataset/images/train --format PNG")
        print("\nОпции:")
        print("  --dpi N         Разрешение (по умолчанию 300)")
        print("  --format FMT    Формат: JPEG или PNG (по умолчанию JPEG)")
        print("  --quality N     Качество JPEG 1-100 (по умолчанию 95)")
        print("\n" + "=" * 60)
        sys.exit(0)
    
    main()
