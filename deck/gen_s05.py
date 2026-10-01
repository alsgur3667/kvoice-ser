# -*- coding: utf-8 -*-
# 05 아키텍쳐 — FastAPI · Supabase · Docker (1920x1080, 절대배치)
S='/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides/s05b.html'

INK='#F5F0EA'; INK2='#B5A9AE'; INK3='#8E8188'
SURF='#1C1620'; SURF2='#241C29'; LINE='#362C38'
GOLD='#F2B63D'; RED='#E8433F'; GREEN='#6FD08C'; BLUE='#9BB7E8'; TEAL='#4FC3B5'; PURP='#B79CEB'

def icon(name, color, size=28):
    return f'<x-icon name="{name}" style="width:{size}px; height:{size}px; color:{color}"></x-icon>'

def chip(text):
    return (f'<p style="display:flex; align-items:center; gap:6px; font-family:Oswald, sans-serif; font-size:15px; '
            f'font-weight:600; letter-spacing:1.5px; color:#9BB7E8; background:#1A2330; border:1px solid #2C3A4F; '
            f'border-radius:999px; padding:3px 12px 3px 9px">{icon("Box", BLUE, 16)}{text}</p>')

def card(x, y, w, h, accent, inner, extra=''):
    return (f'<div style="position:absolute; left:{x}px; top:{y}px; width:{w}px; height:{h}px; background:{SURF}; '
            f'border:1px solid {LINE}; border-top:4px solid {accent}; border-radius:16px; padding:18px 18px 16px; '
            f'display:flex; flex-direction:column; gap:10px{extra}">{inner}</div>')

def head(ic, color, title, sub, right=''):
    return (f'<div style="display:flex; align-items:center; gap:12px">{icon(ic, color, 34)}'
            f'<div style="flex:1; display:flex; flex-direction:column; gap:1px">'
            f'<h3 style="font-size:27px; font-weight:700; line-height:1.2; color:{INK}">{title}</h3>'
            f'<p style="font-size:17px; font-weight:400; color:{INK3}">{sub}</p></div>{right}</div>')

def row(ic, color, title, sub, h=None):
    hh = f' height:{h}px;' if h else ''
    return (f'<div style="display:flex; align-items:center; gap:13px; background:{SURF2}; border-radius:10px; padding:9px 14px;{hh}">'
            f'{icon(ic, color, 26)}<div style="display:flex; flex-direction:column; gap:1px">'
            f'<p style="font-size:20px; font-weight:700; line-height:1.25; color:{INK}">{title}</p>'
            f'<p style="font-size:16px; font-weight:300; line-height:1.3; color:{INK2}">{sub}</p></div></div>')

def step(ic, title, sub):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:6px; background:{SURF2}; border-radius:10px; padding:12px 14px">'
            f'<div style="display:flex; align-items:center; gap:9px">{icon(ic, GOLD, 22)}'
            f'<p style="font-size:19px; font-weight:700; color:{INK}; white-space:nowrap">{title}</p></div>'
            f'<p style="font-size:15.5px; font-weight:300; line-height:1.35; color:{INK2}">{sub}</p></div>')

ARROW = '<x-shape kind="arrow-right" style="width:26px; height:14px; background:#6C5F70; align-self:center"></x-shape>'

def sbcol(ic, color, title, sub, items):
    li = ''.join(f'<p style="font-size:15.5px; font-weight:300; line-height:1.45; color:{INK2}">· {t}</p>' for t in items)
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:8px; background:{SURF2}; border-radius:12px; padding:14px 14px">'
            f'<div style="display:flex; align-items:center; gap:9px">{icon(ic, color, 26)}'
            f'<p style="font-size:21px; font-weight:700; color:{INK}">{title}</p></div>'
            f'<p style="font-size:15px; color:{INK3}; line-height:1.3">{sub}</p>'
            f'<div style="display:flex; flex-direction:column; gap:1px; border-top:1px solid {LINE}; padding-top:7px">{li}</div></div>')

def tstep(t, s):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:3px; background:{SURF2}; border-radius:10px; padding:8px 11px">'
            f'<p style="font-size:17px; font-weight:700; color:{INK}; white-space:nowrap">{t}</p>'
            f'<p style="font-size:14.5px; font-weight:300; color:{INK2}; line-height:1.3">{s}</p></div>')

