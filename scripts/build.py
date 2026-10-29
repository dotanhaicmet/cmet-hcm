#!/usr/bin/env python3
"""Generate deployable, SEO-ready HTML from shared templates + data/content.json.
Usage: python scripts/build.py [--site-url https://username.github.io/cmet/] [--noindex]
The output is committed as static HTML: GitHub Pages needs no Python build step.
"""
import argparse, html, json, pathlib, textwrap, urllib.parse, datetime, posixpath, re
from xml.sax.saxutils import escape as xml_esc
P = pathlib.Path(__file__).resolve().parents[1]
D=json.loads((P/'data/content.json').read_text(encoding='utf-8'))
MAJORS=D['majors']; NEWS=D['news']
F=lambda s: html.escape(str(s), quote=True)
parser=argparse.ArgumentParser()
parser.add_argument('--site-url',default='',help='Public deployment root URL for canonical links + sitemap')
parser.add_argument('--noindex',action='store_true',help='Recommended for review-only demo on GitHub Pages')
args=parser.parse_args()
SITE=args.site_url.rstrip('/')+'/' if args.site_url else ''
PAGES=[]

# Public HTML lives in html/. The two exceptions are mandatory GitHub Pages
# entrypoints: /index.html and /404.html. All paths remain relative so the site
# works at either a custom domain or username.github.io/repo/.
def target_path(old_slug):
    if old_slug in ('index.html', '404.html'):
        return old_slug
    if old_slug.endswith('.html'):
        return 'html/' + old_slug
    if old_slug.startswith('assets/images/'):
        return 'images/' + old_slug[len('assets/images/'):]
    if old_slug.startswith('assets/css/'):
        return 'css/' + old_slug[len('assets/css/'):]
    if old_slug.startswith('assets/js/'):
        return 'js/' + old_slug[len('assets/js/'):]
    if old_slug.startswith('assets/vendor/'):
        name = old_slug[len('assets/vendor/'):]
        return ('css/vendor/' if name.endswith('.css') else 'js/vendor/') + name
    return old_slug

URL_ATTR = re.compile(r'(?P<attr>\b(?:href|src|srcset|data-large)\s*=\s*)(?P<quote>["\'])(?P<url>.*?)(?P=quote)', re.I | re.S)
def relocate_links(document, old_slug):
    """Update all locally referenced HTML/media/styles/scripts when relocating pages."""
    new_slug = target_path(old_slug)
    def replace(match):
        value = match.group('url')
        if not value or value[0] in ('#', '/') or value.startswith(('data:', 'mailto:', 'tel:', 'javascript:', '//')):
            return match.group(0)
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme or not parsed.path:
            return match.group(0)
        old_target = posixpath.normpath(posixpath.join(posixpath.dirname(old_slug), parsed.path))
        if old_target.startswith('../'):
            raise ValueError(f'Out-of-root resource in {old_slug}: {value}')
        new_target = target_path(old_target)
        relative = posixpath.relpath(new_target, posixpath.dirname(new_slug) or '.')
        new_url = urllib.parse.urlunsplit(('', '', relative, parsed.query, parsed.fragment))
        return match.group('attr') + match.group('quote') + new_url + match.group('quote')
    return URL_ATTR.sub(replace, document)


# A single asset resolver keeps the generated HTML independent of folder layout.
# Edit this function only if asset families are moved in a later version.
def asset_url(root, name):
    name = str(name)
    if '.' not in pathlib.Path(name).name:
        name += '.webp'
    if name.startswith('course-'):
        folder = 'programs'
    elif name.startswith('partner-'):
        folder = 'partners'
    elif name.startswith('album-'):
        folder = 'gallery'
    elif name in ('brand.webp', 'emblem.webp', 'favicon.png'):
        folder = 'branding'
    elif name in ('hero.webp','hero-mobile.webp','promo-scholarship.webp',
                  'scholarship-ribbon.webp','official-banner.webp',
                  'scholarship-ribbon.gif','official-banner.gif'):
        folder = 'banners'
    elif name == 'campus-gate.webp':
        folder = 'campus'
    elif name == 'video-cover.webp':
        folder = 'media'
    elif name.startswith(('news-', 'student-')):
        folder = 'news'
    else:
        raise ValueError('Unclassified image asset: '+name)
    return f'{root}assets/images/{folder}/{name}'

def img(root,name,alt,cls='',lazy=True):
    return f'<img src="{F(asset_url(root,name))}" alt="{F(alt)}" class="{cls}" '+('loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"')+'>'

def animated_banner(root, kind, label, href):
    """Animated original GIF + still WebP for prefers-reduced-motion users."""
    return (f'<a class="banner-full media-zoom" href="{F(href)}" aria-label="{F(label)}">'
            f'<picture><source media="(prefers-reduced-motion: reduce)" '
            f'srcset="{F(asset_url(root,kind+".webp"))}">'
            f'{img(root,kind+".gif",label)}</picture></a>')

