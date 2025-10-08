# Technical Drawing Generator

Automatically generates technical drawings (SVG + PDF) from STEP files using FreeCAD.

## System Requirements

- **FreeCAD**: Install FreeCAD and ensure `freecadcmd` command is available from command line
- **Python 3.7+** with libraries:
  ```bash
  pip install cairosvg  # Optional: for SVG to PDF conversion
  ```

## Usage

1. **Edit the STEP file path** in `test_pdf_generation.py`:
   ```python
   # Change this line to your STEP file path
   step_file = Path("CAD/SUPPORT 1.step")  # Update this path
   ```

2. **Run the test script**:
   ```bash
   python test_pdf_generation.py
   ```

The script will automatically generate both SVG and PDF files in the `output/` directory.

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