def badge(n, cx, cy, color, label, lx, ly, align='left'):
    ink = '#120E14' if color in (GOLD, GREEN, BLUE) else '#FFF6F2'
    b = (f'<p data-fx-skip="1" class="stepb" data-step="{n}" style="position:absolute; left:{cx-17}px; top:{cy-17}px; width:34px; height:34px; '
         f'border-radius:50%; background:{color}; color:{ink}; font-family:Oswald, sans-serif; font-size:19px; font-weight:600; '
         f'display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 4px #120E14">{n}</p>')
    l = (f'<p data-fx-skip="1" class="stepb" data-step="{n}" style="position:absolute; left:{lx}px; top:{ly}px; '
         f'font-size:17px; font-weight:700; color:{INK}; white-space:nowrap; text-align:{align}; '
         f'text-shadow:0 0 6px #120E14, 0 0 6px #120E14">{label}</p>')
    return b + l

# ---------------- 박스들 ----------------
H = []
# 헤더
H.append(f'''<div style="position:absolute; left:96px; top:62px; display:flex; align-items:center; gap:24px">
  <p style="font-family:Oswald, 'Arial Narrow', sans-serif; font-size:32px; font-weight:600; color:{INK}; background:{RED}; border-radius:12px; padding:8px 22px">05</p>
  <h2 style="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif; font-size:50px; font-weight:400; line-height:1.15; color:{INK}">아키텍쳐 상세 — FastAPI · Supabase · Docker</h2>
</div>''')
H.append(f'<p style="position:absolute; left:98px; top:146px; font-size:23px; font-weight:300; color:{INK2}">녹취를 올리면 감정 흐름이 그려지기까지 — <b style="color:{INK}">사용자 흐름 ①~⑨</b> 과 <b style="color:{INK}">학습 백엔드 0</b></p>')

# 범례
leg = lambda color, dash, t: (f'<div style="display:flex; align-items:center; gap:10px"><svg width="46" height="10" viewBox="0 0 46 10">'
      f'<line x1="2" y1="5" x2="44" y2="5" stroke="{color}" stroke-width="3" {"stroke-dasharray=&quot;7 6&quot;" if dash else ""}/></svg>'
      f'<p style="font-size:15.5px; color:{INK2}">{t}</p></div>')
H.append(f'''<div style="position:absolute; left:1404px; top:48px; width:420px; background:#15111A; border:1px solid {LINE}; border-radius:12px; padding:12px 16px; display:grid; grid-template-columns:1fr 1fr; gap:6px 12px">
  {leg(GOLD,False,'요청 흐름')}{leg(GREEN,True,'인증 (JWT)')}{leg(BLUE,True,'저장 · 상태')}{leg(RED,True,'모델 배포')}
  <div style="grid-column:1 / span 2; display:flex; align-items:center; gap:8px; border-top:1px solid {LINE}; padding-top:6px">{icon("Box", BLUE, 16)}<p style="font-size:15px; color:{INK2}">= Docker 컨테이너 · <b style="color:{INK}">compose</b> 한 번에 기동</p></div>
</div>''')

# 클라이언트
cl = head('Monitor' if False else 'Users', BLUE, '클라이언트', '브라우저 · 외부 서비스') + \
     row('Mic', BLUE, '웹 앱', '녹취 업로드 · 녹음') + \
     row('LineChart', BLUE, '타임라인 뷰어', '감정 흐름 · 구간 재생') + \
     (f'<div class="dashblk" style="display:flex; flex-direction:column; gap:6px; background:#221A12; border:2px solid {GOLD}; border-radius:10px; padding:9px 12px">'
      f'<div style="display:flex; align-items:center; gap:10px">{icon("Grid", GOLD, 24)}<p style="font-size:20px; font-weight:700; color:{INK}">대시보드</p>'
      f'<p style="font-size:13px; font-weight:700; color:#120E14; background:{GOLD}; border-radius:999px; padding:1px 8px; margin-left:auto">NEW</p></div>'
      f'<p style="font-size:15.5px; line-height:1.35; color:{INK2}"><b style="color:{INK}">서비스 통계</b><br>통화 · 감정 분포 · 위험 통화</p>'
      f'<p style="font-size:15.5px; line-height:1.35; color:{INK2}"><b style="color:{INK}">모델 모니터링</b><br>지연 · 신뢰도 · 보류율</p></div>') + \
     row('Link', BLUE, '외부 연동', '상담 · 교육 시스템 REST')
