/* ══════════════════════════════════════════════════════════════
   live.js — 데모 화면을 실제 API에 연결하는 어댑터
   · /api/health 가 살아 있으면 "서버 연결됨"으로 전환
   · 파일을 고르면 진짜 업로드 → 큐 → 워커 추론 → 결과 폴링
   · 서버가 없으면 기존 예시 데이터 그대로 (발표 안전장치)
   ══════════════════════════════════════════════════════════════ */
const API = (window.VK_API || '/api');
let LIVE = false, LIVE_INFO = null, PICKED = null, MAX_MB = 100, REJECT_MSG = '';

async function apiHealth() {
  try {
    const r = await fetch(`${API}/health`, { cache: 'no-store' });
    if (!r.ok) return null;
    return await r.json();
  } catch (e) { return null; }
}

function liveBadge() {
  const bar = document.querySelector('#scr-setup .nav .sp');
  if (!bar || document.getElementById('liveBadge')) return;
  const b = document.createElement('span');
  b.id = 'liveBadge'; b.className = 'pill ' + (LIVE ? 'ok' : 'gray');
  b.style.marginRight = '10px';
  b.textContent = LIVE
    ? `● 서버 연결됨 · ${LIVE_INFO.mock ? 'MOCK 모드' : LIVE_INFO.model_version}`
    : '○ 서버 없음 · 예시 데이터';
  bar.parentNode.insertBefore(b, bar.nextSibling);
}

/* 업로드 UI를 실제 파일 입력으로 바꾼다 */
function attachUpload() {
  const drop = document.querySelector('#scr-setup .drop');
  if (!drop || drop.dataset.live) return;
  drop.dataset.live = '1';

  const input = document.createElement('input');
  input.type = 'file'; input.accept = '.wav,.mp3,.m4a,.flac,.ogg,.webm,audio/*';
  input.style.display = 'none';
  const btn = document.createElement('button');
  btn.className = 'btn btn-o btn-sm'; btn.style.marginTop = '14px';
  btn.textContent = '＋ 내 음성 파일 올리기';
  const label = document.createElement('p');
  label.style.cssText = 'font-size:12.5px; color:var(--mut); margin-top:8px';

  btn.onclick = () => input.click();
  const tooBig = f => f && f.size > MAX_MB * 1024 * 1024;
  const showPick = f => {
    if (tooBig(f)) {
      PICKED = null;
      REJECT_MSG = `${f.name} 은(는) ${(f.size / 1048576).toFixed(1)}MB 라 올릴 수 없어요 (최대 ${MAX_MB}MB).\n`
        + '다른 파일을 고르거나, 아래 예시 통화 버튼을 눌러 예시로 진행할 수 있어요.';
      label.innerHTML = `<b style="color:var(--red)">${f.name} — ${(f.size / 1048576).toFixed(1)}MB 라 올릴 수 없어요.</b>`
        + `<br>${MAX_MB}MB 이하만 됩니다. 긴 녹음이면 필요한 구간만 잘라서 올려주세요.`;
      return;
    }
    PICKED = f || null;
    REJECT_MSG = '';
    label.textContent = PICKED ? `선택됨: ${PICKED.name} (${(PICKED.size / 1048576).toFixed(1)}MB)` : '';
    document.querySelectorAll('#optSample button').forEach(b => b.classList.remove('on'));
  };
  input.onchange = () => showPick(input.files[0]);
  const hint = document.createElement('p');
  hint.style.cssText = 'font-size:12px; color:var(--mut); margin-top:6px';
  hint.textContent = `wav · mp3 · m4a · flac · ogg · 최대 ${MAX_MB}MB`;
  drop.appendChild(input); drop.appendChild(btn); drop.appendChild(label); drop.appendChild(hint);

  drop.addEventListener('dragover', e => { e.preventDefault(); drop.style.borderColor = 'var(--red)'; });
  drop.addEventListener('dragleave', () => { drop.style.borderColor = ''; });
  drop.addEventListener('drop', e => {
    e.preventDefault(); drop.style.borderColor = '';
    showPick(e.dataTransfer.files[0]);
  });
}

