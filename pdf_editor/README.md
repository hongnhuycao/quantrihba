# Trình sửa PDF (Python)

Phần mềm chỉnh sửa PDF có giao diện tiếng Việt, viết bằng Python, Tkinter và PyMuPDF.

## Cài đặt và chạy

**Windows:** cài [Python 3.10 trở lên](https://www.python.org/downloads/) (nhớ tích ô *Add Python to PATH*). Sau đó bấm đúp vào **`chay_phan_mem.bat`**. Lần đầu chạy, file này tự cài thư viện còn thiếu.

**Chạy bằng lệnh (mọi hệ điều hành):**
```bash
pip install -r requirements.txt
python pdf_editor.py            # hoặc: python pdf_editor.py duong_dan/tep.pdf
```

**Đóng gói thành `TrinhSuaPDF.exe`** (để chạy trên máy không cài Python): bấm đúp vào `dong_goi_exe.bat`. File `.exe` nằm trong thư mục `dist\`.

## Chức năng

| Nhóm | Chức năng |
|---|---|
| Sửa nội dung | Thêm chữ tiếng Việt (chọn phông, cỡ, màu) • **Tìm & thay chữ có sẵn, giữ phông gốc** (Ctrl+H) • Chèn ảnh / chữ ký • Che trắng (xoá hẳn nội dung bên dưới) • Tô sáng • Vẽ khung • Ghi chú |
| Trang | Xoay • Xoá • Di chuyển lên/xuống • Nhân bản • Chèn trang trắng • Chèn trang từ PDF khác • Chọn nhiều trang bằng Ctrl/Shift |
| Tệp | Gộp nhiều PDF/ảnh • Ảnh → PDF • Trích trang • Tách mỗi N trang • Xuất ảnh PNG • Trích văn bản .txt |
| Bản scan | **Nhận dạng chữ (OCR) tiếng Việt** để tìm, chép và thay chữ • Công cụ **✎ Sửa chữ scan**: che chữ cũ bằng đúng màu giấy, viết chữ mới cùng cỡ, cùng màu mực, đúng dòng |
| Khác | Đóng dấu chìm • Đánh số trang • Nén giảm dung lượng • Đặt mật khẩu • Mở tệp có mật khẩu • Tìm kiếm • Hoàn tác/Làm lại (30 bước) |

## Phím tắt
Ctrl+O mở · Ctrl+S lưu · Ctrl+Shift+S lưu thành · Ctrl+Z / Ctrl+Y hoàn tác / làm lại · Ctrl+H tìm & thay · Ctrl+R / Ctrl+L xoay · Ctrl+lăn chuột phóng to · PageUp/PageDown chuyển trang · Delete xoá trang

## Giữ phông chữ gốc khi thay chữ
Khi thay chữ, phần mềm thử lần lượt:
1. **Phông nhúng trong PDF.** Dùng được khi phông nhúng có đủ các ký tự cần viết.
2. **Phông cùng tên cài trên máy**, cùng kiểu đậm hoặc nghiêng (Times New Roman, Arial, Calibri…). Hầu hết PDF xuất từ Word chỉ nhúng một phần phông, nên phần mềm thường dùng cách này. Kết quả vẫn giống hệt bản gốc nếu máy có cài phông đó.
3. **Phông đang chọn trên thanh công cụ**, khi hai cách trên đều không được.

Sau khi thay, phần mềm báo mỗi đoạn chữ đã dùng phông nào.

## Sửa file scan
1. Cài **Tesseract OCR** (miễn phí). Trên Windows, tải bộ cài tại <https://github.com/UB-Mannheim/tesseract/wiki>. Khi cài, ở mục *Additional language data*, tích chọn **Vietnamese**.
2. Mở file scan, chọn **Chỉnh sửa → Nhận dạng chữ bản scan (OCR)**. Ảnh gốc giữ nguyên, phần mềm chỉ thêm một lớp chữ ẩn nằm đúng vị trí trên trang.
3. Sau bước này có thể tìm và chép chữ, dùng **Tìm & thay** (Ctrl+H), hoặc dùng công cụ **✎ Sửa chữ scan**: kéo khung quanh chữ cần sửa rồi gõ chữ mới.
4. Trên thanh công cụ, chọn phông gần giống bản scan. Văn bản hành chính thường dùng **Times New Roman**.

Công cụ ✎ Sửa chữ scan dùng được cả khi chưa cài OCR. Khi đó phần mềm ước lượng cỡ chữ theo chiều cao vùng bạn kéo.

## Giới hạn cần biết
- Thay chữ trên PDF thường sẽ viết lại cả dòng chứa chữ đó. Dòng quá dài có thể tràn lề.
- Trên bản scan, phần mềm chỉ phủ màu giấy lên chữ cũ, nét mực cũ vẫn còn trong ảnh bên dưới. Nếu cần xoá hẳn thông tin nhạy cảm, hãy dùng **Che trắng**.
- OCR có thể đọc sai vài chữ hoặc dính chữ (ví dụ "CHỦNGHĨA"), nhất là khi bản scan mờ hoặc chụp nghiêng. Scan ở 300 dpi trở lên sẽ cho kết quả tốt nhất.
- Phông chuẩn của PDF không có dấu tiếng Việt, vì vậy phần mềm dùng phông có sẵn trên máy. Kèm theo phần mềm có phông Noto Serif để dùng khi máy không có phông phù hợp.

## Cấu trúc
- `pdf_editor.py`: giao diện.
- `pdf_core.py`: các thao tác xử lý PDF, có thể gọi riêng từ script khác.
- `fonts/`: phông có dấu tiếng Việt (Noto Serif, giấy phép SIL OFL).
