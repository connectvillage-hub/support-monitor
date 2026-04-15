let currentPage = 1;
let searchTimer = null;
let activeCat = '';

const CAT_COLORS = {
    'R&D': 'c-rd', '사업화': 'c-biz', '투자연계': 'c-invest',
    '입주지원': 'c-space', 'IR피칭': 'c-ir', '경진대회': 'c-contest',
    '교육멘토링': 'c-edu', '인력지원': 'c-hr', '기타': 'c-etc',
};

async function api(url, opts) {
    const res = await fetch(url, { headers: {'Content-Type': 'application/json'}, ...opts });
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json().catch(() => ({}));
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        const btn = document.getElementById('refreshBtn');
        btn.disabled = true;
        try {
            const res = await api('/api/scrape/run', { method: 'POST' });
            if (res.ok === false) { alert(res.message); btn.disabled = false; return; }
            showScrapePopup();
            pollScrapeStatus(btn);
        } catch (e) {
            alert('스크래핑 실행 실패: ' + e.message);
            btn.disabled = false;
        }
    });

    document.getElementById('markAllReadBtn').addEventListener('click', async () => {
        await api('/api/support/programs/mark-all-read', { method: 'POST' });
        refresh();
    });

    document.getElementById('siteFilter').addEventListener('change', () => { currentPage = 1; refresh(); });
    document.getElementById('statusFilter').addEventListener('change', () => { currentPage = 1; refresh(); });
    document.getElementById('searchInput').addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => { currentPage = 1; refresh(); }, 400);
    });

    refresh();
});

async function refresh() {
    const $list = document.getElementById('programList');
    $list.innerHTML = '<div class="loading">불러오는 중...</div>';

    const site = document.getElementById('siteFilter').value;
    const filter = document.getElementById('statusFilter').value;
    const search = document.getElementById('searchInput').value;

    const params = new URLSearchParams({ page: currentPage, per_page: 20 });
    if (site) params.set('source_site', site);
    if (filter) params.set('filter', filter);
    if (search) params.set('search', search);
    if (activeCat) params.set('category', activeCat);

    try {
        const [data, stats, logs] = await Promise.all([
            api(`/api/support/programs?${params}`),
            api('/api/support/stats'),
            api('/api/support/logs'),
        ]);
        renderStats(stats);
        renderCatTags(stats);
        renderSiteFilter(stats);
        renderList(data);
        renderPagination(data);
        renderLastUpdate(logs);
    } catch (e) {
        $list.innerHTML = '<div class="empty">데이터를 불러올 수 없습니다. "업데이트" 버튼을 눌러주세요.</div>';
    }
}

function renderStats(stats) {
    const $el = document.getElementById('stats');
    const f = document.getElementById('statusFilter').value;
    $el.innerHTML = `
        <div class="stat-card ${f===''?'active':''}" data-filter="">
            <div class="stat-num">${stats.total || 0}</div><div class="stat-label">전체</div>
        </div>
        <div class="stat-card unread ${f==='unread'?'active':''}" data-filter="unread">
            <div class="stat-num">${stats.unread_count || 0}</div><div class="stat-label">미확인</div>
        </div>
        <div class="stat-card bookmark ${f==='bookmarked'?'active':''}" data-filter="bookmarked">
            <div class="stat-num">${stats.bookmark_count || 0}</div><div class="stat-label">북마크</div>
        </div>
    `;
    $el.querySelectorAll('.stat-card').forEach(card => {
        card.addEventListener('click', () => {
            document.getElementById('statusFilter').value = card.dataset.filter;
            currentPage = 1;
            refresh();
        });
    });
}

