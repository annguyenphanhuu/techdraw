#!/usr/bin/env python3
"""
Test script để kiểm tra auto-scaling và positioning với tất cả STEP files
"""

import os
import sys
import subprocess

def test_file(step_file):
    """Test một STEP file cụ thể"""
    print(f"\n{'='*60}")
    print(f"Testing: {step_file}")
    print(f"{'='*60}")
    
    # Cập nhật run.py để sử dụng file này
    with open('run.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thay đổi step_file_path
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('step_file_path = '):
            lines[i] = f'step_file_path = os.path.join(os.path.dirname(__file__), "input", "{step_file}")'
            break
    
    # Ghi lại file
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # Chạy test
    try:
        result = subprocess.run(['freecadcmd', 'run.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            # Tìm thông tin auto-scaling trong output
            for line in result.stdout.split('\n'):
                if 'Auto-scaling:' in line or 'Positions:' in line or 'Dimensions:' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ FAILED")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Auto-Scaling & Positioning System")
    print("=" * 60)
    
    # Danh sách các file test
    test_files = [
        "sheet.step",
        "tube.step", 
        "block.step"
    ]
    
    # Kiểm tra file tồn tại
    input_dir = "input"
    available_files = []
    
    for file in test_files:
        file_path = os.path.join(input_dir, file)
        if os.path.exists(file_path):
            available_files.append(file)
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
    
    if not available_files:
        print("❌ No test files found!")
        return
    
    # Test từng file
    for file in available_files:
        test_file(file)
    
    print(f"\n{'='*60}")
    print("🏁 Testing completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