def layout(title,desc,body,slug='index.html',depth=0,schema=None):
    root='../'*depth
    if SITE:
        url=SITE+target_path(slug)
        canonical=f'<link rel="canonical" href="{F(url)}">'
        ogurl=f'<meta property="og:url" content="{F(url)}"><meta property="og:image" content="{F(SITE+target_path(asset_url("","hero.webp")))}">'
    else: canonical=ogurl=''
    structure=schema if schema is not None else {
      '@context':'https://schema.org','@type':'CollegeOrUniversity',
      'name':'Trường Cao đẳng Y Dược và Kinh tế Công nghệ (CMET)',
      'url':'https://cvn.edu.vn/','telephone':'+841900636365',
      'address':{'@type':'PostalAddress','streetAddress':'KM 15 Quốc lộ 5, thôn Trai Túc, xã Như Quỳnh','addressRegion':'Hưng Yên','addressCountry':'VN'}
    }
    ld=json.dumps(structure,ensure_ascii=False).replace('<','\\u003c')
    sections=[('Giới thiệu','gioi-thieu.html'),('Đào tạo','nganh-dao-tao.html'),('Tuyển sinh','tuyen-sinh.html'),('Hợp tác quốc tế','hop-tac-quoc-te.html'),('Hoạt động sinh viên','hoat-dong-sinh-vien.html')]
    quick=[('Tuyển dụng','tuyen-dung.html'),('Tin tức','tin-tuc.html'),('Liên hệ','lien-he.html'),('Thư viện','thu-vien.html'),('Đăng ký xét tuyển','tuyen-sinh.html#dang-ky')]
    quick_html=''.join(f'<a href="{root}{p}">{F(n)}</a>' for n,p in quick)
    nav=f'''<div class="nav-drop"><button type="button" aria-expanded="false" aria-haspopup="true">GIỚI THIỆU <span class="chevron">⌄</span></button><div class="submenu"><a href="{root}gioi-thieu.html">Giới thiệu nhà trường</a><a href="{root}gioi-thieu.html#co-so">Cơ sở đào tạo</a><a href="{root}thu-vien.html">Thư viện ảnh</a></div></div>
    <div class="nav-drop"><button type="button" aria-expanded="false" aria-haspopup="true">ĐÀO TẠO <span class="chevron">⌄</span></button><div class="submenu"><a href="{root}nganh-dao-tao.html">Các ngành đào tạo</a><a href="{root}nganh-dao-tao.html#y-duoc">Khối ngành Y Dược</a><a href="{root}nganh-dao-tao.html#kinh-te">Khối ngành Kinh tế</a><a href="{root}nganh-dao-tao.html#ngon-ngu">Khối ngành Ngôn ngữ</a></div></div>
    <a href="{root}tuyen-sinh.html">TUYỂN SINH</a><a href="{root}hop-tac-quoc-te.html">HỢP TÁC QUỐC TẾ</a>
    <div class="nav-drop"><button type="button" aria-expanded="false" aria-haspopup="true">HOẠT ĐỘNG SINH VIÊN <span class="chevron">⌄</span></button><div class="submenu"><a href="{root}hoat-dong-sinh-vien.html">Hoạt động sinh viên</a><a href="{root}tin-tuc.html">Tin tức</a></div></div>'''
    mobile=''.join(f'<a href="{root}{p}">{F(n)}</a>' for n,p in sections+[('Tin tức','tin-tuc.html'),('Thư viện','thu-vien.html'),('Liên hệ','lien-he.html')])
    header=f'''<header class="site-header"><div class="wrap"><a class="brand" href="{root}index.html" aria-label="CMET — Trang chủ">{img(root,'brand','Trường Cao đẳng Y Dược và Kinh tế Công nghệ CMET','',False)}</a><div class="quick-links">{quick_html}<a href="{root}en.html" lang="en" aria-label="English overview"><span class="flag">🇬🇧</span></a><a href="{root}index.html" lang="vi" aria-label="Tiếng Việt"><span class="flag">🇻🇳</span></a></div><div class="nav-backdrop"></div><nav class="desktop-nav" aria-label="Điều hướng chính">{nav}</nav><button class="mobile-toggle" id="mobile-toggle" type="button" aria-controls="mobile-nav" aria-expanded="false" aria-label="Mở menu">☰</button></div><nav id="mobile-nav" class="mobile-nav" aria-label="Điều hướng điện thoại">{mobile}</nav></header>'''
    footer=f'''<footer class="site-footer"><div class="wrap"><div class="footer-brand">{img(root,'emblem','Biểu trưng CMET')}<div><div class="footer-brand-sub">BỘ GIÁO DỤC VÀ ĐÀO TẠO</div><div class="footer-brand-main">TRƯỜNG CAO ĐẲNG Y DƯỢC VÀ KINH TẾ CÔNG NGHỆ</div><div class="footer-brand-en">College of Medicine, Pharmacy, Economics, Technology</div></div></div><div class="footer-grid"><div><h2>Kết nối với chúng tôi</h2><p>☎ <a href="tel:1900636365">1900.63.63.65</a> - <a href="tel:0566535999">0566.535.999</a></p><p>◉ Website: <a href="https://cvn.edu.vn/" target="_blank" rel="noopener noreferrer">https://cvn.edu.vn/</a></p><p><a href="https://www.youtube.com/watch?v=bbUowf_BKZg" target="_blank" rel="noopener noreferrer" aria-label="Kênh YouTube CMET">▶ YouTube CMET</a></p></div><div><h2>Cơ sở đào tạo</h2><p>⚑ Trụ sở chính: KM 15 Quốc lộ 5 (Hà Nội - Hải Phòng), thôn Trai Túc, xã Như Quỳnh, tỉnh Hưng Yên.</p><p>⚑ Hà Nội: Lô TH1, KĐT Cổ Nhuế, phường Nghĩa Đô, TP Hà Nội.</p><p>⚑ TP Hồ Chí Minh: Số 01 ĐHT 27, phường Đông Hưng Thuận, TP Hồ Chí Minh.</p></div><div><h2>Ngành đào tạo</h2><div class="footer-links"><a href="{root}nganh-dao-tao.html#y-duoc">✔ Ngành Y Dược</a><a href="{root}nganh-dao-tao.html#kinh-te">✔ Ngành Kinh tế</a><a href="{root}nganh-dao-tao.html#cong-nghe">✔ Ngành Công nghệ</a><a href="{root}nganh-dao-tao.html#ngon-ngu">✔ Ngành Ngôn ngữ</a></div></div><div><h2>Hệ đào tạo</h2><div class="footer-links"><a href="{root}tuyen-sinh.html">› Hệ chính quy</a><a href="{root}tuyen-sinh.html">› Hệ liên thông</a><a href="{root}tuyen-sinh.html">› Hệ từ xa</a><a href="{root}tuyen-sinh.html">› Hệ ngắn hạn</a></div></div></div><div class="footer-bottom">© CMET · Thông tin tuyển sinh, học bổng và chương trình đào tạo cần được xác nhận theo thông báo chính thức.</div></div></footer>'''
    floating='''<div class="float-actions" aria-label="Liên hệ nhanh"><a class="float-action zalo" href="https://zalo.me/0566535999" target="_blank" rel="noopener noreferrer" title="Tư vấn CMET qua Zalo" aria-label="Tư vấn CMET qua Zalo">Zalo</a><a class="float-action phone" href="tel:1900636365" title="Gọi 1900 63 63 65" aria-label="Gọi 1900 63 63 65">☎</a></div>'''
    doc=f'''<!doctype html><html lang="{'en' if slug=='en.html' else 'vi'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{F(desc)}"><meta name="robots" content="{'noindex,nofollow' if args.noindex else 'index,follow,max-image-preview:large'}"><meta name="theme-color" content="#10264d"><meta property="og:type" content="website"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="CMET"><meta property="og:title" content="{F(title)}"><meta property="og:description" content="{F(desc)}">{ogurl}{canonical}<title>{F(title)}</title><link rel="icon" type="image/png" href="{asset_url(root,"favicon.png")}"><link rel="preload" href="{root}assets/vendor/bootstrap.min.css" as="style"><link rel="stylesheet" href="{root}assets/vendor/bootstrap.min.css"><link rel="stylesheet" href="{root}assets/css/site.css"><script type="application/ld+json">{ld}</script><script src="{root}assets/vendor/jquery.min.js" defer></script><script src="{root}assets/vendor/bootstrap.bundle.min.js" defer></script><script src="{root}assets/js/config.js" defer></script><script src="{root}assets/js/site.js" defer></script></head><body><a class="sr-only" href="#noi-dung">Bỏ qua điều hướng</a>{header}<main id="noi-dung">{body}</main>{footer}{floating}</body></html>'''
    new_slug = target_path(slug)
    path=P/new_slug;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(relocate_links(doc, slug),encoding='utf-8');PAGES.append(new_slug)