function renderCatTags(stats) {
    const $el = document.getElementById('catTags');
    const cats = stats.by_category || {};
    const order = ['R&D','사업화','투자연계','입주지원','IR피칭','경진대회','교육멘토링','인력지원','기타'];

    let html = `<span class="cat-tag ${activeCat===''?'active':''}" data-cat="">전체</span>`;
    for (const cat of order) {
        if (cats[cat]) {
            const cls = CAT_COLORS[cat] || 'c-etc';
            html += `<span class="cat-tag ${activeCat===cat?'active':''}" data-cat="${cat}">${cat}<span class="tag-count">${cats[cat]}</span></span>`;
        }
    }
    $el.innerHTML = html;

    $el.querySelectorAll('.cat-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            activeCat = tag.dataset.cat;
            currentPage = 1;
            refresh();
        });
    });
}

function renderSiteFilter(stats) {
    const $sel = document.getElementById('siteFilter');
    const current = $sel.value;
    const sites = Object.keys(stats.by_site || {}).sort();
    const existing = Array.from($sel.options).slice(1).map(o => o.value);
    if (JSON.stringify(sites) !== JSON.stringify(existing)) {
        $sel.innerHTML = '<option value="">전체 사이트</option>';
        sites.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s; opt.textContent = `${s} (${stats.by_site[s]})`;
            $sel.appendChild(opt);
        });
        $sel.value = current;
    }
}

function renderList(data) {
    const $list = document.getElementById('programList');
    const programs = data.programs || [];
    if (!programs.length) { $list.innerHTML = '<div class="empty">표시할 지원사업이 없습니다.</div>'; return; }

    $list.innerHTML = programs.map(p => {
        const dismissedCls = p.is_read ? ' is-dismissed' : '';
        const bmCls = p.is_bookmarked ? ' active' : '';

        // Status badge
        const stCls = p.status && (p.status.includes('진행') || p.status.includes('접수')) ? 'ing' : (p.status && (p.status.includes('마감') || p.status.includes('종료')) ? 'end' : '');
        const stHtml = p.status ? `<span class="status-badge ${stCls}">${p.status}</span>` : '';

        // Category badges
        const cats = (p.category || '').split(',').filter(c => c.trim());
        const catHtml = cats.map(c => {
            const cls = CAT_COLORS[c.trim()] || 'c-etc';
            return `<span class="cat-badge ${cls}">${c.trim()}</span>`;
        }).join('');

        // Duplicate badge
        const dupes = p.duplicates || [];
        const dupeHtml = dupes.length > 0 ? `<button class="dupe-btn" data-id="${p.id}">+${dupes.length}</button>` : '';
        const dupeListHtml = dupes.length > 0 ? `<div class="dupe-list hidden" id="dupes-${p.id}">${dupes.map(d =>
            `<a href="${d.source_url}" target="_blank" class="dupe-item"><span class="badge">${d.source_site}</span></a>`
        ).join('')}</div>` : '';

        return `
        <div class="card${dismissedCls}" data-id="${p.id}">
            <div class="card-ox">
                <button class="ox-btn o-btn" data-id="${p.id}" title="관심있음">O</button>
                <button class="ox-btn x-btn" data-id="${p.id}" title="관심없음">X</button>
            </div>
            <div class="card-body">
                <div class="card-top">
                    <div class="card-top-left">
                        <span class="badge">${p.source_site}</span>
                        ${dupeHtml}
                        ${stHtml}
                        ${catHtml}
                    </div>
                    <div class="card-right">
                        <button class="icon-btn bookmark-btn${bmCls}" data-id="${p.id}" title="북마크">${p.is_bookmarked ? '\u2605' : '\u2606'}</button>
                        <span class="card-date">${p.first_seen ? p.first_seen.split('T')[0].slice(5) : ''}</span>
                    </div>
                </div>
                <a class="card-title" href="${p.source_url}" target="_blank" rel="noopener">${p.title}</a>
                ${dupeListHtml}
                <div class="card-meta">
                    ${p.organization ? `<span>${p.organization}</span>` : ''}
                    ${p.deadline ? `<span>마감: ${p.deadline}</span>` : ''}
                </div>
            </div>
        </div>`;
    }).join('');

    // Dupe toggle
    $list.querySelectorAll('.dupe-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const el = document.getElementById(`dupes-${btn.dataset.id}`);
            if (el) el.classList.toggle('hidden');
        });
    });

    // O button = bookmark + keep visible
    $list.querySelectorAll('.o-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            await api(`/api/support/programs/${id}/bookmark`, { method: 'POST', body: JSON.stringify({set: true}) });
            refresh();
        });
    });

    // X button = dismiss (gray out)
    $list.querySelectorAll('.x-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            await api(`/api/support/programs/${id}/read`, { method: 'POST' });
            refresh();
        });
    });

    // Bookmark handlers
    $list.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const res = await api(`/api/support/programs/${btn.dataset.id}/bookmark`, { method: 'POST' });
            btn.classList.toggle('active', res.is_bookmarked);
            btn.textContent = res.is_bookmarked ? '\u2605' : '\u2606';
        });
    });
}

