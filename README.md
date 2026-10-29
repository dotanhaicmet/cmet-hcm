# CMET Website — v5: phân loại thư mục và đồng bộ hệ thống sinh trang

Bản v5 **chỉ tái cấu trúc thư mục**, giữ nguyên nội dung, bố cục, hình ảnh, CSS và JavaScript từ bản v4 do người dùng cung cấp. Trang tĩnh hoạt động với GitHub Pages hoặc các máy chủ tĩnh khác; không cần Python trong lúc người dùng truy cập.

## Sơ đồ thư mục chuẩn

```text
CMET-Website-Organized-v5/
├── index.html                  # Trang chủ; BẮT BUỘC ở gốc cho GitHub Pages
├── 404.html                    # Trang báo lỗi; GitHub Pages đọc từ gốc
├── html/                       # Toàn bộ trang nội dung HTML
│   ├── gioi-thieu.html
│   ├── nganh-dao-tao.html
│   ├── tuyen-sinh.html
│   ├── tin-tuc.html
│   ├── en.html
│   ├── ...
│   └── tin-tuc/               # 5 bài viết chi tiết
├── css/
│   ├── site.css                # Định dạng giao diện CMET
│   └── vendor/bootstrap.min.css
├── js/
│   ├── config.js              # Cấu hình public; KHÔNG lưu mật khẩu
│   ├── site.js                # Menu, bộ lọc, tìm kiếm, form, lightbox
│   └── vendor/                # jQuery & Bootstrap JS
├── images/                     # 42 ảnh, chia theo 8 nhóm chủ đề
│   ├── banners/  branding/  campus/  gallery/
│   └── media/  news/  partners/  programs/
├── data/
│   ├── content.json            # Nguồn dữ liệu ngành học / tin tức
│   └── asset-sources.json      # Danh mục xuất xứ & vị trí hình ảnh
├── scripts/
│   ├── build.py                # Sinh tất cả HTML theo cấu trúc v5
│   └── check.py                # Kiểm tra nội bộ & toàn vẹn tài nguyên
├── docs/                       # Hướng dẫn triển khai, QA, tích hợp form
├── .gitignore  .nojekyll
├── robots.txt
└── THIRD_PARTY_NOTICES.md
```

**Giải thích hai ngoại lệ:** GitHub Pages chọn `index.html` ở thư mục gốc làm trang chủ và đọc `404.html` ở gốc làm trang lỗi. Di chuyển hai tệp này vào `html/` sẽ ảnh hưởng cách triển khai hiện tại. Các trang thông tin khác đều nằm trong `html/`.

## Chạy thử

Từ thư mục gốc (ngang cấp `index.html`):

```bash
python -m http.server 8000
```

Mở <http://localhost:8000/>. Bạn cũng có thể mở trực tiếp `index.html` để xem bản tĩnh (nên dùng HTTP server khi kiểm thử). Bootstrap 5.1.1 và jQuery 3.6.1 được lưu cục bộ trong `css/vendor` và `js/vendor`; không phụ thuộc CDN.

## Quy trình cập nhật đúng cách

1. **Thay đổi ngành đào tạo, danh sách tin tức:** sửa `data/content.json`.
2. **Ảnh:** đặt trong nhóm tương ứng ở `images/`; giữ `data/asset-sources.json` đồng bộ.
3. **Giao diện:** sửa `css/site.css`; **tương tác:** sửa `js/site.js`; **địa chỉ email/API:** sửa `js/config.js`.
4. **HTML, menu, các mẫu trang:** sửa `scripts/build.py` (các file HTML là sản phẩm được sinh, có thể bị ghi đè).
5. Chạy lần lượt:

```bash
python scripts/build.py
python scripts/check.py
```

`scripts/build.py` tự chuyển đường dẫn HTML/ảnh/CSS/JS theo vị trí mới, và sinh đủ trang con cùng các tin tức. **Không** dời file đã sinh thủ công rồi tiếp tục dùng bộ sinh cũ: sẽ phá liên kết ở lần build tiếp theo.

## URL cũ và URL mới — cần đọc trước khi deploy

- Trang chủ: `index.html` → `index.html` (không đổi).
- Ví dụ: `tuyen-sinh.html` → `html/tuyen-sinh.html`.
- Ví dụ bài viết: `tin-tuc/bo-nhiem-can-bo-quan-ly.html` → `html/tin-tuc/bo-nhiem-can-bo-quan-ly.html`.
- Ví dụ tệp: `assets/css/site.css` → `css/site.css`; `assets/js/site.js` → `js/site.js`; `assets/images/...` → `images/...`.

**Quan trọng:** Nếu bản v4 đã công khai với các liên kết URL cũ được chia sẻ/lập chỉ mục, việc đổi đường dẫn sẽ tạo URL 404 trên các link cũ. Cần cấu hình redirect HTTP 301 từ đường dẫn cũ sang mới trên hosting có hỗ trợ, hoặc có chiến lược giữ URL cũ trước khi thay thế website đang hoạt động. **GitHub Pages không hỗ trợ quy tắc redirect 301 phía máy chủ.** Bản v5 ưu tiên cấu trúc thư mục rõ ràng theo yêu cầu, không tự tạo thêm các trang HTML chuyển hướng ở root.