def head(title,home=False):
    return '' if home else f'<div class="page-heading-band"><div class="wrap"><h1>{F(title)}</h1><div class="breadcrumbs"><a href="index.html">Trang chủ</a> / {F(title)}</div></div></div>'

def form_fragment(fid='home-form',root=''):
    options=''.join(f'<option value="{F(m["name"])}">{F(m["name"])}</option>' for m in MAJORS)
    return f'''<form class="consultation-form" id="{fid}" autocomplete="on"><label class="sr-only" for="{fid}-name">Họ và tên</label><input id="{fid}-name" name="fullname" autocomplete="name" maxlength="100" required placeholder="Họ và tên"><label class="sr-only" for="{fid}-phone">Số điện thoại</label><input id="{fid}-phone" type="tel" name="phone" inputmode="tel" autocomplete="tel" required maxlength="16" placeholder="Số điện thoại"><label class="sr-only" for="{fid}-major">Ngành quan tâm</label><select id="{fid}-major" name="major" required><option value="" selected disabled>Ngành</option>{options}</select><label class="sr-only" for="{fid}-campus">Cơ sở đào tạo</label><select id="{fid}-campus" name="campus" required><option value="" selected disabled>Cơ sở đào tạo</option><option>Hưng Yên</option><option>Hà Nội</option><option>TP Hồ Chí Minh</option></select><label class="form-check"><input class="form-check-input" type="checkbox" name="consent" value="yes" required> Tôi đồng ý cung cấp thông tin để được tư vấn tuyển sinh. <a href="{root}chinh-sach-bao-mat.html" style="color:inherit;text-decoration:underline">Chính sách bảo mật</a>.</label><button type="submit" class="primary-btn form-button">ĐĂNG KÝ XÉT TUYỂN</button><p class="form-note">Bạn có thể chuẩn bị phiếu qua email; cần nhấn Gửi trong ứng dụng thư để hoàn tất. Hệ thống hiện chưa tiếp nhận tự động.</p></form><div class="response-box" aria-live="polite"><strong class="response-title"></strong><pre class="response-summary"></pre><div class="response-actions"><button type="button" class="secondary-btn copy-summary">Sao chép phiếu</button><button type="button" class="secondary-btn download-summary">Tải phiếu .txt</button><a class="secondary-btn email-summary" style="display:none" href="#">Mở ứng dụng email</a><a class="primary-btn" href="tel:1900636365">Gọi hotline</a></div></div>'''

def course_cards(root=''):
    """Real photos with editable HTML captions—not screenshots of cards."""
    return '<div class="courses-grid">'+''.join(
        f'<a class="course-card" data-group="{F(m["group"])}" href="{root}nganh-dao-tao.html#{m["slug"]}" aria-label="Tìm hiểu ngành {F(m["name"])}">'
        +img(root,'course-'+m['slug'],'Hình minh họa ngành '+m['name'])
        +f'<span class="course-label">{F(m["name"])}</span></a>' for m in MAJORS
    )+'</div>'