function renderPagination(data) {
    const $el = document.getElementById('pagination');
    const total = data.total_pages || 1, cur = data.page || 1;
    if (total <= 1) { $el.innerHTML = ''; return; }

    let html = '';
    if (cur > 1) html += `<button data-p="${cur-1}">&laquo;</button>`;
    for (let i = Math.max(1, cur-3); i <= Math.min(total, cur+3); i++)
        html += `<button data-p="${i}" class="${i===cur?'active':''}">${i}</button>`;
    if (cur < total) html += `<button data-p="${cur+1}">&raquo;</button>`;
    $el.innerHTML = html;

    $el.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => { currentPage = parseInt(btn.dataset.p); refresh(); });
    });
}

function renderLastUpdate(logs) {
    const $el = document.getElementById('lastUpdate');
    const items = logs.logs || [];
    if (items.length > 0 && items[0].scraped_at) {
        const d = new Date(items[0].scraped_at);
        $el.textContent = `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    }
}

/* ── 스크래핑 팝업 ── */

function showScrapePopup() {
    let overlay = document.getElementById('scrapeOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'scrapeOverlay';
        overlay.innerHTML = `
            <div class="scrape-popup">
                <div class="scrape-spinner"></div>
                <div class="scrape-title" id="scrapeTitle">공고 수집 중...</div>
                <div class="scrape-progress" id="scrapeProgress">0 / 14 사이트</div>
                <div class="scrape-bar-wrap"><div class="scrape-bar" id="scrapeBar"></div></div>
                <div class="scrape-detail" id="scrapeDetail"></div>
            </div>`;
        document.body.appendChild(overlay);
    }
    overlay.classList.remove('hidden');
    overlay.style.display = 'flex';
}

function updateScrapePopup(status) {
    const pct = Math.round((status.done_count / status.total_count) * 100);
    document.getElementById('scrapeProgress').textContent = `${status.done_count} / ${status.total_count} 사이트`;
    document.getElementById('scrapeBar').style.width = pct + '%';
    document.getElementById('scrapeDetail').textContent = `신규 ${status.new_items}건${status.failed ? ', 실패 ' + status.failed + '건' : ''}`;
}

function showScrapeDone(status) {
    document.getElementById('scrapeTitle').textContent = '수집 완료!';
    document.getElementById('scrapeProgress').textContent = `${status.total_count}개 사이트 수집 완료`;
    document.getElementById('scrapeDetail').textContent = `신규 ${status.new_items}건 추가됨`;
    document.getElementById('scrapeBar').style.width = '100%';
    const spinner = document.querySelector('.scrape-spinner');
    if (spinner) spinner.style.display = 'none';

    setTimeout(() => {
        const overlay = document.getElementById('scrapeOverlay');
        if (overlay) overlay.style.display = 'none';
        refresh();
    }, 2500);
}

function pollScrapeStatus(btn) {
    const poll = setInterval(async () => {
        try {
            const status = await api('/api/scrape/status');
            updateScrapePopup(status);
            if (!status.running) {
                clearInterval(poll);
                showScrapeDone(status);
                btn.disabled = false;
            }
        } catch (e) {
            clearInterval(poll);
            btn.disabled = false;
        }
    }, 2000);
}
