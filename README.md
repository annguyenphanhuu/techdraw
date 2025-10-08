# Technical Drawing Generator

Automatically generates technical drawings (SVG + PDF) from STEP files using FreeCAD.

## System Requirements

- **FreeCAD**: Install FreeCAD and ensure `freecadcmd` command is available from command line
- **Python 3.7+** with libraries:
  ```bash
  pip install cairosvg  # Optional: for SVG to PDF conversion
  ```

## Usage

### 1. Direct Function Usage

```python
from pathlib import Path
from technical_drawing_generator import generate_technical_drawing_from_step

# Generate technical drawing from STEP file
result = generate_technical_drawing_from_step(
    step_file_path=Path("input/part.step"),
    output_dir=Path("output"),
    base_filename="my_part_drawing"  # Optional
)

print(f"Success: {result['success']}")
print(f"SVG file: {result['svg_path']}")
print(f"PDF file: {result['pdf_path']}")
```

### 2. Class Usage

```python
from pathlib import Path
from technical_drawing_generator import TechnicalDrawingGenerator

generator = TechnicalDrawingGenerator()
success, svg_path, pdf_path, message = generator.generate_technical_drawing(
    step_file_path=Path("input/part.step"),
    output_dir=Path("output")
)
```

## Directory Structure

```
├── technical_drawing_generator.py  # Main module
├── techdraw/                      # Techdraw directory (cloned from GitHub)
│   ├── run_techdraw_final.py     # FreeCAD script
│   ├── templates/                # SVG templates
│   │   └── A4_TOLERY.svg
│   └── temp_output/              # Temporary directory
├── output/                       # Output directory (auto-created)
└── README.md
```

## Features

- ✅ Generate technical drawings from STEP files
- ✅ Export to SVG and PDF formats
- ✅ Automatic hole detection and dimensioning
- ✅ Uses ISO standard A4 template
- ✅ Supports 3 views: front, top, right

## Notes

- Ensure FreeCAD is installed and `freecadcmd` command is available
- Input STEP file must be valid
- Without `cairosvg`, only SVG files will be generated
- Processing time depends on 3D model complexity

## Troubleshooting

**Error "freecadcmd not found":**
- Install FreeCAD and add to PATH
- Or use full path to freecadcmd

**Template not found error:**
- Ensure `techdraw/templates/A4_TOLERY.svg` exists

**PDF file not generated:**
- Install `cairosvg`: `pip install cairosvg`
- Or install `wkhtmltopdf` as alternative
