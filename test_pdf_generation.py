#!/usr/bin/env python3
"""
Test script to diagnose PDF generation issues
"""

import logging
from pathlib import Path
from technical_drawing_generator import TechnicalDrawingGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_pdf_generation():
    """Test PDF generation with the existing STEP file"""
    
    # Input and output paths
    step_file = Path("/home/tis/techdraw-update/FICHIER PROMPT/SUPPORT/SUPPORT/SUPPORT 3.step")
    output_dir = Path("output")
    
    print(f"Testing PDF generation...")
    print(f"STEP file: {step_file}")
    print(f"Output directory: {output_dir}")
    print(f"STEP file exists: {step_file.exists()}")
    
    if not step_file.exists():
        print("ERROR: STEP file not found!")
        return
    
    try:
        # Create generator
        generator = TechnicalDrawingGenerator()
        
        # Generate technical drawing
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"drawing_{timestamp}"
        success, svg_path, pdf_path, message = generator.generate_technical_drawing(
            step_file, output_dir, filename
        )
        
        print(f"\nResults:")
        print(f"Success: {success}")
        print(f"SVG path: {svg_path}")
        print(f"PDF path: {pdf_path}")
        print(f"Message: {message}")
        
        # Check what files were actually created
        print(f"\nFiles in output directory:")
        if output_dir.exists():
            for file in output_dir.iterdir():
                print(f"  {file.name} ({file.stat().st_size} bytes)")
        else:
            print("  Output directory does not exist")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()