/* 서버 결과 → 데모 화면이 아는 형태로 변환 */
function toScene(a) {
  const EM = ['angry', 'sadness', 'neutral', 'happy', 'fear', 'disgust', 'surprise'];
  const wins = a.segments.map(s => [
    s.t_start,
    [s.t_start, s.hold ? s.emotion : s.emotion, s.valence, s.arousal, s.confidence, s.probs, s.probs_raw]
  ]);
  // 급변 지점: 대표 감정이 10초 이상 유지되다 바뀌는 지점
  const flags = [];
  let cur = null;
  a.segments.forEach(s => {
    if (!cur || cur.emo !== s.emotion) {
      if (cur && (s.t_start - cur.start) >= 10 && flags.length < 3 && cur.start > 0) {
        flags.push([Math.round(cur.start), `${EMO[cur.emo][0]} 구간 시작`, EMO[cur.emo][1],
          `${Math.round(cur.start)}초부터 ${Math.round(s.t_start - cur.start)}초 동안 이어졌습니다.`]);
      }
      cur = { emo: s.emotion, start: s.t_start };
    }
  });
  const risk = (a.summary && a.risk_seconds)
    ? [[a.summary.risk_start ?? 0, (a.summary.risk_start ?? 0) + a.risk_seconds,
        a.summary.signal, EMO[a.top_emotion || 'angry'][1]]] : [];
  const mid = a.segments[Math.floor(a.segments.length / 2)] || { t_start: 0 };
  return {
    id: a.id, dom: a.domain, thr: a.threshold, label: a.filename || '업로드한 음성', date: (a.created_at || '').slice(0, 16).replace('T', ' '),
    dur: Math.round(a.duration_sec || 0), sel: risk.length ? risk[0][0] : mid.t_start,
    region: a.region_used || a.region, wins, risk,
    flags: flags.length ? flags : [[Math.round(mid.t_start), '구간 살펴보기', EMO.neutral[1], '그래프를 클릭하면 그 3초 구간을 볼 수 있습니다.']],
    raw: (a.segments[0] || {}).probs || {}, serverSummary: a.summary,
    quote: '음성만 분석합니다 · 대화 내용은 저장하지 않습니다'
  };
}

/* 분석 시작 버튼 가로채기 */
async function runLive() {
  if (PICKED.size > MAX_MB * 1024 * 1024) {
    alert(`${(PICKED.size / 1048576).toFixed(1)}MB 라 올릴 수 없어요 (최대 ${MAX_MB}MB).`);
    return;
  }
  const fd = new FormData();
  fd.append('file', PICKED);
  fd.append('domain', S.domain);
  fd.append('region', S.region);

  window.LIVE_JOB = true;             // 가짜 진행바가 먼저 결과로 넘어가지 않게
  go('ana');
  const title = document.getElementById('anaTitle');
  title.textContent = `${PICKED.name} 분석 중`;
  document.getElementById('anaSub').textContent =
    `${DOMAINS[S.domain].name} · ${REGIONS[activeRegion()].name} 보정 · 서버로 업로드 중`;

  let id;
  try {
    const r = await fetch(`${API}/analyses`, { method: 'POST', body: fd });
    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
    id = (await r.json()).id;
  } catch (e) {
    window.LIVE_JOB = false;
    alert('업로드 실패: ' + e.message);
    return go('setup');
  }

  const t0 = Date.now();
  while (true) {
    await new Promise(r => setTimeout(r, 1200));
    let a;
    try { a = await (await fetch(`${API}/analyses/${id}`)).json(); } catch (e) { continue; }
    const sec = Math.round((Date.now() - t0) / 1000);
    const kor = { queued: '대기 중 (워커가 곧 집어갑니다)', running: 'WavLM 추론 중', done: '완료', failed: '실패' };
    document.getElementById('anaSub').textContent =
      `${DOMAINS[S.domain].name} · ${REGIONS[activeRegion()].name} 보정 · ${kor[a.status] || a.status} · ${sec}초 경과`;
    if (a.status === 'done') {
      window.LIVE_JOB = false;
      window.DASH_DATA = null;                            // 새 분석이 반영되도록
      SCENES.live = toScene(a);
      S.sample = 'live';
      S.sel = SCENES.live.sel;
      document.getElementById('anaSub').textContent =
        `${DOMAINS[S.domain].name} · ${REGIONS[activeRegion()].name} 보정 · 완료 · ${sec}초 소요`;
      await finishAna(sec, a.n_windows || (a.segments ? a.segments.length : 0));
      go('result');                                  // renderResult 훅이 플레이어를 연결한다
      return;
    }
    if (a.status === 'failed') {
      window.LIVE_JOB = false;
      alert('분석 실패: ' + (a.error || '알 수 없는 오류'));
      return go('setup');
    }
    if (Date.now() - t0 > 10 * 60 * 1000) {
      window.LIVE_JOB = false; alert('시간 초과'); return go('setup');
    }
  }
}


