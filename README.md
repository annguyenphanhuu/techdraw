freecadtechdrawcorev2: Chuyển đổi mô hình 3D sang bản vẽ 2D cơ bản
freecadtechdrawcorev2 là một dự án tập trung vào việc chuyển đổi các mô hình 3D định dạng STEP thành bản vẽ kỹ thuật 2D. Dự án này cung cấp một quy trình cơ bản để tạo ra các hình chiếu 2D và thêm các kích thước đơn giản, sử dụng FreeCAD và ezdxf.

🚀 Mục tiêu
Mục tiêu chính của freecadtechdrawcorev2 là cung cấp một giải pháp hiệu quả để:

Chuyển đổi các tệp mô hình 3D (.step) thành bản vẽ 2D.

Tạo các hình chiếu cơ bản của mô hình.

Thêm các kích thước tuyến tính vào bản vẽ.

Xuất bản vẽ cuối cùng ở định dạng SVG.

💡 So sánh với My CAD Project (Phiên bản nâng cao)
freecadtechdrawcorev2 là một cách tiếp cận cơ bản hơn so với My CAD Project. Trong khi My CAD Project tập trung vào tự động hóa toàn diện với các tính năng nâng cao, freecadtechdrawcorev2 cung cấp một quy trình đơn giản hơn:

Quy trình đơn giản hơn: Tập trung vào các bước cốt lõi để tạo hình chiếu và thêm kích thước, ít tùy chỉnh nâng cao.

Kích thước cơ bản: Chỉ thêm các kích thước tuyến tính, không bao gồm các tính năng kích thước tự động thông minh, GD&T hay độ nhám bề mặt.

Bố cục mặc định: Sử dụng bố cục hình chiếu cơ bản hoặc mặc định của FreeCAD, không có khả năng bố cục thông minh tự động tối ưu hóa vị trí.

Hiển thị cơ bản: Hỗ trợ các đường ẩn, nhưng có thể không bao gồm các tính năng như đường tâm tự động hoặc các tùy chỉnh hiển thị phức tạp khác.

Cấu hình đơn giản: Các tùy chọn cấu hình được giới hạn hơn, tập trung vào các thông số cơ bản như tệp đầu vào và template.

🛠️ Yêu cầu hệ thống
Để chạy freecadtechdrawcorev2, bạn cần:

Docker: Để xây dựng và quản lý môi trường chạy ứng dụng.

Git: Để sao chép mã nguồn từ repository.

📂 Quy trình làm việc (Pipeline)
Dự án này sử dụng một quy trình 3 bước được điều phối bởi scripts/pipeline.py:

Bước 1: Tạo DXF cơ bản từ FreeCAD (scripts/freecad_techdraw_core.py)

Sử dụng FreeCAD để nhập mô hình STEP và tạo các hình chiếu 2D cơ bản.

Xuất các hình chiếu này ra tệp DXF.

Đầu ra: /app/output/step1_base_drawing.dxf

Bước 2: Thêm kích thước vào DXF (scripts/dxf_add_dim.py)

Sử dụng ezdxf để đọc tệp DXF từ Bước 1.

Thêm các kích thước tuyến tính vào bản vẽ.

Đầu ra: /app/output/step2_with_dims.dxf

Bước 3: Render DXF và ghép vào Template SVG (scripts/dxf_render_svg.py)

Đọc tệp DXF đã có kích thước.

Render nội dung DXF thành SVG.

Ghép nội dung SVG này vào một tệp template SVG đã chọn.

Đầu ra: /app/output/final_drawing.svg

🚀 Thiết lập & Chạy
Sao chép Repository:

git clone https://github.com/TranKhoi723/my_cad_project1.5.git # Hoặc URL thực tế của repository của bạn nếu khác
cd freecadtechdrawcorev2 # Hoặc tên thư mục dự án của bạn

Khởi chạy Quy trình:
Sử dụng script run.sh để bắt đầu. Script này sẽ hướng dẫn bạn chọn tệp STEP, template SVG và cấu hình các thông số bản vẽ cơ bản. Nó cũng sẽ tự động xây dựng Docker image (nếu cần) và chạy toàn bộ quy trình.

./scripts/run.sh

Lưu ý: run.sh sẽ tạo một tệp config.tmp.json tạm thời chứa các cài đặt cấu hình của bạn. Tệp này sẽ được sử dụng bởi các script Python bên trong Docker container.

⚙️ Các thông số cấu hình chính (qua run.sh)
Khi chạy run.sh, bạn sẽ được yêu cầu nhập các thông số sau để tùy chỉnh bản vẽ:

INPUT_FILE: Tên tệp STEP 3D đầu vào.

TEMPLATE_FILE: Tên tệp template SVG cho bản vẽ cuối cùng.

AUTO_SCALE: true để tự động tính toán tỷ lệ, hoặc false để đặt thủ công.

SCALE: Giá trị tỷ lệ thủ công (chỉ khi AUTO_SCALE là false).

DIMENSION_OFFSET: Khoảng cách offset của đường kích thước (mm).

DIMENSION_TEXT_HEIGHT: Chiều cao văn bản kích thước (mm).