def statistics_fragment():
    """All statistics are editable content; source is CMET's published graphic."""
    items=[('22','NGÀNH ĐÀO TẠO','graduation-cap'),('14','PHÒNG THỰC HÀNH','hospital'),
           ('98%','SINH VIÊN CÓ VIỆC','briefcase'),('300+','DOANH NGHIỆP, BỆNH VIỆN, NHÀ THUỐC LIÊN KẾT','heart')]
    blocks=''.join(f'<div class="stat-card"><span class="stat-symbol" aria-hidden="true">◆</span><strong>{val}</strong><span>{label}</span></div>' for val,label,_ in items)
    return '<div class="stats-panel" aria-label="Các số liệu được nhà trường công bố"><div class="stats-grid">'+blocks+'</div><div class="stats-location"><strong>03</strong><p><b>CƠ SỞ ĐÀO TẠO</b><span>Hưng Yên · Hà Nội · TP Hồ Chí Minh</span></p></div></div>'

def newslink(n,root=''):
    return f'{root}tin-tuc/{n["slug"]}.html'

def homepage():
    a=NEWS
    news_side=''.join(f'<a class="news-side-item" href="{newslink(n)}"><span class="news-thumb">{img("",n["image"],n["title"])}</span><div><h3>{F(n["title"])}</h3><p>{F(n["summary"])}</p></div></a>' for n in a[:3])
    cooperate=''.join(f'<a class="news-side-item" href="{newslink(n)}"><span class="news-thumb">{img("",n["image"],n["title"])}</span><div><h3>{F(n["title"])}</h3><p>{F(n["summary"])}</p></div></a>' for n in [a[0],a[4],a[1]])
    students=''.join(f'<a href="{newslink(n)}" class="student-card">{img("",n["image"],n["title"])}<div class="card-copy"><h3>{F(n["title"])}</h3><p>{F(n["summary"])}</p></div></a>' for n in [a[3],a[4],a[1]])
    album=''.join(f'<button type="button" data-large="{asset_url("",f"album-{i}.webp")}" aria-label="Xem ảnh số {i} CMET">{img("",f"album-{i}",f"Hình ảnh hoạt động CMET số {i}")}</button>' for i in range(1,6))
    partners=''.join(img('',f'partner-{i}',f'Logo đơn vị hợp tác {i}') for i in range(1,6))
    return f'''<section class="hero" aria-label="Tuyển sinh CMET 2026"><h1 class="sr-only">Trường Cao đẳng Y Dược và Kinh tế Công nghệ CMET – Tuyển sinh 2026</h1><picture><source media="(max-width:620px)" srcset="{asset_url("","hero-mobile.webp")}">{img('','hero','Thông tin tuyển sinh CMET 2026: khối Y Dược, Kinh tế, ngôn ngữ và kỹ thuật. Học bổng và thông tin đăng ký.','',False)}</picture><a class="hero-hit-area" href="#dang-ky" aria-label="Đến biểu mẫu đăng ký tư vấn tuyển sinh 2026"></a><div class="hero-mobile-cta"><a href="#dang-ky" class="primary-btn">ĐĂNG KÝ TƯ VẤN NGAY</a></div></section>
    <section class="admission-section" id="dang-ky"><div class="wrap"><div class="admission-grid admission-grid--home"><div class="admission-column admission-column--promo"><div class="admission-heading">ƯU ĐÃI TUYỂN SINH 2026</div><div class="scholarship-poster">{img('','promo-scholarship','Chính sách học bổng tuyển sinh CMET 2026, cơ hội tặng laptop')}</div><div class="admission-promo-footer"><p><strong>Khám phá ngành học phù hợp</strong>Tìm hiểu chương trình đào tạo và lựa chọn cơ sở học tập tại CMET.</p><div class="admission-promo-footer__actions"><a href="nganh-dao-tao.html">XEM CÁC NGÀNH ĐÀO TẠO <span aria-hidden="true">→</span></a><a href="lien-he.html">LIÊN HỆ TƯ VẤN <span aria-hidden="true">→</span></a></div></div></div><div class="admission-column admission-column--form"><div class="admission-heading">ĐĂNG KÝ TƯ VẤN MIỄN PHÍ</div><div class="admission-text"><p>Căn cứ theo kế hoạch đào tạo và tuyển sinh năm học 2026 – 2027, Trường Cao đẳng Y Dược và Kinh tế Công nghệ tuyển sinh cao đẳng chính quy trên toàn quốc:</p><ul><li>Tên trường: Cao đẳng Y Dược và Kinh tế Công nghệ</li><li>Ký hiệu trường: CMET</li><li>Đối tượng tuyển sinh: Tốt nghiệp THPT hoặc tương đương</li><li>Phương thức xét tuyển: Học bạ lớp 12 và điểm thi THPT Quốc gia 2026</li><li>Cơ sở đào tạo: Hưng Yên, Hà Nội, TP Hồ Chí Minh</li></ul><p><b>Dành 1 phút điền thông tin đăng ký để được nhận <strong>ƯU ĐÃI TUYỂN SINH</strong></b></p></div>{form_fragment()}</div></div></div></section>
    <section class="section" id="gioi-thieu"><div class="wrap"><div class="about-grid"><div><div class="about-left-title"><p class="lead-in">Bạn đã biết đến</p><h2>TRƯỜNG CAO ĐẲNG Y DƯỢC VÀ KINH TẾ CÔNG NGHỆ</h2></div>{img('','campus-gate','Cổng Trường Cao đẳng Y Dược và Kinh tế Công nghệ CMET','about-img')}</div><div>{statistics_fragment()}</div></div></div></section>
    <section class="section" style="padding-top:0"><div class="wrap"><p class="about-copy">Trường Cao đẳng Y Dược và Kinh tế Công nghệ (CMET) được thành lập năm 2010, đào tạo các lĩnh vực Y Dược – Kinh tế – Công nghệ. Nhà trường giới thiệu các cơ sở tại Hưng Yên, Hà Nội và TP Hồ Chí Minh, định hướng chú trọng thực hành và cơ hội nghề nghiệp cho sinh viên.</p><a class="video-big" href="https://www.youtube.com/watch?v=bbUowf_BKZg" target="_blank" rel="noopener noreferrer" aria-label="Mở kênh YouTube giới thiệu CMET">{img('','video-cover','Hình ảnh hoạt động tại trường CMET')}<span class="video-overlay"><span class="play-button">▶</span></span></a></div></section>
    <section class="section section-muted" id="nganh-dao-tao"><div class="wrap"><h2 class="section-heading">CÁC NGÀNH ĐÀO TẠO</h2>{course_cards()}{animated_banner("","scholarship-ribbon","Học bổng tuyển sinh CMET, miễn giảm đến 70–100% học phí","tuyen-sinh.html#dang-ky")}</div></section>
    <section class="section"><div class="wrap"><h2 class="section-heading">TIN TUYỂN SINH</h2><div class="news-layout"><a class="feature-card" href="{newslink(a[0])}">{img('','news-d2',a[0]['title'])}<span class="feature-caption">{F(a[0]['title'])}</span></a><div class="news-side">{news_side}</div></div></div></section>
    <section class="section section-muted"><div class="wrap"><h2 class="section-heading">HỢP TÁC DOANH NGHIỆP</h2><div class="news-layout"><a class="feature-card" href="{newslink(a[0])}">{img('','news-d2',a[0]['title'])}<span class="feature-caption">{F(a[0]['title'])}</span></a><div class="news-side">{cooperate}</div></div>{animated_banner("","official-banner","Thông tin tuyển sinh cao đẳng chính quy CMET năm 2026","tuyen-sinh.html")}</div></section>
    <section class="section section-muted"><div class="wrap"><h2 class="section-heading">HOẠT ĐỘNG SINH VIÊN</h2><div class="student-cards">{students}</div></div></section>
    <section class="section"><div class="wrap"><div class="media-grid"><div><h2 class="section-heading">VIDEO GIỚI THIỆU TRƯỜNG</h2><a class="video-big" href="https://www.youtube.com/watch?v=bbUowf_BKZg" target="_blank" rel="noopener noreferrer" aria-label="Mở video giới thiệu CMET trên YouTube">{img('','video-cover','Hình ảnh CMET – xem video giới thiệu trường')}<span class="video-overlay"><span class="play-button">▶</span></span></a></div><div><h2 class="section-heading">ALBUM ẢNH</h2><div class="album-grid">{album}</div></div></div></div></section>
    <section class="section section-muted"><div class="wrap"><h2 class="section-heading">HỢP TÁC TRƯỜNG VÀ DOANH NGHIỆP</h2><div class="partner-grid">{partners}</div></div></section>
    <dialog class="lightbox" id="image-lightbox" aria-label="Xem ảnh phóng to"><button type="button" id="close-lightbox" aria-label="Đóng ảnh">✕ Đóng</button><img id="lightbox-image" src="{asset_url("","album-1.webp")}" alt="Ảnh CMET"></dialog>'''