/* ══════════════════════════════════════════════════════════════
   실제 음성 재생 — 결과 화면의 플레이어를 진짜로 동작하게
   ══════════════════════════════════════════════════════════════ */
let AUD = null, RAF = 0, LAST_WIN = -1, SPEEDS = [1, 1.25, 1.5, 0.75], SPD = 0, CUR_ID = null;
const _selectSeg = window.selectSeg;

/* 사용자가 그래프·급변지점·다음구간을 누르면 음성도 그 위치로 따라간다 */
window.selectSeg = function (t, quiet) {
  _selectSeg(t, quiet);
  if (AUD && !quiet && isFinite(t) && Math.abs(AUD.currentTime - t) > 0.25) {
    try { AUD.currentTime = t; } catch (e) { }
  }
};

function timelineX(sc, t) {           // tlSVG 와 같은 좌표 계산
  const L = 44, R = 12, W = 1000;
  return L + (W - L - R) * t / sc.dur;
}

function playhead(sc, t) {
  const svg = document.querySelector('#rTimeline svg');
  if (!svg) return;
  let ph = svg.querySelector('.ph');
  if (!ph) {
    const ns = 'http://www.w3.org/2000/svg';
    ph = document.createElementNS(ns, 'line');
    ph.setAttribute('class', 'ph');
    ph.setAttribute('y1', 10); ph.setAttribute('y2', 310);
    ph.setAttribute('stroke', '#E8433F'); ph.setAttribute('stroke-width', 2);
    svg.insertBefore(ph, svg.querySelector('.hit'));
  }
  const x = timelineX(sc, t);
  ph.setAttribute('x1', x); ph.setAttribute('x2', x);
}

function tick() {
  if (!AUD || AUD.paused) return;
  const sc = scene(), t = AUD.currentTime;
  document.getElementById('rCur').textContent = mmss(t);
  playhead(sc, t);
  document.getElementById('rWave').innerHTML = waveSVG(sc, 700, 46, t);
  const w = Math.floor(t / 1.5) * 1.5;               // 3초 창 단위로만 패널 갱신
  if (w !== LAST_WIN) { LAST_WIN = w; _selectSeg(w, true); playhead(sc, t); }
  RAF = setTimeout(tick, 150);
}

function playerNote(card, msg, tone) {
  let n = card.parentElement.querySelector('.audionote');
  if (!n) { n = document.createElement('p'); n.className = 'note audionote'; card.parentElement.appendChild(n); }
  n.textContent = msg;
  n.style.color = tone === 'warn' ? 'var(--red)' : 'var(--mut)';
  return n;
}

/* 예시 통화 = 음성 파일이 없다. 화면에 분명히 표시해 준다. */
function disablePlayer() {
  const card = document.querySelector('#scr-result .player');
  if (!card) return;
  if (AUD) { AUD.pause(); clearTimeout(RAF); }
  CUR_ID = null;
  const btn = card.querySelector('.pb');
  btn.textContent = '▶';
  btn.style.opacity = '.45';
  btn.style.cursor = 'not-allowed';
  btn.onclick = () => playerNote(card,
    '예시 통화라 음성 파일이 없어요. 설정 화면에서 내 음성 파일을 올리면 실제로 들을 수 있습니다.', 'warn');
  card.querySelectorAll('button').forEach(b => { if (/×/.test(b.textContent)) b.onclick = null; });
  const wave = document.getElementById('rWave');
  if (wave) { wave.onclick = null; wave.style.cursor = 'default'; }
  playerNote(card, '예시 통화 · 재생 불가 — 파일을 올리면 이 구간을 실제로 들을 수 있습니다');
}

