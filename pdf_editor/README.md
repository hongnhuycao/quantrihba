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
| Sửa nội dung | Thêm chữ tiếng Việt (chọn phông, cỡ, màu) • **Tìm & thay chữ có sẵn** (Ctrl+H) • Chèn ảnh / chữ ký • Che trắng (xoá hẳn nội dung bên dưới) • Tô sáng • Vẽ khung • Ghi chú |
| Trang | Xoay • Xoá • Di chuyển lên/xuống • Nhân bản • Chèn trang trắng • Chèn trang từ PDF khác • Chọn nhiều trang bằng Ctrl/Shift |
| Tệp | Gộp nhiều PDF/ảnh • Ảnh → PDF • Trích trang • Tách mỗi N trang • Xuất ảnh PNG • Trích văn bản .txt |
| Khác | Đóng dấu chìm • Đánh số trang • Nén giảm dung lượng • Đặt mật khẩu • Mở tệp có mật khẩu • Tìm kiếm • Hoàn tác/Làm lại (30 bước) |

## Phím tắt
Ctrl+O mở · Ctrl+S lưu · Ctrl+Shift+S lưu thành · Ctrl+Z / Ctrl+Y hoàn tác / làm lại · Ctrl+H tìm & thay · Ctrl+R / Ctrl+L xoay · Ctrl+lăn chuột phóng to · PageUp/PageDown chuyển trang · Delete xoá trang

## Giới hạn cần biết
- **Tìm & thay chữ** viết lại cả dòng chứa chữ bằng phông đang chọn, nên phông của dòng đó có thể khác chút so với bản gốc. Dòng quá dài có thể tràn lề.
- **PDF scan** (trang là ảnh chụp) không có chữ thật, nên không tìm hay sửa chữ được. Vẫn thêm chữ, chèn ảnh và che trắng bình thường.
- Phông chuẩn của PDF không có dấu tiếng Việt, vì vậy phần mềm dùng Arial hoặc Times New Roman có sẵn trên máy. Kèm theo phần mềm có phông Noto Serif để dùng khi máy không có các phông này.

## Cấu trúc
- `pdf_editor.py`: giao diện.
- `pdf_core.py`: các thao tác xử lý PDF, có thể gọi riêng từ script khác.
- `fonts/`: phông có dấu tiếng Việt (Noto Serif, giấy phép SIL OFL).
