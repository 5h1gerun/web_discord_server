document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('gdriveForm');
  const result = document.getElementById('gdriveResult');
  const list = document.getElementById('driveFileList');
  const refreshBtn = document.getElementById('refreshFiles');
  const searchInput = document.getElementById('searchQuery');
  const importBtn = document.getElementById('importBtn');
  const importSpinner = document.getElementById('importSpinner');
  if (!form) return;

  function extractFileId(value) {
    const m = value.match(/[-\w]{25,}/);
    return m ? m[0] : value;
  }

  async function importFile(fileId, filename = '', btn = importBtn) {
    if (!result) return;
    result.textContent = '';
    if (btn) {
      btn.disabled = true;
      const sp = btn.querySelector('.spinner-border');
      if (sp) {
        sp.style.display = 'inline-block';
      } else {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = '取り込み中...';
      }
    }
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
    } finally {
      if (btn) {
        const sp = btn.querySelector('.spinner-border');
        if (sp) {
          sp.style.display = 'none';
        } else if (btn.dataset.originalText) {
          btn.textContent = btn.dataset.originalText;
          delete btn.dataset.originalText;
        }
        btn.disabled = false;
      }
    }
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    const fileId = extractFileId(form.file_id.value.trim());
    const filename = form.filename.value.trim();
    if (fileId) importFile(fileId, filename, importBtn);
  });

  async function loadFiles(query = '') {
    if (!list) return;
    list.textContent = 'loading...';
    try {
      const url = query ? `/gdrive_files?q=${encodeURIComponent(query)}` : '/gdrive_files';
      const res = await fetch(url, {credentials: 'same-origin'});
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'error');
      list.textContent = '';
      data.files.forEach(f => {
        const div = document.createElement('div');
        div.className = 'd-flex align-items-center mb-2';
        const span = document.createElement('span');
        span.textContent = f.name;
        div.appendChild(span);
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-primary ms-auto';
        btn.textContent = '取り込み';
        btn.addEventListener('click', () => importFile(f.id, f.name, btn));
        div.appendChild(btn);
        list.appendChild(div);
      });
    } catch (err) {
      list.textContent = `一覧取得に失敗しました: ${err.message}`;
    }
  }

  if (refreshBtn) refreshBtn.addEventListener('click', () => loadFiles());
  if (searchInput) {
    let timer;
    const triggerSearch = () => {
      clearTimeout(timer);
      timer = setTimeout(
        () => loadFiles(searchInput.value.trim()),
        500
      );
    };
    searchInput.addEventListener('input', triggerSearch);
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') e.preventDefault();
    });
  }
  loadFiles();
});