H.append(card(96, 210, 284, 480, BLUE, cl, '; gap:9px'))

# FastAPI
fa = head('Zap', TEAL, 'FastAPI 추론 서버', '비동기 요청 · 워크플로우 관리') + \
     f'<div style="display:flex; gap:8px; margin:-2px 0 2px">{chip("api")}</div>' + \
     row('Link', TEAL, 'REST API · WebSocket', '업로드 · 조회 · 진행률 · Rate Limit', 62) + \
     row('Filter', TEAL, 'Pydantic 검증', '형식 · 길이 · 적용 현장', 62) + \
     row('Shield', GREEN, 'JWT 검증', 'Supabase Auth 토큰 확인', 62) + \
     row('Workflow', TEAL, 'Job Orchestrator', '작업 생성 · 큐 적재', 62) + \
     row('List', TEAL, 'Job Status API', '진행률 · 타임라인 조회', 62) + \
     row('Chart', GOLD, 'Stats API', '대시보드 집계 · 통계 · 모델 지표', 62)
H.append(card(520, 210, 360, 560, TEAL, fa, '; gap:8px'))

# Redis
rd = f'''<div style="display:flex; align-items:center; gap:12px; height:100%">{icon('Layers', RED, 34)}
  <div style="flex:1; display:flex; flex-direction:column; gap:1px"><h3 style="font-size:26px; font-weight:700; color:{INK}">Redis Queue</h3>
  <p style="font-size:16px; color:{INK3}">작업 대기열 · 상태 캐시</p></div>{chip("redis")}</div>'''
H.append(card(1010, 210, 430, 90, RED, rd, '; padding:12px 18px'))

# 온디바이스 메모 (Redis 오른쪽)
H.append(f'''<div style="position:absolute; left:1470px; top:210px; width:354px; height:94px; background:#231A10; border:2px solid {GOLD}; border-radius:14px; padding:12px 16px; display:flex; flex-direction:column; justify-content:center; gap:3px">
  <p style="font-size:19px; font-weight:700; color:{GOLD}">GPU 없이도 돈다</p>
  <p style="font-size:15.5px; font-weight:300; color:{INK2}; line-height:1.4">CPU 추론 RTF 0.057 · int8 197MB<br>워커는 노트북 · 사내 서버 어디서든</p>
</div>''')

# 추론 워커 (뒤에 겹친 카드로 ×N 표현)
for off, op in ((16, .35), (8, .6)):
    H.append(f'<div data-fx-skip="1" style="position:absolute; left:{1010+off}px; top:{350+off}px; width:814px; height:280px; background:{SURF}; border:1px solid {LINE}; border-radius:16px; opacity:{op}"></div>')
wk = head('Cpu', GOLD, '추론 워커', '큐에서 작업을 꺼내 분석 — 컨테이너만 늘리면 처리량 증가',
          f'<div style="display:flex; gap:8px; align-items:center">{chip("worker × N")}'
          f'<p style="font-size:15px; font-weight:700; color:{GOLD}; background:#3B2E1A; border-radius:999px; padding:4px 12px">스케일 아웃</p></div>') + \
     f'<div style="display:flex; gap:8px; align-items:stretch">' + \
       step('Wave', '전처리', '16kHz · 정규화 · 무음 제거') + ARROW + \
       step('Clock', '3초 창 분할', '1.5초 간격 슬라이딩') + ARROW + \
       step('Cpu', 'WavLM 추론', '7감정 + 긍부정 · 각성도') + ARROW + \
       step('Settings', '후처리', '현장 매핑 · 신뢰도 0.70 · 타임라인') + \
     '</div>' + \
     f'<div style="display:flex; align-items:center; gap:8px">{icon("Folder", RED, 18)}<p style="font-size:15.5px; color:{INK3}"><b style="color:{INK2}">Model Loader</b> — 기동할 때 Storage의 best.pt를 한 번 불러와 메모리에 올린다</p></div>'
H.append(card(1010, 350, 814, 280, GOLD, wk, '; gap:12px'))

