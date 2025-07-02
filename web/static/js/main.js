// static/js/main.js

// ―― CSRF トークン取得ヘルパー ――
function getCsrfToken() {
  const m = document.querySelector('meta[name="csrf-token"]');
  return m ? m.getAttribute('content') : "";
}

/*──────────────────────
  フルプレビュー表示
──────────────────────*/
function showFull(url, isVideoExplicit = false) {
  const modal      = document.getElementById("previewModal");
  const body       = document.getElementById("previewBody");
  if (!modal || !body) return;

  // URL の拡張子で画像か動画か判定
  const isHls   = url.endsWith('.m3u8');
  const isVideo = isVideoExplicit || /\.(mp4|webm|ogg)$/i.test(url) || isHls;

  if (isVideo) {
    body.innerHTML = `<video id="hlsPlayer" class="w-100" controls autoplay></video>`;
    const video = document.getElementById('hlsPlayer');
    if (isHls && Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(video);
    } else {
      video.src = url;
    }
  } else {
    body.innerHTML = `<img src="${url}" class="img-fluid" />`;
  }

  // Bootstrap 5 のモーダル操作
  const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
  bsModal.show();
}

// プレビュー読み込み失敗時のフォールバック
function previewError(img) {
  const icon = img.parentNode?.querySelector('.fallback-icon');
  if (icon) icon.classList.remove('d-none');
  img.classList.add('d-none');
}

/*─────────────────────────────
    History-API / AJAX ナビゲータ
─────────────────────────────*/
function ajaxNavigate(url, replace = false) {
  fetch(url, { credentials: "same-origin" })
    .then(r => r.text())
    .then(html => {
      const doc    = new DOMParser().parseFromString(html, "text/html");
      const newMain= doc.getElementById("main") || doc.body;  // 要素が無ければ body
      const curMain= document.getElementById("main") || document.body;
      curMain.replaceWith(newMain);          // コンテンツ差し替え

      document.title = doc.title;            // タイトル更新
      if (replace) {
        history.replaceState({ html }, "", url);
      } else {
        history.pushState({ html }, "", url);
      }

      rebindDynamicHandlers();               // D&D / 共有トグル 等を再バインド
    })
    .catch(console.error);
}

// popstate（戻る／進む）時の復元
window.addEventListener("popstate", e => {
  if (e.state && e.state.html) {
    const doc     = new DOMParser().parseFromString(e.state.html, "text/html");
    const newMain = doc.getElementById("main") || doc.body;
    const curMain = document.getElementById("main") || document.body;
    curMain.replaceWith(newMain);
    document.title = doc.title;
    rebindDynamicHandlers();
  }
});

let isUploading = false;
let progWrap = null;
let progBar  = null;
let userList = [];

// ―― ファイル一覧を再描画 ――
async function reloadFileList() {
  const container = document.getElementById("fileListContainer");
  if (!container) return;

  // data-shared 属性で URL を切り替える
  const fldInput = document.querySelector('input[name="folder_id"]');
  const folderId = fldInput?.value;
  const isShared = fldInput?.dataset.shared === "1";
  const url      = isShared && folderId
                     ? `/shared/${folderId}`
                     : window.location.pathname + window.location.search;

  try {
    const res  = await fetch(url, { credentials: "same-origin" });
    if (!res.ok) throw new Error("一覧取得失敗: HTTP " + res.status);

    const html = await res.text();
    // フルページ取得か部分断片か両方に対応
    const parser    = new DOMParser();
    const doc       = parser.parseFromString(html, "text/html");
    const newCont   = doc.getElementById("fileListContainer");
    container.innerHTML = newCont ? newCont.innerHTML : html;

    // 再初期化：Tilt, Ripple, Tooltip など
    if (window.VanillaTilt) {
      VanillaTilt.init(document.querySelectorAll('.tilt'), {
        max: 10, speed: 400, glare: true, "max-glare": 0.3
      });
    }
    if (window.mdb?.Ripple) {
      document.querySelectorAll('[data-mdb-ripple-init]').forEach(el => {
        new mdb.Ripple(el);
      });
    }
    if (window.bootstrap) {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
      });
    }
  } catch (err) {
    console.error("ファイル一覧更新失敗", err);
  }
  const q = document.getElementById("fileSearch")?.value?.toLowerCase() || "";
  if (q) filterTable(q);
  // 再描画後に期限カウントダウン再起動
  startExpirationCountdowns();
  // 残り期限のカウントダウンを再起動
  // 共有トグルのクリックはイベントデリゲーションで処理するため
  // ここでは個別のイベント登録を行わない
}