# homepage
layout('CMET | Trường Cao đẳng Y Dược và Kinh tế Công nghệ – Tuyển sinh 2026',
'Trang thông tin CMET: tuyển sinh cao đẳng 2026, các ngành Y Dược, Kinh tế, Công nghệ, Ngoại ngữ, học bổng và tư vấn xét tuyển.',homepage())

layout('Giới thiệu Trường Cao đẳng Y Dược và Kinh tế Công nghệ | CMET',
'Khám phá Trường Cao đẳng Y Dược và Kinh tế Công nghệ, cơ sở đào tạo, ngành học và hoạt động CMET.',
head('Giới thiệu nhà trường')+f'''<section class="section page-content"><div class="wrap"><div class="about-grid"><div><h2 class="section-heading">VỀ CMET</h2><p>Trường Cao đẳng Y Dược và Kinh tế Công nghệ (CMET) được giới thiệu thành lập năm 2010; nhà trường định hướng đào tạo gắn kiến thức với thực hành và nhu cầu nhân lực.</p><p>CMET cung cấp thông tin tuyển sinh các khối ngành Y Dược, Kinh tế, Công nghệ và Ngôn ngữ.</p>{img('','campus-gate','Cổng trường CMET','about-img')}</div><div>{statistics_fragment()}</div></div><div class="content-prose" id="co-so"><h2>Hệ thống cơ sở đào tạo</h2><p><strong>Hưng Yên:</strong> KM 15 Quốc lộ 5, thôn Trai Túc, xã Như Quỳnh, tỉnh Hưng Yên.</p><p><strong>Hà Nội:</strong> Lô TH1, Khu đô thị Cổ Nhuế, phường Nghĩa Đô, TP Hà Nội.</p><p><strong>TP Hồ Chí Minh:</strong> Số 01 ĐHT 27, phường Đông Hưng Thuận, TP Hồ Chí Minh.</p><p><a href="lien-he.html" class="primary-btn">Liên hệ nhà trường</a></p></div></div></section>''','gioi-thieu.html')

