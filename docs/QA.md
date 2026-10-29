# Kiểm thử CMET Website

## Kiểm tra tự động (Python stdlib)

`python scripts/check.py` kiểm tra HTML/CSS/JS còn tồn tại, link nội bộ, ảnh và file CSS/JS không bị thiếu, ảnh không được sử dụng, đường dẫn đối chiếu nguồn ảnh, file tạm không cần thiết, file ảnh trùng SHA-256, cùng chữ ký định dạng GIF. Kết quả kiểm tra thuộc **mã nguồn trong repo**, không chứng minh khả năng chạy API production.

## Kiểm thử trình duyệt

Đã chạy bản dựng mới trong Chromium dùng CSS và các ảnh WebP được nhúng để tránh giới hạn truy cập mạng trong môi trường thử nghiệm:

- Desktop: khung 1650 × 927 px; không tràn ngang.
- Mobile: khung 390 × 844 px; không tràn ngang, menu mobile mở được.
- Trang ngành: 16 thẻ từ dữ liệu, bộ lọc nhóm hoạt động (thử nhóm cuối hiển thị 4 mục).

Đã thử thêm với JavaScript chạy trong Chromium: mở menu mobile, lọc ngành, tìm kiếm tin tức không dấu (trả 2 tin về bổ nhiệm), mở/đóng album lightbox, kiểm tra form (xác nhận chưa tự gửi và hiện nút email).

Cần kiểm tra thêm **sau khi deploy lên URL thật**: toàn bộ link trang con, biểu mẫu trên iOS/Android, lightbox, Chrome/Edge/Safari/Firefox, SEO indexing và Lighthouse.

## Nghiệm thu nghiệp vụ còn thiếu

- Phê duyệt toàn văn tin tức, danh sách đầy đủ các ngành đào tạo, địa chỉ/cơ sở và quyền lợi học bổng.
- Quyết định luồng tiếp nhận hồ sơ thực, chọn API backend hoặc Google Apps Script và cấu hình chống spam.
- Phê duyệt chính sách thu thập dữ liệu cá nhân; kiểm tra quyền sở hữu ảnh/đối tác.
- Trỏ DNS và chạy `build.py --site-url` đúng URL triển khai để tạo sitemap và canonical.

## Kiểm thử lại v3 — 14/10/2026

Bản kiểm thử Chromium (desktop 1650 × 927px và mobile 390 × 844px, dùng tài nguyên cục bộ inline để tương đương HTML/CSS/JS trên hosting tĩnh) cho kết quả:

- Không có lỗi JavaScript được ghi nhận, không tràn ngang ở hai kích thước trên.
- Hai `.news-layout` có chiều cao cột trái và cột phải bằng nhau (488px tại 1650px). Mỗi hàng bên phải ~151px, không chừa khoảng trắng ở dưới.
- Hover phóng to ảnh feature: ma trận biến đổi từ `none` sang `scale(1.055)`; có `:focus-visible` và ưu tiên giảm chuyển động.
- Banner `.gif` đã được tham chiếu trực tiếp; mỗi banner nguồn có 20 khung hình. Bản `picture source` chọn WebP tĩnh cho `prefers-reduced-motion: reduce`.
- Footer hiển thị bằng `Segoe UI, Arial, Helvetica, sans-serif`, `font-weight:700`, UTF-8 đúng ký tự tiếng Việt.
- Menu mobile có thể mở, các đường dẫn CSS/JS/ảnh đều tồn tại sau dựng.

**Chưa được kiểm thử trong môi trường production**: API form tiếp nhận, thiết bị Safari/iOS, thời gian tải thực tế trên kết nối 3G/4G, Lighthouse sau xuất bản, canonical trên tên miền thật.


## Kiểm thử v4 — cân đối giao diện khối tuyển sinh

- 1650 × 927 và 1366 × 900: cạnh trên/dưới 2 cột trùng nhau theo bounding rectangles; poster giữ tỷ lệ gốc, không bị crop; phần bên dưới poster là HTML.
- 1150 × 850 và 390 × 844: nội dung chuyển sang một cột, không tràn ngang.
- Mobile: menu mở được; tất cả kịch bản render không phát sinh lỗi JavaScript trong Chromium.
- `python scripts/check.py`: không liên kết nội bộ hỏng, không ảnh thiếu/trùng/không sử dụng.

## Kiểm tra riêng cho v5 — phân loại thư mục (29/10/2026)

- Đã chạy `python scripts/build.py` và `python scripts/check.py`: 18 trang HTML (17 trang sinh tự động và trang 404), 42 ảnh. Tất cả liên kết nội bộ HTML, ảnh, CSS, JavaScript và mục trong danh mục ảnh đều tồn tại.
- Đã kiểm tra về mặt mã nguồn việc sinh lại tất cả trang vào `html/`, giữ 2 trang vào chuẩn GitHub Pages (`index.html`, `404.html`) ở root.
- Đã cập nhật các liên kết từ trang chủ tới trang con, liên kết giữa trang con, liên kết bài báo lồng thư mục, preloads, favicon, ảnh và tài nguyên bên thứ ba.
- Kiểm tra JS trực tiếp trong Chromium trên môi trường thực hiện bị hạn chế truy cập file/HTTP (`ERR_BLOCKED_BY_ADMINISTRATOR`), vì vậy **chưa xác minh được tương tác thật bằng trình duyệt trong phiên này**. Trước khi xuất bản, cần kiểm thử lại menu mobile, bộ lọc ngành học, tìm kiếm tin, lightbox và form theo các kịch bản phần trên.
- Chú ý SEO/URL: khi chuyển từ bản v4 sang v5 trên website đang vận hành, phải xử lý URL cũ (redirect 301 nếu máy chủ hỗ trợ) và dựng lại sitemap/canonical.