function attachPlayer(id) {
  const card = document.querySelector('#scr-result .player');
  if (!card) return;
  if (CUR_ID === id && AUD) return;                 // 이미 연결돼 있으면 그대로
  if (AUD) { AUD.pause(); AUD.src = ''; clearTimeout(RAF); }
  CUR_ID = id;

  AUD = new Audio(`${API}/analyses/${id}/audio`);
  AUD.preload = 'metadata';
  LAST_WIN = -1;

  const btn = card.querySelector('.pb');
  btn.textContent = '▶';
  btn.style.opacity = '1';
  btn.style.cursor = 'pointer';
  btn.onclick = () => {
    if (AUD.paused) { AUD.play().catch(err => note('재생할 수 없어: ' + err.message)); }
    else AUD.pause();
  };
  AUD.onplay = () => { btn.textContent = '‖'; clearTimeout(RAF); tick(); };
  AUD.onpause = () => { btn.textContent = '▶'; clearTimeout(RAF); };
  AUD.onended = () => { btn.textContent = '▶'; clearTimeout(RAF); };
  AUD.onerror = () => note('음성을 불러오지 못했어 (재생 없이 결과만 표시)');

  // 배속 버튼
  const sp = [...card.querySelectorAll('button')].find(b => /×/.test(b.textContent));
  if (sp) sp.onclick = () => {
    SPD = (SPD + 1) % SPEEDS.length;
    AUD.playbackRate = SPEEDS[SPD];
    sp.textContent = SPEEDS[SPD].toFixed(2).replace(/0$/, '') + '×';
  };

  // 파형을 클릭해도 그 위치로 이동
  const wave = document.getElementById('rWave');
  wave.style.cursor = 'pointer';
  wave.onclick = e => {
    const b = wave.getBoundingClientRect();
    const t = Math.max(0, Math.min(scene().dur, (e.clientX - b.left) / b.width * scene().dur));
    AUD.currentTime = t;
    window.selectSeg(Math.round(t / 1.5) * 1.5);
  };

  const note = m => playerNote(card, m, 'warn');
  playerNote(card, '내 음성 · 그래프나 파형을 누르면 그 구간부터 들을 수 있습니다');
  AUD.onloadedmetadata = () => {
    document.getElementById('rDur').textContent = '/ ' + mmss(AUD.duration);
  };
}

/* 설정 화면이 그려질 때마다 후킹 */
const _renderSetup = window.renderSetup;
window.renderSetup = function () {
  _renderSetup();
  liveBadge(); attachUpload();
  const btn = document.getElementById('goAna');
  const prev = btn.onclick;
  btn.onclick = () => {
    if (REJECT_MSG && !PICKED) { alert(REJECT_MSG); return; }   // 용량 초과 파일은 조용히 넘어가지 않게
    return (LIVE && PICKED) ? runLive() : prev();
  };
  if (LIVE && PICKED) {
    const rev = document.getElementById('review');
    rev.insertAdjacentHTML('beforeend',
      `<div><p>처리 방식</p><p style="color:var(--red)">서버 추론 (FastAPI → 워커)</p></div>`);
  }
};

/* 예시 통화 버튼을 누르면 '용량 초과' 상태를 푼다 */
document.addEventListener('click', e => {
  if (!e.target.closest('#optSample button')) return;
  REJECT_MSG = ''; PICKED = null;
  const lb = document.querySelector('#scr-setup .drop p:nth-of-type(2)');
  if (lb) lb.textContent = '';
});

/* 결과 화면이 그려질 때마다: 내 음성이면 플레이어 연결, 예시면 비활성 표시 */
const _renderResult = window.renderResult;
window.renderResult = function () {
  _renderResult();
  if (LIVE && S.sample === 'live' && SCENES.live && SCENES.live.id) attachPlayer(SCENES.live.id);
  else disablePlayer();
};


/* ══════════════════════════════════════════════════════════════
   대시보드 — 서버 집계(/stats)로 채우기
   ══════════════════════════════════════════════════════════════ */
let DASH_AT = 0;
async function loadDash(force) {
  if (!LIVE) return;
  if (!force && Date.now() - DASH_AT < 5000) return;      // 과한 호출 방지
  try {
    const r = await fetch(`${API}/stats?domain=${S.domain}`, { cache: 'no-store' });
    if (!r.ok) throw new Error(r.statusText);
    window.DASH_DATA = await r.json();
    DASH_AT = Date.now();
    if (S.screen === 'dash') _renderDash();               // 받아온 값으로 다시 그림
  } catch (e) {
    console.warn('[live] 집계를 못 받아옴 — 예시 데이터로 표시', e);
    window.DASH_DATA = null;
  }
}