# majors page filters and accessible text details
filter_buttons=''.join(f'<button type="button" class="filter-pill {"active" if i==0 else ""}" data-group="{F(group)}" aria-pressed="{"true" if i==0 else "false"}">{F(group)}</button>' for i,group in enumerate(['Tất cả','Y Dược','Kinh tế','Công nghệ','Ngôn ngữ']))
details=''.join(f'<article class="course-detail" id="{m["slug"]}" data-group="{F(m["group"])}"><span class="tag">{F(m["group"])}</span><h3>{F(m["name"])}</h3><p>{F(m["description"])}</p><a href="tuyen-sinh.html#dang-ky">Đăng ký tư vấn ngành này →</a></article>' for m in MAJORS)
layout('Các ngành đào tạo tại CMET | Y Dược – Kinh tế – Công nghệ – Ngôn ngữ',
'Tìm hiểu danh sách các ngành đào tạo CMET: Y sĩ đa khoa, Điều dưỡng, Dược, Kế toán, Marketing, CNTT và các ngành ngôn ngữ.',
head('Các ngành đào tạo')+f'<section class="section page-content"><div class="wrap"><h2 class="section-heading" id="y-duoc">KHÁM PHÁ CHƯƠNG TRÌNH ĐÀO TẠO</h2><p>Chọn lĩnh vực quan tâm để lọc ngành. Thông tin chi tiết về chương trình, chỉ tiêu và học phí cần đối chiếu với thông báo chính thức của nhà trường.</p><div class="category-controls" role="group" aria-label="Lọc ngành học">{filter_buttons}</div>{course_cards()}<div class="course-detail-list">{details}</div><div id="kinh-te"></div><div id="cong-nghe"></div><div id="ngon-ngu"></div></div></section>','nganh-dao-tao.html')

layout('Thông tin tuyển sinh CMET 2026 – 2027 | Đăng ký tư vấn',
'Thông tin tuyển sinh Cao đẳng CMET năm học 2026–2027: đối tượng, phương thức xét tuyển, ngành học, cơ sở đào tạo và tư vấn.',
head('Thông tin tuyển sinh 2026')+f'''<section class="section page-content"><div class="wrap"><div class="admission-grid"><div style="color:#1c2f4b"><h2 class="section-heading">TUYỂN SINH CAO ĐẲNG CHÍNH QUY</h2>{img('','promo-scholarship','Học bổng, ưu đãi tuyển sinh năm 2026')}<div class="content-prose"><h2>Thông tin tuyển sinh</h2><ul><li>Đối tượng: tốt nghiệp THPT hoặc tương đương.</li><li>Phương thức: xét học bạ lớp 12 và điểm thi tốt nghiệp THPT 2026.</li><li>Cơ sở được giới thiệu: Hưng Yên, Hà Nội, TP Hồ Chí Minh.</li><li>Ngành đào tạo: <a href="nganh-dao-tao.html">Xem danh sách ngành học</a>.</li></ul><p class="disclosure-note">Các khoản học bổng, điều kiện xét tuyển và quyền lợi theo thông báo tuyển sinh chính thức, không tự động được đảm bảo khi gửi phiếu tư vấn.</p></div></div><div id="dang-ky"><h2 class="section-heading">ĐĂNG KÝ TƯ VẤN MIỄN PHÍ</h2>{form_fragment('admissions-form')}<p>Hotline: <a href="tel:1900636365">1900 63 63 65</a>.</p></div></div></div></section>''','tuyen-sinh.html')

cards=''.join(f'<a href="{newslink(n)}" class="article-card">{img("",n["image"],n["title"])}<div class="card-body"><span class="tag">{F(n["tag"])}</span><h2>{F(n["title"])}</h2><p>{F(n["summary"])}</p><span>Đọc tiếp →</span></div></a>' for n in NEWS)
layout('Tin tức tuyển sinh và hoạt động CMET',
'Tin tuyển sinh CMET, hoạt động sinh viên, sự kiện và hợp tác doanh nghiệp năm 2026.',
head('Tin tức và sự kiện')+f'<section class="section page-content"><div class="wrap"><label for="news-search" class="form-label">Tìm kiếm tin tức</label><div><input id="news-search" class="search-field" type="search" placeholder="Nhập từ khóa, ví dụ: tuyển sinh..." autocomplete="off"></div><div class="article-grid">{cards}</div><p class="news-search-empty" id="no-news-results">Không có bài viết phù hợp.</p></div></section>','tin-tuc.html')

layout('Hợp tác quốc tế và du học Hàn Quốc D2-6 | CMET',
'Thông tin hợp tác quốc tế, chương trình trao đổi sinh viên và du học Hàn Quốc D2-6 của CMET.',
head('Hợp tác quốc tế')+f'''<section class="section page-content"><div class="wrap"><div class="about-grid"><div>{img('','news-d2','Thư mời hợp tác phát triển mạng lưới du học Hàn Quốc D2-6','about-img')}</div><div class="content-prose"><h2 class="section-heading">KẾT NỐI VÀ HỢP TÁC</h2><p>Trường Cao đẳng Y Dược và Kinh tế Công nghệ công bố các hoạt động liên quan tới mạng lưới du học Hàn Quốc theo diện D2-6 và trao đổi sinh viên.</p><p>Đối tác hoặc sinh viên có nhu cầu tìm hiểu về điều kiện, thời gian, quyền lợi và hồ sơ cần liên hệ trực tiếp với nhà trường để nhận văn bản cập nhật.</p><p><a href="{newslink(NEWS[0])}" class="primary-btn">Đọc thông tin hợp tác</a></p><p><a href="lien-he.html">Liên hệ tư vấn chương trình →</a></p></div></div></div></section>''','hop-tac-quoc-te.html')

