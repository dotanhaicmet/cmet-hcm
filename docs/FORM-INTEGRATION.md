# Thiết kế tích hợp form tuyển sinh sau GitHub Pages

Trang tĩnh hiện tại **không giả lập lưu hồ sơ thành công**. Các trường form: `fullname`, `phone`, `major`, `campus`, `consent` và tùy chọn email/tin nhắn. Client kiểm tra bắt buộc, kiểm tra định dạng điện thoại và xin đồng ý sử dụng dữ liệu.

## Giao thức gợi ý

- Dịch vụ HTTPS: `POST /api/admissions` với JSON UTF-8, cho phép CORS **chỉ** trên domain chính thức.
- Backend kiểm tra server-side, giới hạn kích thước input, chuẩn hóa số điện thoại, rate limit, CAPTCHA/honeypot chống spam, bản ghi thời gian/nguồn/consent và xác nhận đã lưu.
- Trả `201 Created` kèm mã hồ sơ ngẫu nhiên không tiết lộ thông tin nhạy cảm; trả 4xx với lỗi đúng dạng; chỉ 2xx sau khi bền vững lưu bản ghi.
- Không ghi dữ liệu hồ sơ vào Google Analytics, URL, localStorage hay console.
- Có quản trị quyền xem, xóa thông tin theo yêu cầu, thời gian lưu, nhật ký xử lý và backup.
- Sau khi backend được kiểm thử, đặt `window.CMET_CONFIG.formEndpoint` vào `js/config.js`; không đặt secret/token trong JavaScript public.

Trong khi chưa có backend, người dùng có thể nhấn nút **Mở ứng dụng email** rồi tự gửi tới phòng tuyển sinh. Đó là kênh gửi mail thủ công, **không phải hồ sơ gửi trực tiếp vào cơ sở dữ liệu**.
