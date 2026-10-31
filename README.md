# HBA Quản trị

Trang web quản trị HBA chạy trên GitHub Pages: https://hongnhuycao.github.io/quantrihba/

- `index.html`: bản trực tuyến. Đăng nhập bằng tài khoản Google, đọc và ghi trực tiếp các file Google Sheet của HBA theo quyền của tài khoản đó. Trang không chứa sẵn số liệu nào.
- `offline.html`: bản chụp chỉ xem, số liệu lúc 31/10/2026 14:20.
- `config.js`: chỗ điền Google Client ID.
- `gshim.js`: phần nối với Google Sheets API.

## Cấu hình đăng nhập Google (làm một lần)

1. Vào https://console.cloud.google.com/, tạo một project (ví dụ `hba-quantri`).
2. **APIs & Services → Library**: bật **Google Sheets API**.
3. **APIs & Services → OAuth consent screen**: chọn **External**, điền tên app và email. Ở **Test users**, thêm email Google của những người được dùng.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**
   - Authorized JavaScript origins: `https://hongnhuycao.github.io`
5. Sao chép **Client ID** (dạng `xxxx.apps.googleusercontent.com`), dán vào `config.js`:

   ```js
   window.HBA_CONFIG={googleClientId:"xxxx.apps.googleusercontent.com"};
   ```

Người dùng chỉ xem và sửa được những file Sheet mà tài khoản Google của họ đã được chia sẻ.

## Các file Google Sheet trang sử dụng

| File | Quyền cần |
| --- | --- |
| TEST_HBA_TheoDoiHopDong_ChinhThuc | sửa (kế toán), xem (CEO) |
| HBA-Nghi Phep_Phieu Cong Viec | xem (trang chỉ đọc) |
| HBAFileMauKeHoachDuAn | xem (trang chỉ đọc) |
| nhân sự HBA (lịch tuần của GĐDA) | sửa, để kê khai phân công |
| TEST_HBA_DuAn_GDDA | sửa, để GĐDA gửi cập nhật |
