#!/bin/bash
# scripts/run.sh (Advanced Version with Auto-Scale Option)

# --- Path Setup ---
PROJECT_ROOT=$(dirname "$(realpath "$0")")/..
INPUT_DIR="$PROJECT_ROOT/input"
TEMPLATE_DIR="$PROJECT_ROOT/templates"
OUTPUT_DIR="$PROJECT_ROOT/output"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
CONFIG_FILE="$PROJECT_ROOT/config.tmp.json"

# --- Cleanup ---
echo "🧹 Cleaning up..."
rm -f "$OUTPUT_DIR"/*
rm -f "$CONFIG_FILE"
echo ""

# --- STEP 1 & 2: SELECT FILE AND TEMPLATE (Unchanged) ---
echo " STEP 1: Select STEP file"
mapfile -t step_files < <(ls -1 "$INPUT_DIR"/*.step 2>/dev/null)
if [ ${#step_files[@]} -eq 0 ]; then echo "❌ Error: No .step files found"; exit 1; fi
PS3="Select a file: "; select selected_step_path in "${step_files[@]}"; do if [[ -n "$selected_step_path" ]]; then INPUT_FILE=$(basename "$selected_step_path"); break; else echo "Invalid selection."; fi; done; echo ""

echo " STEP 2: Select template"
mapfile -t template_files < <(find "$TEMPLATE_DIR" -name "*.svg")
if [ ${#template_files[@]} -eq 0 ]; then echo "❌ Error: No .svg files found"; exit 1; fi
PS3="Select a template: "; select selected_template_path in "${template_files[@]}"; do if [[ -n "$selected_template_path" ]]; then TEMPLATE_FILE=${selected_template_path#"$TEMPLATE_DIR/"}; break; else echo "Invalid selection."; fi; done; echo ""

# --- STEP 3: CONFIGURATION (Updated) ---
echo " STEP 3: Configuration"

# Default SCALE is 1.0 and AUTO_SCALE is true
SCALE="1.0"
AUTO_SCALE="true"

read -p "Use auto-scale? (yes/no) [Default: yes]: " AUTO_SCALE_INPUT
AUTO_SCALE_CHOICE=${AUTO_SCALE_INPUT:-yes}

if [[ "$AUTO_SCALE_CHOICE" == "no" || "$AUTO_SCALE_CHOICE" == "n" ]]; then
    AUTO_SCALE="false"
    read -p "Enter manual scale [1.0]: " SCALE_INPUT
    SCALE=${SCALE_INPUT:-1.0}
else
    # Keep the default value of AUTO_SCALE as "true"
    # The scale will be calculated by the Python script, so the value here doesn't matter
    SCALE="auto" 
fi

read -p "Dim line offset (mm) [15.0]: " DIM_OFFSET_INPUT
DIMENSION_OFFSET=${DIM_OFFSET_INPUT:-15.0}
read -p "Dim text height (mm) [2.5]: " DIM_TEXT_HEIGHT_INPUT
DIMENSION_TEXT_HEIGHT=${DIM_TEXT_HEIGHT_INPUT:-2.5}
echo ""

# --- CONFIRMATION (Updated) ---
echo "================ SUMMARY ================"
echo "  Input file           : $INPUT_FILE"
echo "  Template             : $TEMPLATE_FILE"
if [[ "$AUTO_SCALE" == "true" ]]; then
    echo "  Scale                : Auto-Scale"
else
    echo "  Scale                : $SCALE (Manual)"
fi
echo "  Dim line offset      : $DIMENSION_OFFSET mm"
echo "  Dim text height      : $DIMENSION_TEXT_HEIGHT mm"
echo "======================================"
read -p "Continue? (Y/n): " confirm
if [[ "$confirm" != "Y" && "$confirm" != "y" && "$confirm" != "" ]]; then
    echo "Aborted."
    exit 0
fi

# --- CREATE CONFIGURATION FILE (Updated) ---
echo "📝 Creating configuration file..."
cat > "$CONFIG_FILE" << EOL
{
  "INPUT_FILE": "$INPUT_FILE",
  "TEMPLATE_FILE": "$TEMPLATE_FILE",
  "AUTO_SCALE": "$AUTO_SCALE",
  "SCALE": "$SCALE",
  "DIMENSION_OFFSET": "$DIMENSION_OFFSET",
  "DIMENSION_TEXT_HEIGHT": "$DIMENSION_TEXT_HEIGHT"
}
EOL

# --- BUILD AND RUN DOCKER (Unchanged) ---
echo "🐳 Building Docker image freecad-automation-v2 (if needed)..."
docker build -t freecad-automation-v2 "$PROJECT_ROOT" > /dev/null

echo "🚀 Starting processing..."
# --- CHANGE HERE ---
# The line mounting the scripts directory has been removed
docker run --rm \
  -v "$INPUT_DIR:/app/input" \
  -v "$TEMPLATE_DIR:/app/templates" \
  -v "$OUTPUT_DIR:/app/output" \
  -v "$CONFIG_FILE:/app/config.json" \
  freecad-automation-v2

# --- FINAL CLEANUP (Unchanged) ---
rm -f "$CONFIG_FILE"
echo "🎉🎉🎉 COMPLETE! Check the results in the '$OUTPUT_DIR' directory 🎉🎉🎉"