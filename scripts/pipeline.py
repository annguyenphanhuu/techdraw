# scripts/pipeline.py (Complete Version - 3 Steps)
import os
import subprocess
import sys
import json
import traceback

def run_command(command: list[str]):
    """Runs a command and exits the program if it fails."""
    print(f"\n--- Running: {' '.join(command)} ---")
    subprocess.run(command, check=True)

def main():
    """
    Coordinates the 3-step process:
    1. Create DXF from FreeCAD.
    2. Add dimensions to the DXF.
    3. Render the final DXF to an SVG and merge it with a template.
    """
    print("--- STARTING THE COMPLETE 3-STEP PIPELINE ---")
    try:
        with open("/app/config.json", 'r') as f:
            config = json.load(f)
        print("ℹ️ Config read:", config)
        
        template_path = f"/app/templates/{config.get('TEMPLATE_FILE', 'A3_Landscape_ISO5457_advanced.svg')}"

        # --------------------------------------------------------------------------
        # STEP 1: CREATE BASE DXF FROM STEP FILE
        # Output: /app/output/step1_base_drawing.dxf
        # --------------------------------------------------------------------------
        run_command([
            "xvfb-run", 
            "python", 
            "/app/scripts/freecad_techdraw_core.py"
        ])

        # --------------------------------------------------------------------------
        # STEP 2: ADD DIMENSIONS TO THE DXF FILE
        # Input: /app/output/step1_base_drawing.dxf
        # Output: /app/output/step2_drawing_with_dims.dxf
        # --------------------------------------------------------------------------
        run_command([
            "python",
            "/app/scripts/dxf_add_dim.py"
        ])

        # --------------------------------------------------------------------------
        # STEP 3: RENDER THE DXF (WITH DIMENSIONS) AND MERGE WITH TEMPLATE
        # Input: /app/output/step2_drawing_with_dims.dxf
        # Output: /app/output/final_drawing_with_template.svg
        # --------------------------------------------------------------------------
        run_command([
            "python",
            "/app/scripts/dxf_render_svg.py",
            template_path  # Pass the template path as an argument
        ])
        
        print("\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"🎉🎉🎉 CHECK THE RESULTS IN THE output DIRECTORY 🎉🎉🎉")

    except Exception as e:
        print(f"\n❌ ERROR in pipeline: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()