async function loadUserList() {
  try {
    const res = await fetch('/users', { credentials: 'same-origin' });
    if (!res.ok) return;
    userList = await res.json();
    filterUsers(document.getElementById('userFilterInput')?.value || '');
  } catch (err) {
    console.error('failed to load users', err);
  }
}

// アップロード & 共有トグルのイベントを毎回付け直す
function bindUploadArea() {
  const form       = document.getElementById("uploadForm");
  const uploadBtn  = document.getElementById("uploadBtn");
  const spinner    = document.getElementById("uploadSpinner");
  const uploadArea = document.getElementById("uploadArea");
  progWrap = document.getElementById("uploadProgressWrap");
  progBar  = document.getElementById("uploadProgressBar");

  if (uploadArea && form && uploadBtn) {
    // ドラッグオーバー
    ["dragenter","dragover"].forEach(ev => {
      uploadArea.addEventListener(ev, e => {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
      });
    });
    // ドラッグ離脱・ドロップ時にクラス除去
    ["dragleave","drop"].forEach(ev => {
      uploadArea.addEventListener(ev, e => {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");
      });
    });

    // ドロップ処理
    uploadArea.addEventListener("drop", async e => {
      e.preventDefault();
      if (isUploading) return;

      const files = Array.from(e.dataTransfer.files);
      if (!files.length) return;

      isUploading = true;
      uploadBtn.disabled = true;
      spinner.style.display = "inline-block";

      // フォルダ情報と URL を決定
      const fldInput = document.querySelector('input[name="folder_id"]');
      const folderId = fldInput?.value;
      const isShared = fldInput?.dataset.shared === "1";
      const reqUrl   = isShared ? "/shared/upload" : "/upload";

      // FormData を一回だけ作る
      const formData = new FormData();
      files.forEach(f => formData.append("file", f));
      if (folderId) formData.append("folder_id", folderId);
      formData.append("csrf_token", getCsrfToken());

      try {
        await uploadWithProgress(reqUrl, formData);    // ★ 置き換え
        await reloadFileList();
      } catch (err) {
        alert("アップロードエラー: " + err.message);
      } finally {
        isUploading          = false;
        uploadBtn.disabled   = false;
        form.reset();
      if (spinner)  spinner.style.display  = "none";
      if (progWrap) progWrap.style.display = "none";
      if (progBar)  progBar.style.width    = "0%";
      }
    });
  }
  if (form && uploadBtn) {
    // Enter 抑制
    form.addEventListener("submit", e => e.preventDefault());
    // クリックで非同期アップロード
    uploadBtn.addEventListener("click", async e => {
      e.preventDefault();
      if (isUploading) return;
      isUploading = true;
      uploadBtn.disabled = true;
      if (spinner) spinner.style.display = "inline-block";

      const formData = new FormData(form);
      // data-shared からアップロード先を判断
      const fldInput = form.querySelector('input[name="folder_id"]');
      const isShared = fldInput?.dataset.shared === "1";
      const url      = isShared ? "/shared/upload" : "/upload";

      try {
        await uploadWithProgress(url, formData);
        await reloadFileList();
      } catch (err) {
        alert("アップロードエラー: " + err.message);
      } finally {
        isUploading = false;
        uploadBtn.disabled = false;
        form.reset();
        if (spinner) spinner.style.display = "none";
      }
      if (wrap) wrap.style.display = "none";
      if (bar)  bar.style.width    = "0%";
    });
  }
}
// 秒数を「○日○時間○分○秒」に変換するヘルパー
function formatExpiration(sec) {
  if (sec === 0) return "無期限";
  if (sec < 0)  return "期限切れ";
  const days = Math.floor(sec / 86400);
  const hrs  = Math.floor((sec % 86400) / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  const secs = sec % 60;
  const parts = [];
  if (days) parts.push(`${days}日`);
  if (hrs)  parts.push(`${hrs}時間`);
  if (mins) parts.push(`${mins}分`);
  parts.push(`${secs}秒`);
  return parts.join("");
}

function startExpirationCountdowns() {
  document.querySelectorAll(".expiration-cell").forEach(cell => {
    const fileId = cell.dataset.fileId;
    const toggle = document.querySelector(`.shared-toggle[data-file-id="${fileId}"]`);
    // 非共有なら期限表示・カウントダウンをスキップ
    if (!toggle || toggle.dataset.shared !== "1") {
      cell.querySelector("small").textContent = "-";
      return;
    }
    let exp = parseInt(cell.dataset.expiration, 10) || 0;
    cell.querySelector("small").textContent = formatExpiration(exp);
    clearInterval(cell._expTimer);
    cell._expTimer = setInterval(() => {
      exp = exp > 0 ? exp - 1 : 0;
      cell.dataset.expiration = exp;
      cell.querySelector("small").textContent = formatExpiration(exp);
      if (exp === 0) clearInterval(cell._expTimer);
    }, 1000);
  });
}

window.addEventListener("DOMContentLoaded", startExpirationCountdowns);

// 共有トグルのクリック処理はイベントデリゲーションで行うため
// ここでは個別のイベント登録を行わない

// ―― 共有トグル処理 ――
async function handleToggle(toggle, expiration) {
  const fileId = toggle.dataset.fileId;
  const url    = toggle.dataset.url;
  try {
    const res = await fetch(url, {
      method:      "POST",
      credentials: "same-origin",
      headers:     {
        "X-CSRF-Token": getCsrfToken(),
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ expiration })
    });

    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    const token    = data.token;
    const isShared = data.is_shared;

    // バッジ更新
    toggle.classList.toggle("bg-success", isShared);
    toggle.classList.toggle("bg-secondary", !isShared);
    toggle.innerHTML = `<i class="bi bi-link-45deg me-1"></i>${isShared ? "共有中" : "非共有"}`;
    // 今後の処理で使われる dataset.shared も更新
    toggle.dataset.shared = isShared ? "1" : "0";

    // 期限セレクトに返却された expiration を反映
    const selExp = document.querySelector(`.expiration-select[data-file-id="${fileId}"]`);
    if (typeof data.expiration === "number" && selExp) {
      selExp.value = data.expiration;
    }

    // 期限セルの残秒数を更新／解除
    const cell = document.querySelector(`.expiration-cell[data-file-id="${fileId}"]`);
    if (cell) {
      clearInterval(cell._expTimer);
      if (isShared) {
        const exp0 = data.expiration || 0;
        cell.dataset.expiration = exp0;
        cell.querySelector("small").textContent = formatExpiration(exp0);
        cell._expTimer = setInterval(() => {
          let e = parseInt(cell.dataset.expiration, 10) || 0;
          e = e > 0 ? e - 1 : 0;
          cell.dataset.expiration = e;
          cell.querySelector("small").textContent = formatExpiration(e);
          if (e === 0) clearInterval(cell._expTimer);
        }, 1000);
      } else {
        cell.querySelector("small").textContent = "-";
      }
    }

    // ─── 期限セレクトの値をサーバー返却の expiration で更新 ───
    const sel = document.querySelector(`.expiration-select[data-file-id="${fileId}"]`);
    if (data.expiration !== undefined && sel) {
      sel.value = data.expiration;
    }

    // リンク欄更新（個人ファイルか共有フォルダ内かでパスを切り替え）
    const href = data.share_url || "";
    const box = document.getElementById(`sharebox-${fileId}`);
    if (box) {
      box.innerHTML = isShared
       ? `<div class="input-group input-group-sm">
              <input id="link-${fileId}" type="text" class="form-control" readonly
                    value="${href}">
              <button class="btn btn-sm btn-outline-secondary ripple"
                      data-mdb-ripple-init
                      onclick="copyLink('${fileId}')">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>`
        : `<span class="text-muted">非共有</span>`;
    }

    // 共有状態が変わった際はプレビューURLも変わるため一覧を再取得
    await reloadFileList();
  } catch (err) {
    alert("共有切替エラー: " + err.message);
  }
}