setInterval(() => { if (LIVE && S.screen === 'dash') loadDash(false); }, 10000);  // 보고 있는 동안 10초마다 갱신

const _renderDash = window.renderDash;
window.renderDash = function () {
  if (LIVE && !window.DASH_DATA) {                        // 처음 들어오면 로딩 표시 후 채움
    _renderDash();
    const t = document.getElementById('dFlag');
    if (t) { t.textContent = '불러오는 중…'; }
    loadDash(true);
    return;
  }
  _renderDash();
  loadDash(false);                                        // 들어올 때마다 갱신
};

/* 현장을 바꾸면 집계도 그 현장 기준으로 다시 */
document.addEventListener('click', e => {
  if (!LIVE) return;
  if (e.target.closest('#optDomain button') || e.target.closest('[data-domain]')) window.DASH_DATA = null;
});

/* 오분류 신고를 실제 API로 */
document.addEventListener('click', async e => {
  const b = e.target.closest('#rActs button');
  if (!b || !/오분류/.test(b.textContent) || !LIVE || S.sample !== 'live') return;
  const s = segAt(scene(), S.sel + 1.5);
  try {
    await fetch(`${API}/feedback`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_id: SCENES.live.id, segment_idx: Math.round(S.sel / 1.5),
        said: s[1], correct: 'unknown', note: '데모 화면에서 신고'
      })
    });
    b.textContent = '신고 완료 — 재학습 데이터로 쌓였습니다';
  } catch (_) { }
});

(async () => {
  LIVE_INFO = await apiHealth();
  LIVE = !!(LIVE_INFO && LIVE_INFO.ok);
  if (LIVE && LIVE_INFO.max_upload_mb) MAX_MB = LIVE_INFO.max_upload_mb;
  console.log(LIVE ? '[live] API 연결됨' : '[live] API 없음 — 예시 데이터로 동작');
  if (document.getElementById('scr-setup')) { liveBadge(); attachUpload(); }
})();


/* ══════════════════════════════════════════════════════════════
   시스템 상태 — 컨테이너·모델·큐가 실제로 살아 있는지 (/system)
   대시보드를 보는 동안 5초마다 갱신한다.
   ══════════════════════════════════════════════════════════════ */
const SYS_EL = () => document.getElementById('dSys');

function sysCard(cls, title, big, sub) {
  return `<div class="sc ${cls}"><h4><i></i>${title}</h4><p>${big}</p><p>${sub}</p></div>`;
}

function renderSys(s) {
  const el = SYS_EL(); if (!el) return;
  if (!s) { el.innerHTML = ''; return; }

  const w = s.worker || {}, m = s.model || {}, q = s.queue || {}, st = s.store || {};
  const mmss = (v) => {
    if (v == null) return '—';
    const h = Math.floor(v / 3600), mn = Math.floor((v % 3600) / 60);
    return h ? `${h}시간 ${mn}분` : (mn ? `${mn}분` : `${Math.round(v)}초`);
  };
  const stateKo = { idle: '대기 중', busy: '분석 중', loading: '모델 로딩 중' };

  const cards = [];

  // ① API 컨테이너
  cards.push(sysCard('ok', 'api 컨테이너',
    'FastAPI 정상',
    `가동 ${mmss(s.api && s.api.uptime_sec)} · 이 화면이 받은 응답`));

  // ② 워커 컨테이너
  cards.push(sysCard(w.ok ? (w.state === 'busy' ? 'wait' : 'ok') : 'bad', 'worker 컨테이너',
    w.ok ? (stateKo[w.state] || w.state) : '응답 없음',
    w.ok ? `심박 ${w.age_sec}초 전 · 처리 ${w.processed || 0}건${w.failed ? ` · 실패 ${w.failed}` : ''}`
         : '컨테이너가 내려갔거나 심박이 끊겼습니다'));

  // ③ 모델
  const mok = m.loaded && !m.mock;
  cards.push(sysCard(m.mock ? 'wait' : (mok ? 'ok' : 'bad'), '모델',
    m.mock ? '가짜 모드(mock)' : (m.loaded ? `${m.version} 로드됨` : '아직 로드 안 됨'),
    m.mock ? '체크포인트 없이 시연 중'
           : `${(m.device || 'cpu').toUpperCase()} 추론 · ${m.ckpt_mb ? m.ckpt_mb + 'MB' : ''} · ${m.win_sec}초 창 / ${m.hop_sec}초 간격`));

  // ④ Supabase
  cards.push(sysCard(st.ok ? 'ok' : 'bad', 'Supabase',
    st.ok ? `연결 ${st.latency_ms}ms` : '연결 실패',
    st.ok ? '통화 · 3초 구간 · 신고 3테이블' : 'REST 응답이 없습니다'));

  // ⑤ 큐
  const backed = (q.queued || 0) > 0;
  cards.push(sysCard(backed ? 'wait' : 'ok', '작업 큐',
    backed ? `대기 ${q.queued}건` : '밀린 작업 없음',
    `분석 중 ${q.running || 0} · 완료 ${q.done || 0}${q.failed ? ` · 실패 ${q.failed}` : ''}`));

  el.innerHTML = cards.join('');
}


