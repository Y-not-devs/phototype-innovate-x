#!/usr/bin/env python3
"""
Test script for CV document analysis endpoint

This script demonstrates how to use the /analyze-document-cv endpoint
to detect stamps, signatures, and QR codes in documents.
"""

import requests
import json
import sys
from pathlib import Path


def test_cv_analysis(file_path: str, return_annotated: bool = True):
    """
    Test CV analysis endpoint with a document file
    
    Args:
        file_path: Path to image or PDF file
        return_annotated: Whether to request annotated images
    """
    # API endpoint
    url = "http://127.0.0.1:8000/analyze-document-cv"
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return None
    
    print(f"\n{'='*60}")
    print(f"Testing CV Analysis")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    print(f"Return annotated: {return_annotated}")
    print(f"{'='*60}\n")
    
    try:
        # Prepare file for upload
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            params = {'return_annotated': return_annotated}
            
            print("Sending request...")
            response = requests.post(url, files=files, params=params)
        
        # Check response status
        if response.status_code == 200:
            result = response.json()
            
            print("✓ Analysis successful!\n")
            print(f"File type: {result['file_type']}")
            print(f"Total pages: {result['total_pages']}")
            print(f"Total detections: {result['total_detections']}")
            
            print("\n" + "-"*60)
            print("Detection Summary:")
            print("-"*60)
            summary = result['summary']
            print(f"Signatures: {summary['signature']}")
            print(f"Stamps: {summary['stamp']}")
            print(f"QR Codes: {summary['qr_code']}")
            
            print("\n" + "-"*60)
            print("Page-by-Page Results:")
            print("-"*60)
            
            for page_result in result['pages']:
                page_num = page_result['page']
                detections = page_result['detections']
                print(f"\nPage {page_num}: {len(detections)} objects detected")
                
                for i, det in enumerate(detections, 1):
                    print(f"  {i}. {det['class_name']} "
                          f"(confidence: {det['confidence']:.2f})")
                    print(f"     Bbox: [{det['bbox'][0]:.0f}, {det['bbox'][1]:.0f}, "
                          f"{det['bbox'][2]:.0f}, {det['bbox'][3]:.0f}]")
            
            # Display annotated image info
            if return_annotated and result.get('annotated_images'):
                print("\n" + "-"*60)
                print("Annotated Images:")
                print("-"*60)
                for img_path in result['annotated_images']:
                    print(f"  • {img_path}")
                print(f"\nOutput directory: {result['output_directory']}")
                print("\nNote: Download annotated images using:")
                print(f"  GET /download-annotated/{{filename}}?output_dir={{dir}}")
                print(f"\nClean up temp files using:")
                print(f"  POST /cleanup-temp/{{output_dir}}")
            
            print("\n" + "="*60)
            
            return result
        
        else:
            print(f"✗ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to the server.")
        print("  Make sure the router-service is running on http://127.0.0.1:8000")
        return None
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def download_annotated_image(filename: str, output_dir: str, save_path: str):
    """
    Download annotated image from server
    
    Args:
        filename: Name of the annotated image
        output_dir: Server-side output directory path
        save_path: Local path to save the downloaded image
    """
    url = f"http://127.0.0.1:8000/download-annotated/{filename}"
    params = {'output_dir': output_dir}
    
    print(f"\nDownloading: {filename}")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Saved to: {save_path}")
            return True
        else:
            print(f"✗ Download failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def cleanup_temp_directory(output_dir: str):
    """
    Clean up temporary directory on server
    
    Args:
        output_dir: Server-side output directory path
    """
    # URL encode the path
    from urllib.parse import quote
    encoded_dir = quote(output_dir, safe='')
    
    url = f"http://127.0.0.1:8000/cleanup-temp/{encoded_dir}"
    
    print(f"\nCleaning up temporary directory...")
    
    try:
        response = requests.post(url)
        
        if response.status_code == 200:
            print("✓ Cleanup successful")
            return True
        else:
            print(f"✗ Cleanup failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_cv_endpoint.py <file_path> [--no-annotated]")
        print("\nExample:")
        print("  python test_cv_endpoint.py document.pdf")
        print("  python test_cv_endpoint.py image.jpg --no-annotated")
        sys.exit(1)
    
    file_path = sys.argv[1]
    return_annotated = '--no-annotated' not in sys.argv
    
    # Test the CV analysis
    result = test_cv_analysis(file_path, return_annotated)
    
    if result and return_annotated and result.get('annotated_images'):
        print("\n" + "="*60)
        print("Download and Cleanup Demo")
        print("="*60)
        
        # Ask if user wants to download
        response = input("\nDownload annotated images? (y/n): ")
        if response.lower() == 'y':
            output_dir = result['output_directory']
            download_dir = Path('./cv_results')
            download_dir.mkdir(exist_ok=True)
            
            for img_path in result['annotated_images']:
                filename = Path(img_path).name
                save_path = download_dir / filename
                download_annotated_image(filename, output_dir, str(save_path))
            
            print(f"\n✓ All images downloaded to: {download_dir}")
            
            # Ask if user wants to cleanup
            response = input("\nClean up temporary files on server? (y/n): ")
            if response.lower() == 'y':
                cleanup_temp_directory(output_dir)


if __name__ == "__main__":
    main()