# Supabase
sb = head('Database', GREEN, 'Supabase', '인증 · 데이터베이스 · 스토리지 · 실시간을 한 곳에서') + \
     '<div style="display:flex; gap:12px; flex:1">' + \
       sbcol('Key', GREEN, 'Auth', '회원 · JWT 발급', ['로그인 · 토큰', 'RLS: 내 녹취만 조회']) + \
       sbcol('Database', GREEN, 'PostgreSQL', '작업 · 결과 · 지표', ['jobs: 상태 · 진행률', 'segments · results', 'metrics: 모델 지표']) + \
       sbcol('Folder', GREEN, 'Storage', '파일 저장소', ['원본 녹취', '결과 JSON', '모델 best.pt']) + \
       sbcol('Bell', GREEN, 'Realtime', '변경 즉시 push', ['진행률 갱신', '완료 알림', '타임라인 즉시 표시']) + \
     '</div>'
H.append(card(1010, 700, 814, 300, GREEN, sb))

# 학습 파이프라인
tr = head('Cpu', PURP, '학습 파이프라인 · GPU 서버 RTX 4090 ×2', '서비스와 분리 — 새 모델은 Storage에 올리기만 하면 교체',
          chip('train · CUDA')) + \
     '<div style="display:flex; gap:6px; align-items:stretch">' + \
       tstep('AI-Hub+SKT', '4.4만 + 확장') + ARROW + \
       tstep('16kHz 캐시', '1회 변환') + ARROW + \
       tstep('화자 분할', '암기 차단') + ARROW + \
       tstep('WavLM 학습', 'bf16') + ARROW + \
       tstep('best.pt', 'UAR 0.734') + \
     '</div>'
H.append(card(96, 815, 784, 185, PURP, tr, '; gap:9px; padding:14px 16px 14px'))

# ---------------- 연결선 (SVG, 박스 아래 레이어) ----------------
def mk(id_, color, start=False):
    return (f'<marker id="{id_}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="{"auto-start-reverse" if start else "auto"}"><path d="M0 0 L10 5 L0 10 z" fill="{color}"/></marker>')
def path(d, color, step, dashed=False, both=False, mid=''):
    dash = ' stroke-dasharray="8 7"' if dashed else ''
    ms = f' marker-start="url(#{mid}s)"' if both else ''
    return (f'<path class="flow" data-step="{step}" data-dashed="{1 if dashed else 0}" d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linejoin="round"{dash} marker-end="url(#{mid})"{ms}/>')

svg = f'''<svg data-fx-skip="1" width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute; left:0; top:0; width:1920px; height:1080px; pointer-events:none">
<defs>{mk("mg",GOLD)}{mk("mgs",GOLD,True)}{mk("mb",BLUE)}{mk("mr",RED)}{mk("mn",GREEN)}{mk("mns",GREEN,True)}</defs>
{path("M380 346 H531", GOLD, 1, mid="mg")}
{path("M238 690 V795 H1002", GREEN, 2, dashed=True, both=True, mid="mn")}
{path("M880 720 H1002", BLUE, 3, dashed=True, mid="mb")}
{path("M880 255 H1002", GOLD, 4, mid="mg")}
{path("M1200 300 V342", GOLD, 5, mid="mg")}
{path("M1319 650 V692", BLUE, 6, dashed=True, mid="mb")}
{path("M1711 1000 V1046 H58 V403 H88", BLUE, 7, dashed=True, mid="mb")}
{path("M388 403 H470 V640 H531", GOLD, 8, both=True, mid="mg")}
{path("M388 540 H440 V710 H531", GOLD, 9, both=True, mid="mg")}
{path("M880 940 H1002", RED, 0, dashed=True, mid="mr")}
{path("M1515 700 V656", RED, 0, dashed=True, mid="mr")}
</svg>'''

badges = ''.join([
  badge(0, 945, 940, RED,  '모델 배포', 907, 900),
  badge(0, 1515, 675,  RED,  '모델 로드', 1540, 664),
  badge(1, 440, 346,  GOLD,  '업로드',     412, 305),
  badge(2, 238, 742,  GREEN, 'JWT 인증',   262, 731),
  badge(3, 945, 720,  BLUE,  '작업 생성',   905, 680),
  badge(4, 945, 255,  GOLD,  '큐 적재',    913, 215),
  badge(5, 1200, 321, GOLD,  '작업 전달',   1226, 310),
  badge(6, 1319, 671, BLUE,  '결과 저장',   1344, 660),
  badge(7, 560, 1046, BLUE,  '진행률 · 완료 실시간 push', 586, 1010),
  badge(8, 470, 480,  GOLD,  '타임라인<br>조회', 390, 430),
  badge(9, 440, 640,  GOLD,  '대시보드 집계', 396, 722),
])

