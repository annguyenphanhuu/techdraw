# 🎯 Single Command Wrapper cho TechDraw Pipeline

Wrapper scripts để chạy **toàn bộ pipeline có sẵn của bạn** chỉ với **một lệnh duy nhất**.

## 📋 Tổng quan

Các wrapper này **KHÔNG thay đổi** code hoặc thuật toán của bạn. Chúng chỉ:
- ✅ Tự động tạo config file
- ✅ Tự động copy input file vào đúng vị trí
- ✅ Chạy tuần tự 3 scripts có sẵn của bạn
- ✅ Cleanup tự động

## 🚀 Cách sử dụng

### **Option 1: Direct Python (Không cần Docker)**
```bash
# Sử dụng template mặc định
python run_single_command.py input/bend.step

# Chỉ định template cụ thể
python run_single_command.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg
```

### **Option 2: Docker (Sử dụng Docker setup có sẵn)**
```bash
# Sử dụng template mặc định
python run_single_docker.py input/bend.step

# Chỉ định template cụ thể  
python run_single_docker.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg
```

## 🔄 Quy trình thực tế

Wrapper sẽ chạy **chính xác** pipeline có sẵn của bạn:

```
1. Tạo config.json tự động
   ↓
2. Copy input file vào input/
   ↓
3. Chạy scripts/freecad_techdraw_core.py
   ↓
4. Chạy scripts/dxf_add_dim.py
   ↓
5. Chạy scripts/dxf_render_svg.py
   ↓
6. Cleanup config file
```

## 📁 Files được tạo

1. **`run_single_command.py`** - Wrapper cho direct Python execution
2. **`run_single_docker.py`** - Wrapper cho Docker execution

## ✨ Tính năng tự động

- ✅ **Auto-detect template**: Tự động chọn template tốt nhất nếu không chỉ định
- ✅ **Auto-config**: Tạo config với settings mặc định tối ưu
- ✅ **Auto-cleanup**: Dọn dẹp files tạm thời
- ✅ **Auto-copy**: Copy input file vào đúng vị trí
- ✅ **Error handling**: Báo lỗi rõ ràng từng bước

## 🎯 Ví dụ output

```bash
$ python run_single_command.py input/bend.step

🎯 TechDraw Pipeline (Using Your Existing Code)
📥 Input: bend.step
📄 Template: A3_Landscape_ISO5457_advanced.svg
📁 Output: output/
==================================================
📋 Copied input to: input/bend.step
🚀 Step 1: FreeCAD TechDraw Core...
✅ Step 1: FreeCAD TechDraw Core completed!
🚀 Step 2: Add Dimensions...
✅ Step 2: Add Dimensions completed!
🚀 Step 3: Render SVG...
✅ Step 3: Render SVG completed!

🎉🎉🎉 SUCCESS! 🎉🎉🎉
📁 Check results in: output/
📄 Generated files:
   - step1_base_drawing.dxf
   - step2_with_dims.dxf
   - final_drawing_with_template.svg
   - page_info.json
```

## 🔧 Yêu cầu

### Cho `run_single_command.py`:
- Python 3.8+
- FreeCAD với freecadcmd trong PATH
- Các Python packages: ezdxf, matplotlib, lxml

### Cho `run_single_docker.py`:
- Docker
- Dockerfile và scripts có sẵn của bạn

## 📊 So sánh với workflow gốc

| Aspect | Workflow gốc | Single Command |
|--------|--------------|----------------|
| **Scripts sử dụng** | ✅ Scripts gốc của bạn | ✅ **Chính xác scripts gốc** |
| **Thuật toán** | ✅ Thuật toán của bạn | ✅ **Chính xác thuật toán của bạn** |
| **Số lệnh cần chạy** | ❌ 3-5 lệnh | ✅ **1 lệnh duy nhất** |
| **Tương tác user** | ❌ Cần input | ✅ **Tự động** |
| **Config file** | ❌ Tạo thủ công | ✅ **Tự động tạo** |
| **File management** | ❌ Copy thủ công | ✅ **Tự động copy** |

## 💡 Lưu ý quan trọng

- ✅ **100% code của bạn**: Không thay đổi gì trong scripts gốc
- ✅ **100% thuật toán của bạn**: Chỉ là wrapper layer
- ✅ **Tương thích hoàn toàn**: Có thể chạy song song với workflow gốc
- ✅ **Không dependencies mới**: Sử dụng chính xác setup hiện tại

Đây chỉ là **convenience wrapper** để làm cho pipeline của bạn dễ sử dụng hơn!