// ―― 削除処理 ――
async function handleDelete(form) {
  if (!confirm("本当に削除しますか？")) return;

  // フォームの action(URL) に対してヘッダ＆クレデンシャル付きでPOST
  const res = await fetch(form.action, {
    method:      "POST",
    credentials: "same-origin",                   // セッション Cookie を送信
    headers:     { "X-CSRF-Token": getCsrfToken() } // CSRF トークンをヘッダで
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error("削除に失敗しました: " + txt);
  }
  // 成功したら自動でリストをリロード
  await reloadFileList();
}

// ―― コピー＆モーダル ――
function copyLink(id) {
  const input = document.getElementById(`link-${id}`);
  if (!input) return;
  navigator.clipboard.writeText(input.value).then(() => {
    const toastEl = document.getElementById('copyToast');
    if (toastEl && window.mdb?.Toast) {
      new mdb.Toast(toastEl).show();
    }
  });
}
// ── XMLHttpRequest で進捗を拾う関数 ───────────────────
function uploadWithProgress(url, formData) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // ── ① プログレスバー要素取得（以降は “wrap/bar” に統一）
    const wrap = document.getElementById("uploadProgressWrap");
    const bar  = document.getElementById("uploadProgressBar");
    const stat = document.getElementById("uploadStat");

    xhr.open("POST", url);
    xhr.withCredentials = true;                       // fetch と同挙動
    xhr.setRequestHeader("X-CSRF-Token", getCsrfToken());

    // ② アップロード開始時にバーを必ず見せる
    if (wrap && bar) {
      wrap.style.display = "block";
      bar.style.width    = "1%";      // 小容量でも 0% で消えないように
    }

    xhr.upload.onprogress = (e) => {
      if (!e.lengthComputable || !bar) return;
      const percent = (e.loaded / e.total) * 100;
      bar.style.width  = percent.toFixed(1) + "%";               // 幅
      bar.textContent  = percent.toFixed(1) + " %";              // 表示

      // ★ バイト数表示（MB 換算、小数 1 桁）
      if (stat) {
        const mbLoaded = (e.loaded / 1048576).toFixed(1);
        const mbTotal  = (e.total  / 1048576).toFixed(1);
        stat.textContent = `${mbLoaded} MB / ${mbTotal} MB`;
      }

      // アクセシビリティ用 ARIA 値も更新
      bar.setAttribute("aria-valuenow", percent.toFixed(0));
    };

    xhr.onload = () => {
      if (wrap && bar) {
        bar.style.width   = "100%";
        bar.textContent   = "100 %";
        if (stat) stat.textContent = "... 完了";
        setTimeout(() => {          // 少し見せてから隠す
          wrap.style.display = "none";
          bar.style.width    = "0%";
          bar.textContent    = "0 %";
          if (stat) stat.textContent = "0 / 0 MB";
        }, 400);
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(xhr.responseText || xhr.status));
      }
    };
    xhr.onerror = () => reject(new Error("network error"));

    xhr.send(formData);
  });
}
function filterTable(term) {
  const rows = document.querySelectorAll("#fileListContainer tbody tr");
  rows.forEach(tr => {
    const name = tr.querySelector(".file-name")?.textContent.toLowerCase() || "";
    const tags = tr.dataset.tags?.toLowerCase() || "";
    tr.style.display = (name.includes(term) || tags.includes(term)) ? "" : "none";
  });
}

