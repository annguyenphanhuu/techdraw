# 🎯 Simple TechDraw Generator

Tạo bản vẽ kỹ thuật từ file STEP chỉ với **một lệnh duy nhất**!

## 🚀 Cài đặt nhanh

```bash
# 1. Cài đặt dependencies
python setup_simple.py

# 2. Đảm bảo FreeCAD đã cài đặt và freecadcmd có trong PATH
freecadcmd --version
```

## 💡 Sử dụng

### Cách 1: Sử dụng template mặc định
```bash
python techdraw_simple.py input/bend.step
```

### Cách 2: Chỉ định template cụ thể
```bash
python techdraw_simple.py input/tube.step templates/A3_Landscape_ISO5457_advanced.svg
```

## 📁 Kết quả

Sau khi chạy, bạn sẽ có:
- `output/final_drawing.svg` - Bản vẽ cuối cùng
- `output/step1_base_drawing.dxf` - DXF cơ bản
- `output/step2_with_dims.dxf` - DXF có kích thước

## 📋 Ví dụ đầy đủ

```bash
# Với file bend.step
python techdraw_simple.py input/bend.step

# Output:
🎯 TechDraw Generator
📥 Input: bend.step
📄 Template: A3_Landscape_ISO5457_advanced.svg
📁 Output: output/
==================================================
🚀 Step 1: Creating base drawing with FreeCAD...
✅ Step 1 completed successfully!
🚀 Step 2: Adding dimensions...
✅ Step 2 completed successfully!
🚀 Step 3: Rendering final SVG...
✅ Step 3 completed successfully!

🎉🎉🎉 SUCCESS! 🎉🎉🎉
📁 Check results in: output/
📄 Generated files:
   - final_drawing.svg
   - step1_base_drawing.dxf
   - step2_with_dims.dxf
   - page_info.json
```

## 🔧 Yêu cầu

1. **Python 3.8+**
2. **FreeCAD** với `freecadcmd` trong PATH
3. **Python packages**: ezdxf, matplotlib, lxml (tự động cài đặt)

## 🛠️ Troubleshooting

### Lỗi "freecadcmd not found"
```bash
# Windows: Thêm FreeCAD vào PATH
set PATH=%PATH%;C:\Program Files\FreeCAD 0.21\bin

# Linux: Cài đặt FreeCAD
sudo apt install freecad

# macOS: Cài đặt FreeCAD
brew install freecad
```

### Lỗi Python packages
```bash
pip install ezdxf matplotlib lxml
```

## 🎨 Tùy chỉnh

Script tự động:
- ✅ Tính toán tỷ lệ tối ưu
- ✅ Tạo 3 view: Front, Top, Right
- ✅ Thêm kích thước tổng thể
- ✅ Ghép vào template chuyên nghiệp
- ✅ Export SVG chất lượng cao

## 📊 So sánh với phiên bản phức tạp

| Tính năng | Simple | Full Pipeline |
|-----------|--------|---------------|
| Số lệnh cần chạy | 1 | 3-5 |
| Tương tác user | Không | Có |
| Tùy chỉnh | Tự động | Thủ công |
| Phù hợp cho | Sử dụng nhanh | Tùy chỉnh chi tiết |

Đây là giải pháp hoàn hảo khi bạn cần tạo bản vẽ nhanh chóng mà không cần nhiều tùy chỉnh!
