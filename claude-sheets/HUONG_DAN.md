# ClaudeSheets – Gọi Claude ngay trong Google Sheets

Một file Apps Script (`Code.gs`) duy nhất. Không cần cài add-on và chạy được trên mọi máy, kể cả Mac và điện thoại (với hàm `=CLAUDE()`).

## 1. Cài đặt (làm một lần cho mỗi file Sheet, khoảng 3 phút)

1. **Lấy API key:** vào <https://platform.claude.com>, mục **API Keys**, bấm **Create Key** rồi sao chép key (`sk-ant-...`). Tài khoản cần có credit (mục **Settings → Billing**).
2. Mở file Google Sheet, chọn **Tiện ích mở rộng (Extensions) → Apps Script**.
3. Xóa hết nội dung có sẵn trong `Code.gs`, **dán toàn bộ nội dung file `Code.gs`** này vào, rồi bấm 💾 **Lưu**.
4. Quay lại Sheet và **tải lại trang (F5)**. Trên thanh menu sẽ có thêm mục **🤖 Claude**.
5. Chọn **🤖 Claude → Cài API key…** rồi dán key.
   - Lần đầu, Google hỏi quyền truy cập. Bấm **Tiếp tục**, chọn tài khoản của bạn. Nếu thấy *"Google chưa xác minh ứng dụng này"* thì bấm **Nâng cao → Đi tới … (không an toàn)** rồi **Cho phép**. Script là của chính bạn nên làm vậy là bình thường.

> ⚠️ Key được lưu trong Script Properties của file Sheet. Ai có **quyền chỉnh sửa** file đều mở được Apps Script và thấy key. Chỉ cấp quyền chỉnh sửa cho người tin cậy. Người chỉ có quyền **xem** thì không thấy key.

## 2. Hàm `=CLAUDE()` trong ô

```
=CLAUDE(yêu_cầu; [dữ_liệu]; [model])
```

| Ví dụ | Kết quả |
|---|---|
| `=CLAUDE("Xin chào")` | Kiểm tra kết nối |
| `=CLAUDE("Phân loại chi phí này: Vật tư / Nhân công / Máy / Khác"; B2)` | Phân loại từng dòng |
| `=CLAUDE("Trích mã số thuế, chỉ trả về số"; C2)` | Trích xuất thông tin |
| `=CLAUDE("Tóm tắt tình hình công nợ trong 3 câu"; A1:F50)` | Phân tích cả bảng |
| `=CLAUDE("Dịch sang tiếng Anh"; D2; "claude-haiku-5-5")` | Dùng model rẻ và nhanh hơn |

Lưu ý:
- Google chỉ cho mỗi hàm trong ô chạy **tối đa 30 giây**. Câu hỏi dài hoặc bảng lớn có thể bị lỗi hết giờ. Khi đó hãy dùng menu **Hỏi Claude về vùng đang chọn**, vì menu được chạy tới 6 phút.
- Kết quả được ghi nhớ trong 6 giờ, nên mở lại file không tốn tiền gọi lại. Sau 6 giờ, nếu Google tính lại công thức thì Claude sẽ được gọi lại. Kết quả nào muốn giữ cố định thì **sao chép rồi dán giá trị** (Ctrl+Shift+V), hoặc dùng menu **Xử lý từng ô**.
- Kéo công thức xuống hàng trăm dòng cùng lúc thì Google sẽ chạy nhiều ô một lúc, dễ bị giới hạn. Danh sách dài nên dùng menu **Xử lý từng ô**.

## 3. Menu 🤖 Claude

| Mục | Công dụng |
|---|---|
| **Hỏi Claude về vùng đang chọn…** | Bôi đen một bảng rồi gõ câu hỏi. Claude trả lời ra một **sheet mới**. Nếu câu trả lời là bảng thì mỗi cột nằm vào một cột của Sheet, số ghi dạng số nên tính SUM được. |
| **Xử lý từng ô…** | Bôi đen một cột rồi nhập yêu cầu. Claude xử lý từng ô (8 ô một lúc) và ghi kết quả **dạng giá trị** vào **cột bên phải**. Ô đã có kết quả thì bỏ qua: nếu Google dừng giữa chừng sau 6 phút, chỉ cần chạy lại để làm tiếp. |
| **Cài API key… / Xóa API key** | Lưu hoặc xóa key. |

## 4. Cấu hình (sửa ở đầu file `Code.gs`)

| Hằng số | Mặc định | Ý nghĩa |
|---|---|---|
| `MODEL_MAC_DINH` | `claude-opus-5-5` | Model mạnh nhất. Đổi sang `claude-sonnet-5-5` hoặc `claude-haiku-5-5` để nhanh và rẻ hơn. |
| `EFFORT` | `low` | Mức "suy nghĩ" của Claude. `low` cho câu trả lời nhanh. Bài toán phức tạp thì dùng `medium` hoặc `high`. |
| `SO_O_CHAY_SONG_SONG` | `8` | Số ô gửi cùng lúc trong menu **Xử lý từng ô**. |

## 5. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `Chưa có API key` | Chọn menu **🤖 Claude → Cài API key** |
| `API key không đúng (HTTP 401)` | Key sai hoặc đã bị thu hồi |
| `HTTP 400 - Your credit balance is too low` | Hết credit, nạp thêm ở platform.claude.com → Settings → Billing |
| `Vượt giới hạn gọi (429)` | Gọi quá nhiều cùng lúc, đợi rồi thử lại |
| Ô báo *"Vượt quá thời gian thực thi tối đa"* | Câu hỏi quá dài so với giới hạn 30 giây của hàm trong ô. Hãy dùng menu, hoặc dùng model `claude-haiku-5-5` |
| Không thấy menu 🤖 Claude | Tải lại trang Sheet (F5) |