notes = '''<aside>■ 한 줄로: 녹취를 올리면 감정 흐름 그래프가 뜨기까지, 뒤에서 뭐가 어떤 순서로 도는지.
■ 먼저 0번(빨강): 학습은 GPU 서버에서 따로 해. 다 되면 best.pt를 Supabase Storage에 올리고, 워커가 켜질 때 그걸 한 번 불러와. 서비스 쪽 코드를 안 건드리고 모델만 갈아끼울 수 있다는 게 포인트야.
■ 사용자 흐름 ①~⑨:
① 웹에서 녹취를 올려 (FastAPI가 받아).
② 그 전에 로그인 — Supabase Auth가 JWT 토큰을 주고, FastAPI가 그 토큰을 확인해. RLS 덕분에 남의 녹취는 DB 단에서 아예 못 봐.
③ FastAPI가 원본을 Storage에 저장하고 jobs 테이블에 "작업 1건"을 만들어.
④ 작업을 Redis 큐에 넣고, 사용자한텐 바로 "접수됐어요"를 돌려줘. 3분짜리 녹취를 붙잡고 기다리게 하지 않는 게 비동기의 핵심.
⑤ 놀고 있는 워커가 큐에서 작업을 꺼내가. 16kHz로 바꾸고 → 3초씩 잘라서 → WavLM으로 감정 뽑고 → 현장 규칙 적용해서 타임라인을 만들어.
⑥ 3초 구간별 결과를 segments 테이블에, 전체 결과를 Storage에 저장해.
⑦ DB가 바뀌면 Supabase Realtime이 브라우저로 바로 쏴줘. 새로고침 안 해도 진행률이 올라가고, 끝나면 그래프가 뜨지.
⑧ 사용자가 그래프에서 튄 구간을 누르면 Job Status API로 그 구간 정보를 가져와서 바로 재생해.
⑨ 대시보드(새로 추가, 금색 테두리): Stats API가 Postgres에 쌓인 결과를 모아서 보여줘. 두 가지야 — 서비스 통계(오늘 통화 수, 감정 분포, 위험 통화 목록, 상담사별 부정 감정)와 모델 모니터링(워커가 metrics 테이블에 남긴 처리 지연·신뢰도·판단 보류 비율). 보류 비율이 올라가면 "모델이 요즘 들어오는 목소리를 낯설어한다"는 신호라 재학습 시점을 알 수 있어.
■ Docker: 파란 칩 붙은 건 다 컨테이너야. api · redis · worker는 docker compose 파일 하나로 같이 켜지고, 학습은 CUDA 이미지로 따로. 워커 컨테이너 수만 늘리면 동시에 처리할 수 있는 녹취가 늘어나(스케일 아웃).
■ 왜 Supabase냐: 인증·DB·파일 저장·실시간 알림을 따로따로 만들면 2인 팀이 일주일에 못 끝내. 하나로 해결되니까 우리는 모델이랑 흐름 분석에 집중할 수 있어.
■ 예상 질문: "Redis 꼭 필요해?" → 규모가 작으면 Postgres jobs 테이블로도 큐를 대신할 수 있어. 그래도 녹취가 몰릴 때 API가 멈추지 않게 하려고 분리했다고 하면 돼.
■ 이렇게 말하면 돼: "업로드는 바로 받고, 분석은 뒤에서 워커가 하고, 결과는 실시간으로 밀어줍니다. 모델은 학습 서버에서 따로 만들어 갈아끼웁니다."</aside>'''

html = (f'<section id="s05b" data-transition="push" style="background:#120E14; color:{INK}; '
        f"font-family:'Noto Sans KR', Arial, sans-serif\">\n" + svg + '\n' + '\n'.join(H) + '\n' + badges + '\n' + notes + '\n</section>\n')
open(S,'w',encoding='utf-8').write(html)
print('s05 written', len(html))