layout('Hoạt động sinh viên CMET – Tin tức và hình ảnh',
'Hoạt động sinh viên, nhà trường, chương trình tiếp sức mùa thi và kết nối doanh nghiệp tại CMET.',
head('Hoạt động sinh viên')+f'<section class="section page-content"><div class="wrap"><div class="student-cards">'+''.join(f'<a href="{newslink(n)}" class="student-card">{img("",n["image"],n["title"])}<div class="card-copy"><h3>{F(n["title"])}</h3><p>{F(n["summary"])}</p></div></a>' for n in [NEWS[3],NEWS[4],NEWS[1]])+'</div><p style="margin-top:25px"><a href="thu-vien.html">Xem thư viện hình ảnh →</a></p></div></section>','hoat-dong-sinh-vien.html')

album=''.join(f'<button type="button" data-large="{asset_url("",f"album-{i}.webp")}" aria-label="Xem ảnh số {i}">{img("",f"album-{i}",f"Album CMET số {i}")}</button>' for i in range(1,6))
layout('Thư viện ảnh và video CMET',
'Thư viện ảnh sinh viên, hoạt động đào tạo và video giới thiệu Trường Cao đẳng Y Dược và Kinh tế Công nghệ.',
head('Thư viện ảnh và video')+f'<section class="section page-content"><div class="wrap"><div class="media-grid"><div><h2 class="section-heading">VIDEO GIỚI THIỆU</h2><a class="video-big" href="https://www.youtube.com/watch?v=bbUowf_BKZg" target="_blank" rel="noopener noreferrer">{img("","video-cover","Video giới thiệu trường CMET")}</a></div><div><h2 class="section-heading">ALBUM ẢNH</h2><div class="album-grid">{album}</div></div></div></div></section><dialog class="lightbox" id="image-lightbox" aria-label="Xem ảnh phóng to"><button id="close-lightbox" type="button">✕ Đóng</button><img id="lightbox-image" src="{asset_url("","album-1.webp")}" alt="Ảnh CMET"></dialog>','thu-vien.html')

layout('Liên hệ Trường Cao đẳng Y Dược và Kinh tế Công nghệ | CMET',
'Thông tin liên hệ, hotline, các cơ sở đào tạo CMET tại Hưng Yên, Hà Nội và TP Hồ Chí Minh.',
head('Liên hệ CMET')+f'''<section class="section page-content"><div class="wrap"><div class="contact-blocks"><div class="contact-block"><h2>Trụ sở Hưng Yên</h2><p>KM 15 Quốc lộ 5, thôn Trai Túc, xã Như Quỳnh, tỉnh Hưng Yên.</p><a href="https://www.google.com/maps/search/?api=1&query=KM+15+Quoc+lo+5+Nhu+Quynh+Hung+Yen" target="_blank" rel="noopener noreferrer">Xem bản đồ →</a></div><div class="contact-block"><h2>Cơ sở Hà Nội</h2><p>Lô TH1, Khu đô thị Cổ Nhuế, phường Nghĩa Đô, TP Hà Nội.</p><a href="https://www.google.com/maps/search/?api=1&query=Lo+TH1+Khu+do+thi+Co+Nhue+Ha+Noi" target="_blank" rel="noopener noreferrer">Xem bản đồ →</a></div><div class="contact-block"><h2>Cơ sở TP Hồ Chí Minh</h2><p>Số 01 ĐHT 27, phường Đông Hưng Thuận, TP Hồ Chí Minh.</p><a href="https://www.google.com/maps/search/?api=1&query=1+Dong+Hung+Thuan+27+Ho+Chi+Minh" target="_blank" rel="noopener noreferrer">Xem bản đồ →</a></div></div><div class="about-grid" style="margin-top:38px"><div class="content-prose"><h2 class="section-heading">KẾT NỐI VỚI CHÚNG TÔI</h2><p><strong>Hotline:</strong> <a href="tel:1900636365">1900.63.63.65</a> – <a href="tel:0566535999">0566.535.999</a></p><p><strong>Website gốc:</strong> <a href="https://cvn.edu.vn/">https://cvn.edu.vn/</a></p><p>Cần hỗ trợ đăng ký xét tuyển hoặc tìm hiểu ngành học? Vui lòng liên hệ hotline chính thức của nhà trường.</p></div><div><h2 class="section-heading">ĐĂNG KÝ NHẬN TƯ VẤN</h2>{form_fragment('contact-form')}</div></div></div></section>''','lien-he.html')

privacy='''<section class="section page-content"><div class="wrap content-prose"><p>Đây là bản dựng thử để báo cáo kết quả. Khi chưa cấu hình API nhận biểu mẫu, thông tin nhập vào không được tự động gửi tới trường và không được lưu trong bộ nhớ trình duyệt.</p><h2>Mục đích sử dụng</h2><p>Phiếu tư vấn (khi được tích hợp máy chủ chính thức) chỉ nhằm liên hệ, tư vấn ngành học, điều kiện và thủ tục tuyển sinh theo yêu cầu của người đăng ký.</p><h2>Dữ liệu và quyền của người đăng ký</h2><p>Giao diện thu thập họ tên, điện thoại, ngành quan tâm và cơ sở đào tạo với sự đồng ý của người điền. Quy trình lưu trữ, thời hạn lưu, đơn vị xử lý và yêu cầu xóa dữ liệu cần được nhà trường phê duyệt và hoàn thiện trước khi kích hoạt tiếp nhận trực tuyến.</p><p>Liên hệ <a href="tel:1900636365">1900 63 63 65</a> để được hỗ trợ.</p></div></section>'''
layout('Chính sách bảo mật dữ liệu – Website CMET',
'Thông tin bảo mật, mục đích và phạm vi dữ liệu của biểu mẫu tư vấn tuyển sinh CMET.',head('Chính sách bảo mật')+privacy,'chinh-sach-bao-mat.html')