## Triển khai GitHub Pages

1. Tải nội dung bên **trong** `CMET-Website-Organized-v5` lên nhánh `main` (đảm bảo `index.html`, `html/`, `css/`, `js/`, `images/` cùng cấp).
2. Vào `Settings → Pages → Build and deployment → Deploy from a branch → main → /(root)`.
3. Khi biết URL thực tế, sinh lại trước khi commit:

```bash
python scripts/build.py --site-url https://TEN-TAI-KHOAN.github.io/TEN-REPO/
python scripts/check.py
```

Công cụ sẽ sinh canonical URL và sitemap theo đường dẫn mới. Dùng `--noindex` cho site demo nội bộ. Chỉ cấu hình `CNAME` hoặc canonical của `cvn.edu.vn` nếu có quyền quản trị tên miền/DNS.

## Biểu mẫu tư vấn — tình trạng hiện tại

`js/config.js` cho phép cấu hình `formEndpoint`. Khi chưa có API, form chỉ tạo phiếu và liên kết email; người dùng phải mở ứng dụng email rồi bấm Gửi. Khi tích hợp backend HTTPS, xem `docs/FORM-INTEGRATION.md`. **GitHub Pages không lưu dữ liệu hồ sơ, không hỗ trợ PHP và không chạy CSDL.**

## Dữ liệu và phạm vi kiểm chứng

- Bộ ảnh, banner động và nội dung v4 giữ nguyên; `data/asset-sources.json` ghi lại nguồn gốc của hình ảnh. Có 42 tài nguyên hình ảnh vật lý.
- Thông tin tuyển sinh, học phí, ngành đào tạo, chỉ tiêu, tỷ lệ việc làm và thông tin liên hệ cần nhà trường kiểm duyệt trước khi xuất bản chính thức.
- Tính năng form gửi trực tiếp tới máy chủ chỉ hoạt động sau khi có API thật. `scripts/check.py` kiểm tra liên kết và tài nguyên, không thay thế kiểm thử thiết bị/nghiệm thu production.

---

## Những thay đổi của v3 (so với v2)

- Thay hai banner tĩnh bằng GIF **gốc** trích xuất từ RAR: học bổng (`gif-hoc-bong-1.gif`) và thông tin tuyển sinh (`thong-tin-tuyen-sinh-1.gif`); bảo lưu ảnh WebP có sẵn để hỗ trợ chế độ giảm chuyển động. Không sao chép RAR hay những file GIF không sử dụng vào project.
- Zoom ảnh khi rê chuột/bàn phím, giữ ảnh được cắt trong khung, không làm xô lệch lưới.
- Sửa khoảng trắng dưới danh sách bên phải của hai khối tin bằng CSS Grid và khung thumbnail có vị trí xác định; responsive trả về chiều cao tự nhiên.
- Sửa font tên trường ở footer bằng `Segoe UI, Arial, sans-serif`, trọng lượng 700; chữ tiếng Việt hiển thị đúng.
- Sắp lại hình vào 8 nhóm trong `images/`; các HTML được **sinh lại hoàn toàn** từ `scripts/build.py`, không chỉnh tay một bản nhưng bỏ sót các trang còn lại.
- Đã thử desktop 1650px, mobile 390px bằng Chromium, không lỗi JavaScript/tràn ngang; kiểm tra hover zoom và bằng chứng GIF được tải (xem `docs/QA.md`).

**Lưu ý phiên bản v5**: các trang nội dung đã chuyển vào `html/` thay vì thư mục gốc; ngoại lệ `index.html` và `404.html` là do yêu cầu điểm vào của GitHub Pages. Trên mỗi đợt phát hành, luôn chạy `python scripts/build.py` rồi `python scripts/check.py`.

## Kiểm tra

```bash
python scripts/check.py
```

Chi tiết tại `docs/QA.md`. Xem `THIRD_PARTY_NOTICES.md` về Bootstrap và jQuery.


## Cập nhật v4 — Cân đối khối tuyển sinh

- Trang chủ dùng lớp `admission-grid--home` và 2 cột `admission-column` để 2 tiêu đề và phần cuối cột căn hàng ở màn hình desktop (>=1200px).
- Giữ poster học bổng đúng tỷ lệ (không crop/kéo giãn); vùng bên dưới là nội dung HTML độc lập với 2 liên kết thực sang ngành học và liên hệ.
- Dưới 1200px, chuyển sang 1 cột để tránh bó hẹp biểu mẫu; mobile tự xếp dọc. Thay đổi chỉ áp dụng trang chủ, không thay layout trang tuyển sinh chi tiết.
- Bố cục đã đối chiếu bằng Chromium ở 1650, 1366, 1150 và 390px, không tràn ngang hoặc lỗi JavaScript được ghi nhận; link và tài nguyên được `scripts/check.py` xác nhận.
# cmet-hcm