function filterUsers(term) {
  const sel = document.getElementById('sendUserSelect');
  if (!sel) return;
  const t = term.toLowerCase();
  sel.innerHTML = userList
    .filter(u => u.name.toLowerCase().includes(t))
    .map(u => `<option value="${u.id}">${u.name}</option>`)
    .join('');
}

function initProgressElems() {
  progWrap = document.getElementById("uploadProgressWrap");
  progBar  = document.getElementById("uploadProgressBar");
}

// ―― DOMContentLoaded 後にイベント登録 ――
function rebindDynamicHandlers() {
  // ダークモード切替
  loadUserList();
  const sw = document.getElementById('darkModeSwitch');
  if (sw) {
    const stored     = localStorage.getItem('theme');
    const prefersDark= window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (stored === 'dark' || (stored === null && prefersDark)) {
      document.body.classList.add('dark-mode');
      sw.checked = true;
    }
    sw.addEventListener('change', () => {
      document.body.classList.toggle('dark-mode', sw.checked);
      localStorage.setItem('theme', sw.checked ? 'dark' : 'light');
    });
  }
  const userFilter = document.getElementById('userFilterInput');
  if (userFilter) {
    userFilter.addEventListener('input', e => filterUsers(e.target.value));
  }
  /* ───── フォルダジャンプ ───── */
  const sel = document.getElementById("folderJump");
  if (sel) {
    sel.onchange = e => {
      const id = e.target.value;
      if (id) ajaxNavigate(`/shared/${id}`);
    };
  }
  bindUploadArea();
  // AJAX／History-API遷移後にも残り期限カウントダウンを再起動
  if (typeof startExpirationCountdowns === "function") {
    startExpirationCountdowns();
  }
}

