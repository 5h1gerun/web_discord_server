document.addEventListener('DOMContentLoaded', () => {
  const result = document.getElementById('gdriveResult');
  const list = document.getElementById('driveFileList');
  const refreshBtn = document.getElementById('refreshFiles');
  const searchInput = document.getElementById('searchQuery');
  const clearBtn = document.getElementById('clearSearch');
  if (!list) return;

  function truncateName(name, limit = 40) {
    return name.length > limit ? name.slice(0, limit) + '…' : name;
  }

  function iconByName(name) {
    const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
    const map = {
      jpg: 'bi-file-earmark-image',
      jpeg: 'bi-file-earmark-image',
      png: 'bi-file-earmark-image',
      gif: 'bi-file-earmark-image',
      mp4: 'bi-file-earmark-play',
      mov: 'bi-file-earmark-play',
      mp3: 'bi-file-earmark-music',
      wav: 'bi-file-earmark-music',
      pdf: 'bi-file-earmark-pdf',
      zip: 'bi-file-earmark-zip',
      rar: 'bi-file-earmark-zip',
      '7z': 'bi-file-earmark-zip'
    };
    return map[ext] || 'bi-file-earmark';
  }

  async function importFile(fileId, filename = '', btn = null) {
    if (!result) return;
    result.textContent = '';
    if (btn) {
      btn.disabled = true;
      btn.dataset.originalText = btn.textContent;
      btn.textContent = '取り込み中...';
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
      await loadFiles(searchInput ? searchInput.value.trim() : '');
    } catch (err) {
      result.innerHTML = `<div class="alert alert-danger">失敗: ${err.message}</div>`;
    } finally {
      if (btn) {
        if (btn.dataset.originalText) {
          btn.textContent = btn.dataset.originalText;
          delete btn.dataset.originalText;
        }
        btn.disabled = false;
      }
    }
  }


  async function loadFiles(query = '') {
    if (!list) return;
    list.innerHTML = '<div class="d-flex justify-content-center my-3"><div class="spinner-border text-secondary" role="status"></div></div>';
    try {
      const url = query ? `/gdrive_files?q=${encodeURIComponent(query)}` : '/gdrive_files';
      const res = await fetch(url, { credentials: 'same-origin' });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'error');
      list.textContent = '';
      if (data.files.length === 0) {
        list.innerHTML = '<div class="text-center text-muted">ファイルが見つかりません</div>';
        return;
      }
      data.files.forEach(f => {
        const item = document.createElement('div');
        item.className = 'list-group-item list-group-item-action d-flex align-items-center';
        const icon = document.createElement('i');
        icon.className = 'bi ' + iconByName(f.name) + ' me-2';
        item.appendChild(icon);
        const span = document.createElement('span');
        span.className = 'flex-grow-1 text-truncate';
        span.style.minWidth = '0';
        span.textContent = truncateName(f.name);
        span.title = f.name;
        item.appendChild(span);
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-outline-primary ms-auto flex-shrink-0';
        btn.style.minWidth = '6em';
        btn.textContent = '取り込み';
        btn.addEventListener('click', () => importFile(f.id, f.name, btn));
        item.appendChild(btn);
        list.appendChild(item);
      });
    } catch (err) {
      list.innerHTML = `<div class="text-danger">一覧取得に失敗しました: ${err.message}</div>`;
    }
  }

  if (refreshBtn) refreshBtn.addEventListener('click', () => loadFiles());
  if (searchInput) {
    let timer;
    const triggerSearch = () => {
      clearTimeout(timer);
      timer = setTimeout(() => loadFiles(searchInput.value.trim()), 500);
    };
    const updateClear = () => {
      if (clearBtn) clearBtn.classList.toggle('d-none', !searchInput.value);
    };
    searchInput.addEventListener('input', () => {
      updateClear();
      triggerSearch();
    });
    searchInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') e.preventDefault();
    });
    updateClear();
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        clearBtn.classList.add('d-none');
      }
      loadFiles();
    });
  }
  loadFiles();
});
