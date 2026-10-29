/* CMET — progressive enhancement: không yêu cầu backend/SPA. jQuery 3.6.1. */
(function ($) {
  'use strict';
  const config = window.CMET_CONFIG || {};
  const $mobileNav = $('#mobile-nav');
  $('#mobile-toggle').on('click', function () {
    const opened = !$mobileNav.hasClass('open');
    $mobileNav.toggleClass('open', opened);
    $(this).attr('aria-expanded', opened).attr('aria-label', opened ? 'Đóng menu' : 'Mở menu');
  });
  $mobileNav.on('click', 'a', function () { $mobileNav.removeClass('open'); $('#mobile-toggle').attr('aria-expanded', 'false'); });
  $('.nav-drop > button').on('click', function (event) {
    event.stopPropagation();
    const $parent = $(this).parent();
    const next = !$parent.hasClass('open');
    $('.nav-drop').removeClass('open').find('>button').attr('aria-expanded', 'false');
    $parent.toggleClass('open', next);
    $(this).attr('aria-expanded', next);
  });
  $(document).on('click', function () { $('.nav-drop').removeClass('open').find('>button').attr('aria-expanded', 'false'); });
  $(document).on('keydown', function (e) { if (e.key === 'Escape') { $('.nav-drop').removeClass('open'); $mobileNav.removeClass('open'); $('#mobile-toggle').attr('aria-expanded', 'false'); } });

  $('.filter-pill').on('click', function () {
    const group = $(this).data('group');
    $('.filter-pill').removeClass('active').attr('aria-pressed', 'false');
    $(this).addClass('active').attr('aria-pressed', 'true');
    $('.course-card, .course-detail').each(function () {
      const show = group === 'Tất cả' || $(this).data('group') === group;
      $(this).prop('hidden', !show).toggle(show);
    });
  });

  // Khi mở #y-duoc / #kinh-te / #cong-nghe / #ngon-ngu từ menu/footer,
  // áp dụng chính bộ lọc tương ứng thay vì chỉ cuộn xuống cuối trang.
  const groupsByAnchor = { 'y-duoc': 'Y Dược', 'kinh-te': 'Kinh tế',
    'cong-nghe': 'Công nghệ', 'ngon-ngu': 'Ngôn ngữ' };
  const selectedGroup = groupsByAnchor[(window.location.hash || '').slice(1)];
  if (selectedGroup) {
    $('.filter-pill').filter(function () {return $(this).data('group') === selectedGroup;}).trigger('click');
  }

  // Tìm kiếm trên dữ liệu đã kết xuất thành HTML: không cần API hoặc fetch().
  function norm(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/đ/g, 'd'); }
  $('#news-search').on('input', function () {
    const needle = norm(this.value.trim()); let count = 0;
    $('.article-card').each(function () {
      const show = norm($(this).text()).includes(needle);
      $(this).toggle(show); if (show) count++;
    });
    $('#no-news-results').toggle(count === 0);
  });

  // Native dialog + lightbox accessible by keyboard. Works in GitHub Pages.
  const dialog = document.getElementById('image-lightbox');
  if (dialog) {
    $('.album-grid button').on('click', function () {
      $('#lightbox-image').attr('src', $(this).data('large')).attr('alt', $(this).find('img').attr('alt') || 'Ảnh CMET');
      if (dialog.showModal) dialog.showModal();
    });
    $('#close-lightbox').on('click', () => dialog.close());
    $(dialog).on('click', e => { if (e.target === dialog) dialog.close(); });
  }

  // Form không thông báo thành công giả khi chưa có nơi tiếp nhận.
  function summaryFrom(form) {
    const d = new FormData(form);
    const fields = [
      ['Họ và tên', d.get('fullname')], ['Số điện thoại', d.get('phone')],
      ['Email', d.get('email')], ['Ngành quan tâm', d.get('major')],
      ['Cơ sở đào tạo', d.get('campus')], ['Nội dung', d.get('message')]
    ];
    return 'PHIẾU YÊU CẦU TƯ VẤN — CMET\n' + fields.filter(x=>x[1]).map(x=>x[0]+': '+x[1]).join('\n');
  }
  function showResponse(form, text, isSuccess, summary) {
    const $box = $(form).next('.response-box');
    $box.addClass('show').attr('role', isSuccess ? 'status' : 'alert');
    $box.find('.response-title').text(text);
    $box.find('.response-summary').text(summary || '');
    $box.find('.copy-summary').attr('data-summary', summary || '');
    $box.find('.download-summary').attr('data-summary', summary || '');
    $box[0]?.scrollIntoView({behavior:'smooth', block:'nearest'});
  }
  $('.consultation-form').each(function () {
    const form = this;
    $(form).on('submit', async function (event) {
      event.preventDefault();
      const phone = form.elements.phone;
      const digits = (phone.value || '').replace(/\D/g,'');
      if (!/^0\d{9,10}$/.test(digits)) {
        phone.setCustomValidity('Vui lòng nhập số điện thoại Việt Nam từ 10 đến 11 số, bắt đầu bằng 0.');
        phone.reportValidity();phone.addEventListener('input', () => phone.setCustomValidity(''), {once:true});
        return;
      }
      if (!form.reportValidity()) return;
      const text = summaryFrom(form);
      const button = form.querySelector('[type=submit]');
      if (config.formEndpoint) {
        const prev=button.textContent; button.disabled = true; button.textContent = 'Đang gửi...';
        try {
          const data = Object.fromEntries(new FormData(form).entries());
          const r = await fetch(config.formEndpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) });
          if (!r.ok) throw new Error('Máy chủ trả về HTTP ' + r.status);
          showResponse(form, 'Đã nhận xác nhận từ hệ thống tiếp nhận. Cảm ơn bạn!', true, text);
          form.reset();
        } catch (e) { showResponse(form, 'Chưa thể gửi biểu mẫu. Bạn có thể sao chép phiếu và liên hệ hotline để được hỗ trợ.', false, text); }
        finally { button.disabled = false; button.textContent = prev; }
      } else if (config.contactEmail) {
        showResponse(form, 'Phiếu đã được chuẩn bị. Nhấn “Mở ứng dụng email” rồi tự gửi email để hoàn tất (chưa gửi tự động).', false, text);
        const $box = $(form).next('.response-box');
        $box.find('.email-summary').attr('href','mailto:' + config.contactEmail + '?subject=' + encodeURIComponent('Yêu cầu tư vấn CMET') + '&body=' + encodeURIComponent(text)).show();
      } else {
        showResponse(form, 'Đây là bản chạy thử chưa kết nối hệ thống nhận hồ sơ. Không có dữ liệu nào được gửi đi. Hãy sao chép/tải phiếu và liên hệ hotline 1900 63 63 65.', false, text);
      }
    });
  });
  $('.copy-summary').on('click', async function () {
    const text = $(this).attr('data-summary') || '';
    try { await navigator.clipboard.writeText(text); $(this).text('Đã sao chép'); }
    catch (_) {
      const t = document.createElement('textarea'); t.value = text; t.style.position = 'fixed'; document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();$(this).text('Đã sao chép');
    }
  });
  $('.download-summary').on('click', function () {
    const text = $(this).attr('data-summary') || '';
    const url = URL.createObjectURL(new Blob(['\uFEFF'+text],{type:'text/plain;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='phieu-tu-van-CMET.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),500);
  });
})(jQuery);