// 初回ロード時にも呼ぶ
document.addEventListener("DOMContentLoaded", rebindDynamicHandlers);
// bfcache 復元（iOS Safari の戻る）対策
window.addEventListener("pageshow", rebindDynamicHandlers);


document.addEventListener("click", async (e) => {
  const sendBtn = e.target.closest(".send-btn");
  if (sendBtn) {
    const fid = sendBtn.dataset.fileId;
    document.getElementById('sendFileId').value = fid;
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('sendModal'));
    modal.show();
    return;
  }

  const toggle = e.target.closest('.shared-toggle');
  if (toggle) {
    const fid = toggle.dataset.fileId;
    const sel = document.querySelector(`.expiration-select[data-file-id="${fid}"]`);
    const exp = sel ? parseInt(sel.value, 10) : 0;
    await handleToggle(toggle, exp);
    return;
  }

  const btn = e.target.closest(".rename-btn");
  if (!btn) return;

  const fileId   = btn.dataset.fileId;
  const current  = btn.dataset.current || "";
  const input = prompt("新しいファイル名（拡張子は自動維持）", current.replace(/\.[^.]+$/, ""));
  if (input === null) return;                    // キャンセル
  if (!input.trim())  { alert("空です"); return;}

  try {
    btn.disabled = true;
      const isShared = btn.dataset.shared === "1";            // ★ 追加
      const apiUrl   = isShared
                      ? `/shared/rename_file/${fileId}`      // ★ 共有用
                      : `/rename/${fileId}`;                 // ★ 個人用

      const res = await fetch(apiUrl, {   
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
      },
      body: JSON.stringify({ name: input.trim() }),
    });
    const j = await res.json();
    if (!res.ok || j.status !== "ok") throw new Error(j.error || res.status);

    // 表示をその場で更新
    const nameEl = document.querySelector(`.file-name[data-file-id="${fileId}"]`);
    if (nameEl) nameEl.textContent = j.new_name;
    btn.dataset.current = j.new_name;
  } catch (err) {
    alert("リネーム失敗: " + err);
  } finally {
    btn.disabled = false;
  }
});

  document.addEventListener("input", e => {
    if (e.target.id === "fileSearch") {
      filterTable(e.target.value.toLowerCase());
    } else if (e.target.classList.contains("tag-input")) {
      const fid  = e.target.dataset.fileId;
      const isShared = e.target.dataset.shared === "1";
      const form = new FormData();
      form.append("tags", e.target.value);
      const url = isShared ? `/shared/tags/${fid}` : `/tags/${fid}`;
      fetch(url, {
        method: "POST",
        body: form,
        headers: { "X-CSRF-Token": getCsrfToken() },
        credentials: "same-origin"
      }).catch(err => console.error("tag update failed", err));
    }
  });

document.addEventListener("click", e => {
  const a = e.target.closest("a[data-ajax]");
  if (a && a.origin === location.origin) {
    e.preventDefault();
    ajaxNavigate(a.href);
  }
});

const sendExecBtn = document.getElementById('sendExecBtn');
if (sendExecBtn) {
  sendExecBtn.addEventListener('click', async () => {
    const uid = document.getElementById('sendUserSelect').value;
    const fid = document.getElementById('sendFileId').value;
    if (!uid) return;
    sendExecBtn.disabled = true;
    try {
      const res = await fetch('/sendfile', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCsrfToken(),
        },
        body: JSON.stringify({ file_id: fid, user_id: uid })
      });
      if (!res.ok) throw new Error(await res.text());
      bootstrap.Modal.getInstance(document.getElementById('sendModal')).hide();
      alert('送信しました');
    } catch (err) {
      alert('送信失敗: ' + err.message);
    } finally {
      sendExecBtn.disabled = false;
    }
  });
}

;(function() {
  const btn = document.getElementById('scrollToTop');
  const SHOW_AFTER = 200;  // 200px 以上スクロールしたら出現

  // スクロールでボタンの出し入れ
  window.addEventListener('scroll', () => {
    if (window.scrollY > SHOW_AFTER) {
      btn.classList.add('show');
    } else {
      btn.classList.remove('show');
    }
  });

  // クリックでトップへスムーズ移動
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();