/* 분석 완료 연출 — 게이지를 100%까지 채우고 "완료"를 보여준 뒤 넘어간다.
   (서버가 끝냈다고 바로 화면을 바꾸면 63%에서 툭 끊긴 것처럼 보인다) */
function finishAna(sec, windows) {
  return new Promise(res => {
    try { if (typeof anaTL !== 'undefined' && anaTL) anaTL.pause(); } catch (e) {}
    const bar = document.getElementById('anaBar');
    const pct = document.getElementById('anaPct');
    const eta = document.getElementById('anaEta');
    if (!bar) return res();

    const rows = [...document.querySelectorAll('#anaSteps .pstep')];
    // 구간 수는 서버가 실제로 자른 개수로 바꿔준다 (예시 값이 남지 않게)
    if (windows && rows[1]) {
      const sub = rows[1].querySelector('p');
      if (sub) sub.textContent = `${windows}개 구간 · 1.5초씩 겹침`;
    }
    const cur = parseFloat(bar.style.width) || 0;
    const o = { p: cur };

    // 남은 단계를 하나씩 체크 — 마지막 두 단계는 실제로 서버가 방금 끝낸 일이다
    rows.forEach((r, i) => {
      setTimeout(() => {
        r.classList.add('on');
        r.classList.remove('run');
        r.classList.add('done');
        const sp = r.querySelector('span');
        if (sp && !/s$/.test(sp.textContent)) sp.textContent = '완료';
      }, 60 * i);
    });

    anime({
      targets: o, p: 100,
      duration: Math.max(520, (100 - cur) * 11),
      easing: 'easeOutCubic',
      update: () => {
        bar.style.width = o.p + '%';
        if (pct) pct.textContent = Math.round(o.p) + '%';
        if (eta) eta.textContent = '마무리 중';
      },
      complete: () => {
        if (pct) pct.textContent = '100%';
        if (eta) eta.textContent = `완료 · ${sec}초 · ${windows}개 구간 분석`;
        if (bar) bar.style.background = '#1E7F4E';
        setTimeout(() => { if (bar) bar.style.background = ''; res(); }, 700);
      }
    });
  });
}

let SYS_AT = 0;
async function loadSys(force) {
  if (!LIVE) return;
  if (!force && Date.now() - SYS_AT < 4000) return;
  try {
    const r = await fetch(`${API}/system`, { cache: 'no-store' });
    if (!r.ok) throw new Error(r.statusText);
    const s = await r.json();
    SYS_AT = Date.now();
    renderSys(s);
  } catch (e) {
    const el = SYS_EL();
    if (el) el.innerHTML = sysCard('bad', 'api 컨테이너', '응답 없음',
      '서버가 내려갔거나 주소가 다릅니다');
  }
}

setInterval(() => { if (LIVE && S.screen === 'dash') loadSys(false); }, 5000);

/* 대시보드에 들어올 때 바로 한 번 */
const _renderDash2 = window.renderDash;
window.renderDash = function () {
  _renderDash2.apply(this, arguments);
  if (LIVE) loadSys(true);
};