layout('CMET | College of Medicine, Pharmacy, Economics and Technology',
'English overview of CMET college in Vietnam: training programs, admissions 2026, campuses and contact.',
"""<div class="page-heading-band"><div class="wrap"><h1>Welcome to CMET</h1><div class="breadcrumbs"><a href="index.html">Tiếng Việt</a> / English overview</div></div></div><section class="section page-content"><div class="wrap"><div class="about-grid"><div><h2 class="section-heading">ABOUT THE COLLEGE</h2><p>The College of Medicine, Pharmacy, Economics and Technology (CMET) provides vocational college programs in health, business, technology and languages.</p><p>Campuses listed by the college are in Hung Yen, Ha Noi and Ho Chi Minh City.</p><p>Admissions inquiries for 2026: <a href="tel:1900636365">1900 63 63 65</a>.</p><p><a class="primary-btn" href="tuyen-sinh.html">Admissions information (Vietnamese)</a></p></div><div>"""+img('','campus-gate','CMET college campus in Vietnam')+"""</div></div><h2 class="section-heading" style="margin-top:45px">PROGRAMS</h2><p>Medicine and Pharmacy · Nursing · Traditional Medicine · Accounting · Marketing · Information Technology · English · Chinese · Korean · Japanese</p><p><a href="nganh-dao-tao.html">Explore training programs (Vietnamese) →</a></p></div></section>""",'en.html')

layout('Thông tin tuyển dụng | CMET',
'Thông tin và kênh liên hệ tuyển dụng của Trường Cao đẳng Y Dược và Kinh tế Công nghệ.',
head('Tuyển dụng')+'''<section class="section page-content"><div class="wrap content-prose"><h2 class="section-heading">CƠ HỘI LÀM VIỆC VÀ HỢP TÁC</h2><p>CMET tiếp nhận các yêu cầu tìm hiểu về tuyển dụng và hợp tác. Danh sách vị trí đang mở và điều kiện ứng tuyển cần được xác nhận trực tiếp với nhà trường trước khi nộp hồ sơ.</p><p><b>Liên hệ:</b> <a href="mailto:phongtstt.cmet@gmail.com">phongtstt.cmet@gmail.com</a> · <a href="tel:0566535999">0566 535 999</a>.</p><p><a href="lien-he.html" class="primary-btn">Thông tin liên hệ</a></p></div></section>''','tuyen-dung.html')

# Miniature standalone stories with grounded short summaries; do not invent article contents.
for n in NEWS:
    article_slug='tin-tuc/'+n['slug']+'.html'
    im=img('../',n['image'],n['title'],'article-image')
    article_body=f'''<div class="page-heading-band"><div class="wrap"><h1>{F(n['title'])}</h1><div class="breadcrumbs"><a href="../index.html">Trang chủ</a> / <a href="../tin-tuc.html">Tin tức</a> / {F(n['tag'])}</div></div></div><section class="section page-content"><article class="wrap content-prose" style="max-width:970px"><p class="article-meta">CMET · {F(n['tag'])}</p><p class="lead">{F(n['summary'])}</p>{im}<h2>Thông tin sự kiện</h2><p>{F(n['summary'])}</p><p>Trang tóm tắt sử dụng hình ảnh gốc và thông tin từ tư liệu website do đơn vị cung cấp. Bản toàn văn, tài liệu liên quan và thời điểm công bố cần được bổ sung từ hồ sơ chính thức của CMET.</p><p><a href="../tin-tuc.html">← Trở lại tin tức</a> &nbsp; <a href="../lien-he.html">Liên hệ nhà trường →</a></p></article></section>'''
    layout(n['title']+' | CMET',n['summary'],article_body,article_slug,1,{
        '@context':'https://schema.org','@type':'Article', 'headline':n['title'],
        'description':n['summary'], 'publisher':{'@type':'Organization','name':'CMET','url':'https://cvn.edu.vn/'}
    })

# Do not leave old generated URL copies behind after refactoring.
for slug in PAGES:
    legacy = slug.removeprefix('html/')
    if legacy != slug:
        (P / legacy).unlink(missing_ok=True)
# Former article directory is only removed when empty (never remove unrelated files).
legacy_news = P / 'tin-tuc'
if legacy_news.exists() and not any(legacy_news.iterdir()):
    legacy_news.rmdir()

# sitemap only with actual deployment URL. Relative URLs are intentionally not used.
if SITE:
    paths=''.join('<url><loc>'+xml_esc(SITE+p)+'</loc><changefreq>monthly</changefreq></url>' for p in PAGES)
    (P/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+paths+'</urlset>',encoding='utf-8')
    (P/'robots.txt').write_text('User-agent: *\n'+('Disallow: /\n' if args.noindex else 'Allow: /\nSitemap: '+SITE+'sitemap.xml\n'),encoding='utf-8')
else:
    (P/'sitemap.xml').unlink(missing_ok=True)
    (P/'robots.txt').write_text('User-agent: *\n'+('Disallow: /\n' if args.noindex else 'Allow: /\n') ,encoding='utf-8')
print('Built',len(PAGES),'HTML pages',f'with sitemap for {SITE}' if SITE else '(sitemap waiting for deployment URL)')
