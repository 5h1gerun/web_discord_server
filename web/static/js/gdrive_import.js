document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('gdriveForm');
  const result = document.getElementById('gdriveResult');
  if (!form) return;
  function extractFileId(value) {
    const m = value.match(/[-\w]{25,}/);
    return m ? m[0] : value;
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (!result) return;
    result.textContent = '';
    const fileId = extractFileId(form.file_id.value.trim());
    const filename = form.filename.value.trim();
    if (!fileId) return;
    try {
      const res = await fetch('/import_gdrive', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCsrfToken(),
        },
        body: JSON.stringify({ file_id: fileId, filename }),
      });
      let data;
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        data = await res.json();
      } else {
        // HTML が返ってきた場合は認証エラーなどとみなす
        const text = await res.text();
        const msg = res.status === 403
          ? '認証エラーです。ページを再読み込みしてください'
          : text;
        throw new Error(msg);
      }
      if (!res.ok || !data.success) throw new Error(data.error || 'error');
      result.innerHTML = `<div class="alert alert-success">取り込み完了 (ID: ${data.file_id})</div>`;
    } catch (err) {
      result.innerHTML = `<div class="alert alert-danger">失敗: ${err.message}</div>`;
    }
  });
});
