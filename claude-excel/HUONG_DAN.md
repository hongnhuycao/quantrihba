# ClaudeExcel – Gọi Claude ngay trong Excel

Một module VBA duy nhất (`ClaudeExcel.bas`), không cần cài thêm phần mềm. Excel gọi thẳng Claude API của Anthropic qua Internet.

> Dùng được trên **Excel cho Windows** (Excel 2010 trở lên, gồm Microsoft 365). Excel trên Mac hoặc Excel Online không chạy được macro này.

## 1. Cài đặt (làm một lần, khoảng 5 phút)

1. **Lấy API key:** vào <https://console.anthropic.com>, mục **API Keys**, bấm **Create Key** rồi sao chép key (dạng `sk-ant-...`). Tài khoản cần được nạp tiền (mục Billing).
2. Mở Excel và bấm **Alt + F11** để mở VBA Editor.
3. Chọn **File → Import File…** rồi chọn `ClaudeExcel.bas`.
4. Đóng VBA Editor. Bấm **Alt + F8**, chọn macro **CaiDatApiKey**, bấm **Run** rồi dán key vào.
   - Key được lưu trong Windows của máy bạn, **không nằm trong file Excel**. Gửi file cho người khác thì họ không thấy key.
5. Lưu file dưới dạng **Excel Macro-Enabled Workbook (.xlsm)**.

**Muốn dùng `=CLAUDE()` cho mọi file:** sau khi import, chọn *File → Save As* rồi lưu dạng **Excel Add-in (.xlam)**. Tiếp theo vào *File → Options → Add-ins → Go…* và tích chọn add-in đó.

## 2. Hàm `=CLAUDE()` trong ô

```
=CLAUDE(yêu_cầu; [dữ_liệu]; [model])
```

(Nếu Excel của bạn dùng dấu phẩy để ngăn tham số thì thay `;` bằng `,`.)

| Ví dụ | Kết quả |
|---|---|
| `=CLAUDE("Xin chào")` | Kiểm tra kết nối |
| `=CLAUDE("Phân loại chi phí này: Vật tư / Nhân công / Máy / Khác"; B2)` | Phân loại từng dòng (kéo công thức xuống) |
| `=CLAUDE("Trích mã số thuế, chỉ trả về số"; C2)` | Trích xuất thông tin |
| `=CLAUDE("Tóm tắt tình hình công nợ trong 3 câu"; A1:F50)` | Phân tích cả bảng |
| `=CLAUDE("Dịch sang tiếng Anh"; D2; "claude-haiku-5-5")` | Dùng model rẻ hơn cho việc đơn giản |
| `=CLAUDE(H1 & " " & H2)` | Ghép câu lệnh từ các ô |

- Kết quả được **ghi nhớ**: Excel tính lại công thức thì không gọi lại API, nếu yêu cầu và dữ liệu không đổi. Muốn hỏi lại từ đầu thì chạy macro **XoaBoNhoDem** rồi bấm **Ctrl+Alt+F9**.
- Khi có lỗi, ô sẽ hiện `#CLAUDE: ...` kèm lý do, ví dụ chưa có key, sai key hoặc mất mạng.

## 3. Các macro (Alt + F8)

| Macro | Công dụng |
|---|---|
| **HoiClaudeVeVungChon** | Bôi đen một bảng rồi gõ câu hỏi, ví dụ *"Tổng hợp công nợ theo chủ đầu tư"*. Claude trả lời ra một **sheet mới**. Nếu câu trả lời là bảng thì mỗi cột nằm vào một cột Excel, số được ghi dạng số nên tính SUM được. |
| **ClaudeXuLyTungO** | Bôi đen một cột rồi nhập yêu cầu. Claude xử lý **từng ô** và ghi kết quả vào **cột bên phải** dưới dạng giá trị, nên không bị tính lại và không tốn tiền thêm. Bấm **Esc** để dừng. Cách này hợp cho danh sách dài (hàng trăm dòng) hơn là kéo công thức. |
| **CaiDatApiKey** / **XoaApiKey** | Lưu hoặc xóa API key trên máy này. |
| **XoaBoNhoDem** | Xóa kết quả đã ghi nhớ của hàm `=CLAUDE()`. |

Bạn có thể gán macro vào nút bấm: *Insert → Shapes*, vẽ một hình, nhấp chuột phải chọn **Assign Macro**.

## 4. Cấu hình (sửa ở đầu file `ClaudeExcel.bas` trong VBA Editor)

| Hằng số | Mặc định | Ý nghĩa |
|---|---|---|
| `MODEL_MAC_DINH` | `claude-opus-5-5` | Model mạnh nhất cho mọi việc. Đổi sang `claude-sonnet-5-5` hoặc `claude-haiku-5-5` để nhanh và rẻ hơn. |
| `EFFORT` | `low` | Mức "suy nghĩ" của Claude. `low` cho câu trả lời nhanh trong ô. Bài toán phức tạp thì dùng `medium` hoặc `high`. |
| `MAX_TOKENS` | `16000` | Độ dài tối đa của câu trả lời. |

Khi Claude Opus 5.5 hoặc Sonnet 5.5 từ chối một yêu cầu vì bộ lọc an toàn, macro sẽ tự chuyển sang model dự phòng (server-side fallback).

## 5. Chi phí và bảo mật

- Bạn trả tiền theo số token đã dùng, xem giá trong Console. Mỗi ô `=CLAUDE()` là một lần gọi API. Một bảng lớn gửi kèm sẽ tốn nhiều token hơn.
- Dữ liệu trong vùng bạn chọn sẽ được **gửi lên Anthropic**. Đừng gửi dữ liệu mà công ty không cho phép đưa ra ngoài.
- Muốn tạm khóa key: chạy **XoaApiKey**, hoặc thu hồi key trong Console.

## 6. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `Chua co API key` | Chạy macro **CaiDatApiKey** |
| `API key khong dung (HTTP 401)` | Key sai hoặc đã bị thu hồi, hãy tạo key mới |
| `HTTP 400 ... credit balance` | Tài khoản hết tiền, nạp thêm ở mục Billing |
| `Vuot gioi han goi (429)` | Gọi quá nhiều cùng lúc, đợi một chút rồi chạy lại |
| Macro không chạy | *File → Options → Trust Center → Macro Settings*, bật macro. Hoặc nhấp chuột phải vào file, chọn *Properties* rồi tích **Unblock** |
| Excel "đứng" vài giây | Bình thường: Excel chờ Claude trả lời. Danh sách dài thì dùng **ClaudeXuLyTungO** |
