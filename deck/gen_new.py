# -*- coding: utf-8 -*-
"""피드백 반영 신규 슬라이드 (9/22): 데이터 여정 · 감정별 음성 · EDA 시각화 2장 · 전처리 시각화 2장 · 불균형 · 학습 요약 · 간트"""
import json, base64, os
SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"
AS = "/root/deck_html/assets"
AUD = json.load(open(os.path.join(AS, "audio.json")))
def b64img(p): return "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(AS, p), "rb").read()).decode()

INK = "#F5F0EA"; INK2 = "#D2C8CD"; SUB = "#ADA1A7"; DIM = "#7A6E74"
RED = "#E8433F"; GOLD = "#F2B63D"; CARD = "#1C1620"; CARD2 = "#241C29"; LINE = "#362C38"
EMO = {'angry': ('분노', '#E8433F'), 'sadness': ('슬픔', '#5B84D6'), 'happy': ('기쁨', '#F2B63D'),
       'neutral': ('중립', '#A7A1AB'), 'fear': ('공포', '#9B7BD6'), 'disgust': ('혐오', '#4FA37A'),
       'surprise': ('놀람', '#E58BC0')}
C7 = ['angry', 'sadness', 'happy', 'neutral', 'fear', 'disgust', 'surprise']
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"


def sec(sid, badge, title, body, notes, bg="#120E14", nozone=False):
    nz = ' data-nozone="1"' if nozone else ''
    b = (f'<p style="{OS}; font-size:34px; font-weight:600; color:{INK}; background:{RED}; border-radius:12px; padding:10px 24px">{badge}</p>'
         if badge else '')
    return f'''<section id="{sid}" data-transition="push"{nz} style="background:{bg}; color:{INK}; font-family:'Noto Sans KR', Arial, sans-serif; padding:104px 128px 120px; display:flex; flex-direction:column; gap:26px">
  <div style="display:flex; align-items:center; gap:28px">
    {b}
    <h2 style="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif; font-size:66px; font-weight:400; line-height:1.15; color:{INK}">{title}</h2>
  </div>
{body}
  <aside>{notes}</aside>
</section>
'''


def wave_svg(peaks, w, h, color, gap=0.35):
    n = len(peaks); bw = w / n
    rects = []
    for i, p in enumerate(peaks):
        hh = max(2, p * h * 0.95)
        rects.append(f'<rect x="{i*bw + bw*gap/2:.1f}" y="{(h-hh)/2:.1f}" width="{bw*(1-gap):.1f}" height="{hh:.1f}" rx="{bw*(1-gap)/2:.1f}"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block"><g fill="{color}">{"".join(rects)}</g></svg>'


def player(aid, peaks, w, h, color):
    """재생되는 파형: 아래는 흐린 막대, 위(.pfill)는 재생 진행만큼 밝은 막대"""
    return (f'<div style="position:relative; width:{w}px; height:{h}px">'
            f'<div style="position:absolute; inset:0; opacity:.32">{wave_svg(peaks, w, h, color)}</div>'
            f'<div class="pfill" style="position:absolute; left:0; top:0; height:{h}px; width:0; overflow:hidden">{wave_svg(peaks, w, h, color)}</div>'
            f'</div>')


def audio_tag(aid, key):
    return f'<audio id="{aid}" preload="auto" src="data:audio/mpeg;base64,{AUD[key]["mp3"]}"></audio>'


slides = {}

# ───────────────────────── 1. 날짜별 데이터 여정 ─────────────────────────
def node(date, title, big, sub, color=GOLD, w=None):
    return f'''<div class="tnode" style="flex:1; display:flex; flex-direction:column; gap:8px; background:{CARD}; border:1px solid {LINE}; border-top:4px solid {color}; border-radius:14px; padding:20px 22px">
      <p style="{OS}; font-size:22px; font-weight:600; color:{color}; letter-spacing:.04em">{date}</p>
      <p style="font-size:24px; font-weight:700; color:{INK}">{title}</p>
      <p style="{OS}; font-size:46px; font-weight:600; line-height:1.05; color:{INK}" data-count>{big}</p>
      <p style="font-size:20px; line-height:1.45; color:{SUB}; word-break:keep-all">{sub}</p>
    </div>'''
arrow = f'<p class="tarr" style="align-self:center; font-size:30px; color:#6C5F70">→</p>'
def lane(label, color, nodes):
    return f'''<div style="display:flex; flex-direction:column; gap:12px">
    <p style="font-size:22px; font-weight:700; color:{color}">● {label}</p>
    <div style="display:flex; gap:12px; align-items:stretch">{arrow.join(nodes)}</div>
  </div>'''
body = lane("AI-Hub 감정 대화 음성 — 학습 기준 데이터", GOLD, [
    node("9/14", "수집", "43,991", "CSV 3종 · 48kHz mono<br>평가자 5명 투표 라벨"),
    node("9/14", "라벨 재정의", "39,188", "동점·전원 불일치<br>4,803개 제외"),
    node("9/15", "전처리", "39,180", "16kHz · 무음 제거 · 정규화<br>0.8초 미만 8개 제외"),
    node("9/15", "화자 독립 분할", "31,162", "train 79명 · val 3,178 16명<br>test 4,840 16명"),
]) + lane("SKT 감정 음성 — 희소 감정 보강용", "#5B84D6", [
    node("9/17", "확보", "151,680", "화자 8명 · 감정 16종<br>48kHz 스튜디오 낭독", "#5B84D6"),
    node("9/22", "7감정 매핑", "119,411", "매핑 안 되는 9종<br>32,269개 제외", "#5B84D6"),
    node("9/22", "전처리", "115,062", "0.8초 미만 4,349개 제외<br>126.6시간", "#5B84D6"),
    node("9/22", "혼합 학습", "71,162", "SKT train 4명에서 4만 개 균형 추출<br>+ AI-Hub train 31,162", "#5B84D6"),
]) + f'''
  <div style="display:flex; gap:14px">
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px; display:flex; gap:18px; align-items:center"><p style="{OS}; font-size:22px; color:#6FD08C">9/16</p><p style="font-size:22px; color:{INK2}">외부 검증 — 학습에 없던 목소리로 시험 · 학습에 없던 목소리로 시험</p></div>
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px; display:flex; gap:18px; align-items:center"><p style="{OS}; font-size:22px; color:{SUB}">다음</p><p style="font-size:22px; color:{INK2}">방언 발화(지역별 편향 평가) · 자체 녹음(실제 대화체)</p></div>
  </div>'''
slides["dtimeline"] = sec("dtimeline", "02", "데이터가 늘어난 순서 — 9/14부터 9/23까지", body,
"""■ 한 줄로: 데이터가 날짜별로 어떻게 들어오고 줄어들었는지 한눈에.
■ 위 줄(AI-Hub): 9/14 4만 4천 개를 받았고, 5명 의견이 동점이거나 다 갈린 4,803개를 뺐어. 9/15 16kHz로 바꾸면서 너무 짧은 8개를 더 빼서 39,180개. 사람 단위로 나눠서 학습 31,162개(79명), 검증 3,178개(16명), 시험 4,840개(16명).
■ 아래 줄(SKT): 9/17 15만 개 확보. 감정이 16종이라 우리 7감정에 맞는 것만 남기니 11만 9천 개. 전처리 후 11만 5천 개. 그중 학습용 화자 4명에서 감정·화자별로 골고루 4만 개를 뽑아 AI-Hub와 섞었어.
■ 이렇게 말하면 돼: "데이터는 매일 숫자로 기록하면서 줄여나갔습니다. 버린 데이터도 왜 버렸는지 다 셀 수 있습니다." """)

# ───────────────────────── 2. 감정별 음성 ─────────────────────────
META = {'angry': ('이번에는 만나면 진짜 제대로 얘기 한번 해볼라고.', '20대 남성'),
        'sadness': ('그 사람이랑 헤어졌어.', '40대 여성'),
        'happy': ('나 드디어 프로젝트가 끝났어.', '40대 여성'),
        'neutral': ('힘들어도 그냥 해야지.', '20대 남성'),
        'fear': ('나 아무래도 갇힌 것 같아.', '40대 여성'),
        'disgust': ('으! 누가 화장실에 토하고 안 치웠어.', '30대 남성'),
        'surprise': ('나 어제 자다가 깜짝 놀랬어!', '30대 여성')}
cards = []
for k in C7:
    ko, col = EMO[k]; txt, who = META[k]; a = AUD[k]
    cards.append(f'''<div data-audio="aud-{k}" data-dur="{a['dur']}" class="vcard" style="position:relative; display:flex; flex-direction:column; gap:12px; background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:22px 24px; cursor:pointer">
      <div style="display:flex; align-items:center; gap:12px">
        <span class="vbtn" style="width:44px; height:44px; border-radius:50%; background:{col}; display:flex; align-items:center; justify-content:center; flex:none"><svg width="18" height="18" viewBox="0 0 18 18"><path d="M5 3 L15 9 L5 15 Z" fill="#120E14"/></svg></span>
        <p style="font-size:32px; font-weight:800; color:{col}">{ko}</p>
        <p style="{OS}; font-size:20px; color:{SUB}; margin-left:auto">{a['dur']:.1f}s</p>
      </div>
      {player(k, a['peaks'], 340, 64, col)}
      <p style="font-size:21px; line-height:1.4; color:{INK2}; word-break:keep-all; min-height:58px">“{txt}”</p>
      <p style="font-size:18px; color:{SUB}">{who} · 평가자 <b style="color:{INK}">5/5</b> 일치</p>
    </div>''')
a = AUD['contrast']
cards.append(f'''<div data-audio="aud-contrast" data-dur="{a['dur']}" class="vcard" style="position:relative; display:flex; flex-direction:column; gap:12px; background:#2A1A1C; border:2px dashed {RED}; border-radius:16px; padding:22px 24px; cursor:pointer">
      <div style="display:flex; align-items:center; gap:12px">
        <span class="vbtn" style="width:44px; height:44px; border-radius:50%; background:{RED}; display:flex; align-items:center; justify-content:center; flex:none"><svg width="18" height="18" viewBox="0 0 18 18"><path d="M5 3 L15 9 L5 15 Z" fill="#120E14"/></svg></span>
        <p style="font-size:22px; font-weight:800; color:{INK}; white-space:nowrap"><span style="color:#4FA37A">혐오</span> 연기 → <span style="color:{RED}">분노</span>로 들림</p>
      </div>
      {player('contrast', a['peaks'], 340, 64, RED)}
      <p style="font-size:21px; line-height:1.4; color:{INK2}; word-break:keep-all; min-height:58px">“그렇다니까. 책임도 못 지면서 키우는 사람들 때문에.”</p>
      <p style="font-size:18px; color:{SUB}">30대 여성 · 5명 <b style="color:{INK}">전원</b> 분노로 들음</p>
    </div>''')
body = f'''  <p style="font-size:24px; color:{INK2}; margin-top:-8px">카드를 누르면 실제 학습 데이터가 재생된다 · 평가자 5명이 모두 같은 감정으로 들은 클립만 골랐다</p>
  <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:18px">
    {''.join(cards)}
  </div>
  {''.join(audio_tag('aud-' + k, k) for k in C7 + ['contrast'])}'''
slides["voices"] = sec("voices", "02", "들어보기 — 7감정, 학습에 쓴 실제 음성", body,
"""■ 한 줄로: 모델이 배운 데이터를 직접 들려주는 장. 카드를 클릭하면 재생돼 (한 번 더 누르면 멈춤).
■ 순서 추천: 분노 → 슬픔 → 기쁨 → 중립 한 두 개만 들려주고, 마지막에 빨간 점선 카드를 꼭 틀어.
■ 빨간 카드: 성우한테는 "혐오로 연기해"라고 지시했는데, 평가자 5명이 전부 "분노"로 들었어. 그래서 우리는 연기 지시가 아니라 사람들이 느낀 감정을 정답으로 썼어. 다음 장 68.1%가 이 얘기야.
■ 고른 기준: 평가자 5명 전원 일치 · 2~4초 · 연기 지시와 사람이 느낀 감정이 같은 것 (빨간 카드만 예외).
■ 이렇게 말하면 돼: "글자는 평범한데 목소리만 들어도 감정이 느껴지시죠? 이게 저희가 텍스트를 빼고 소리만 쓰는 이유입니다." """, nozone=True)

# ───────────────────────── 3. EDA 히트맵 ─────────────────────────
HM = {  # 행=연기 지시, 열=사람이 느낀 감정(다수결), 행 정규화 % · merged_labels.csv 43,991행 실측
 'angry': [58.2, 24.5, 1.6, 9.6, 0.7, 4.7, 0.7], 'sadness': [0.7, 87.8, 2.0, 9.1, 0.3, 0.1, 0.1],
 'happy': [1.1, 3.4, 69.5, 22.8, 0.2, 0.1, 2.9], 'neutral': [6.9, 8.7, 8.9, 66.1, 2.1, 3.6, 3.6],
 'fear': [0.9, 12.0, 1.4, 21.9, 62.5, 0.1, 1.1], 'disgust': [16.1, 13.3, 1.2, 19.0, 0.4, 48.0, 2.0],
 'surprise': [1.4, 9.3, 1.2, 37.9, 6.0, 0.7, 43.5]}
cs = 92
cells = []
for i, r in enumerate(C7):
    for j, c in enumerate(C7):
        v = HM[r][j]; diag = i == j
        if diag:
            bg = f"rgba(242,182,61,{0.25 + v/100*0.75:.2f})"; fc = "#120E14" if v > 55 else INK
        else:
            bg = f"rgba(232,67,63,{min(1, v/40):.2f})" if v >= 1 else "#1C1620"; fc = INK if v >= 8 else SUB
        cells.append(f'<div class="hm" data-r="{i}" data-c="{j}" style="background:{bg}; color:{fc}; display:flex; align-items:center; justify-content:center; {OS}; font-size:22px; font-weight:{600 if diag or v>=15 else 400}; border-radius:6px">{v:.0f}</div>')
hdr = ''.join(f'<div style="display:flex; align-items:end; justify-content:center; font-size:20px; font-weight:700; color:{EMO[c][1]}">{EMO[c][0]}</div>' for c in C7)
rows = ''
for i, r in enumerate(C7):
    rows += f'<div style="display:flex; align-items:center; justify-content:flex-end; padding-right:10px; font-size:20px; font-weight:700; color:{EMO[r][1]}">{EMO[r][0]}</div>' + ''.join(cells[i*7:(i+1)*7])
body = f'''  <div style="display:flex; gap:56px; align-items:flex-start">
    <div style="display:flex; flex-direction:column; gap:10px">
      <p style="font-size:21px; color:{SUB}; padding-left:80px">열 = 평가자 5명이 <b style="color:{INK}">느낀</b> 감정 (다수결) →</p>
      <div style="display:grid; grid-template-columns:70px repeat(7, {cs}px); grid-template-rows:34px repeat(7, {cs-14}px); gap:5px">
        <div></div>{hdr}{rows}
      </div>
      <p style="font-size:21px; color:{SUB}">↑ 행 = 성우에게 준 <b style="color:{INK}">연기 지시</b> ('상황' 컬럼) · 칸 = 행 기준 % · 43,991클립</p>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; gap:18px; padding-top:40px">
      <div style="background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:26px 30px">
        <p style="{OS}; font-size:84px; font-weight:600; line-height:1; color:{GOLD}" data-count>68.1%</p>
        <p style="font-size:26px; font-weight:700; margin-top:10px">연기 지시와 사람이 느낀 감정이 같은 비율</p>
        <p style="font-size:21px; color:{SUB}; margin-top:6px">대각선(금색)이 진할수록 지시대로 들렸다는 뜻</p>
      </div>
      <div style="display:flex; flex-direction:column; gap:12px">
        <p style="font-size:24px; line-height:1.5; color:{INK2}"><b style="color:#4FA37A">혐오</b> 연기의 <b style="color:{INK}">48%</b>만 혐오로 들렸다 — 16%는 <b style="color:{RED}">분노</b>로</p>
        <p style="font-size:24px; line-height:1.5; color:{INK2}"><b style="color:#E58BC0">놀람</b> 연기의 <b style="color:{INK}">38%</b>는 그냥 <b style="color:#A7A1AB">중립</b>으로 들렸다</p>
        <p style="font-size:24px; line-height:1.5; color:{INK2}"><b style="color:{RED}">분노</b> 연기의 <b style="color:{INK}">25%</b>는 <b style="color:#5B84D6">슬픔</b>으로 들렸다</p>
      </div>
      <div style="background:#2A1A1C; border-left:6px solid {RED}; border-radius:8px; padding:18px 24px">
        <p style="font-size:24px; font-weight:700">→ '상황' 컬럼을 버리고 5명 투표로 정답을 다시 만들었다</p>
        <p style="font-size:20px; color:{SUB}; margin-top:6px">다수결 = 정답 감정 · 투표 비율 = 얼마나 확실한지 (soft 라벨)</p>
      </div>
    </div>
  </div>'''
slides["edaheat"] = sec("edaheat", "02", "EDA ① 혐오 연기의 48%만 혐오로 들렸다", body,
"""■ 한 줄로: 데이터에 붙어 있던 감정 라벨을 그대로 믿으면 안 된다는 걸 보여주는 표.
■ 읽는 법: 왼쪽이 성우한테 준 연기 지시, 위쪽이 평가자 5명이 실제로 느낀 감정. 칸 숫자는 그 지시 중 몇 %가 그렇게 들렸는지. 금색 대각선이 "지시대로 들림".
■ 짚을 곳: 혐오 줄 — 48%만 혐오, 16%는 분노, 19%는 중립. 놀람 줄 — 38%가 중립. 슬픔만 88%로 잘 전달됐어.
■ 앞 장 빨간 카드가 바로 이 혐오→분노 칸의 실제 예시야.
■ 이렇게 말하면 돼: "라벨을 의심하는 데서 EDA를 시작했고, 전체의 3분의 1이 지시와 다르게 들린다는 걸 확인해서 정답을 다시 만들었습니다." """)

# ───────────────────────── 4. EDA 분포 3종 ─────────────────────────
CLS = [('sadness', 16856), ('neutral', 8038), ('angry', 7958), ('happy', 4061), ('disgust', 2934), ('fear', 2903), ('surprise', 1241)]
mx = CLS[0][1]
bars = ''.join(f'''<div style="display:flex; align-items:center; gap:12px; height:44px">
        <p style="width:60px; text-align:right; font-size:21px; font-weight:700; color:{EMO[k][1]}">{EMO[k][0]}</p>
        <div class="hbar" style="height:30px; width:{v/mx*330:.0f}px; background:{EMO[k][1]}; border-radius:0 6px 6px 0"></div>
        <p style="{OS}; font-size:21px; color:{INK2}">{v:,}</p></div>''' for k, v in CLS)
SPK = [5932, 3762, 3248, 2936, 1278, 1237, 1196, 1191, 1070, 848, 837, 804, 757, 719, 701, 674, 645, 632, 553, 548, 533, 533, 531, 529, 453, 433, 429, 428, 415, 366, 357, 338, 336, 318, 308, 305, 299, 291, 285, 284, 283, 268, 247, 241, 238, 233, 231, 231, 222, 221, 204, 202, 199, 196, 190, 189, 169, 168, 163, 127, 114, 114, 110, 106, 104, 96, 94, 92, 89, 87, 86, 82, 81, 70, 69, 68, 66, 63, 63, 63, 62, 54, 50, 48, 46, 43, 42, 40, 37, 36, 30, 29, 26, 24, 22, 18, 15, 15, 13, 12, 12, 11, 5, 5, 4, 3, 3, 2, 2, 2, 2]
sw, sh = 470, 250; bw = sw / len(SPK)
spk_svg = f'<svg width="{sw}" height="{sh}" style="display:block">' + ''.join(
    f'<rect class="vbar" x="{i*bw:.2f}" y="{sh - v/SPK[0]*sh:.1f}" width="{max(bw-0.8,1):.2f}" height="{v/SPK[0]*sh:.1f}" fill="{RED if i < 2 else "#6C5F70"}"/>' for i, v in enumerate(SPK)) + '</svg>'
VOT = [(1, 192), (2, 7119), (3, 11739), (4, 11314), (5, 13627)]
vm = 13627
vot = ''.join(f'''<div style="flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:6px; height:250px">
        <p style="{OS}; font-size:19px; color:{INK2}">{v:,}</p>
        <div class="vbar" style="width:58px; height:{v/vm*190:.0f}px; background:{GOLD if n>=4 else ("#8C7A4A" if n>=2 else "#4A3F4E")}; border-radius:6px 6px 0 0"></div>
        <p style="font-size:20px; font-weight:700; color:{INK}">{n}명</p></div>''' for n, v in VOT)
def panel(title, big, bigc, chart, foot, act):
    return f'''<div style="flex:1 1 0; min-width:0; display:flex; flex-direction:column; gap:14px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:26px 28px">
      <div style="display:flex; align-items:baseline; gap:14px"><p style="font-size:26px; font-weight:700">{title}</p><p data-count style="{OS}; font-size:40px; font-weight:600; color:{bigc}; margin-left:auto">{big}</p></div>
      <div style="height:330px; display:flex; flex-direction:column; justify-content:flex-end">{chart}</div>
      <p style="font-size:20px; line-height:1.45; color:{SUB}; word-break:keep-all">{foot}</p>
      <p style="font-size:21px; font-weight:600; color:#F08A7E; word-break:keep-all">{act}</p>
    </div>'''
body = f'''  <div style="display:flex; gap:22px; align-items:stretch">
    {panel("감정별 개수", "13.6:1", GOLD, f'<div style="display:flex; flex-direction:column; gap:2px">{bars}</div>', "슬픔 16,856개 vs 놀람 1,241개. 그냥 학습하면 '다 슬픔'만 찍어도 점수가 나온다", "→ UAR 지표 · 균형 샘플러 · CB-Focal")}
    {panel("화자별 발화 수 (111명)", "22%", RED, spk_svg + f'<p style="font-size:18px; color:{SUB}; margin-top:8px">왼쪽부터 많은 순 · 빨강 = 상위 2명</p>', "상위 2명이 전체의 22%. 섞어서 나누면 모델이 감정이 아니라 목소리를 외운다", "→ 사람 단위로 train · val · test 분할")}
    {panel("같은 감정을 고른 평가자 수", "31%", GOLD, f'<div style="display:flex; gap:8px; align-items:flex-end">{vot}</div>', "5명 중 5명 일치는 31%뿐. 3명 이하 합의가 43% — 사람끼리도 감정 판단이 갈린다", "→ 투표 비율을 soft 라벨로 · 동점·1명 합의 제외")}
  </div>'''
slides["edadist"] = sec("edadist", "02", "EDA ② 슬픔이 놀람의 13.6배 · 화자 2명이 22%", body,
"""■ 한 줄로: 감정·화자·합의도 세 가지 분포를 그려보니 각각 함정이 있었고, 각각 대응했다.
■ 왼쪽(감정별 개수): 슬픔이 놀람의 13.6배. 그대로 학습하면 모델이 슬픔만 찍어. 그래서 정확도 대신 감정별 평균 재현율(UAR)로 채점하고, 적은 감정을 더 자주 보여주는 샘플러를 썼어.
■ 가운데(화자별): 111명인데 상위 2명(빨간 막대)이 22%. 랜덤으로 나누면 같은 사람 목소리가 시험에도 들어가서 점수가 부풀어. 그래서 사람 단위로 나눴어.
■ 오른쪽(합의도): 5명 중 몇 명이 같은 감정을 골랐는지. 5명 전원 일치는 31%뿐이야. 사람도 헷갈리는 샘플이 많다는 거라, 투표 비율 자체를 정답의 일부(soft 라벨)로 썼어.
■ 이렇게 말하면 돼: "분포 세 개를 그렸더니 함정이 세 개 나왔고, 각각 지표·분할·라벨 방식으로 막았습니다." """)

# ───────────────────────── 5. 전처리 시각화 (실제 클립) ─────────────────────────
raw = AUD['raw']; nrm = AUD['norm']
W = 1060; H = 118
t0, t1 = raw['trim']
def step(no, title, sub, vis, metric, mc=GOLD):
    return f'''<div class="pstep" style="display:flex; gap:26px; align-items:center; background:{CARD}; border:1px solid {LINE}; border-radius:14px; padding:16px 24px">
      <div style="width:260px; flex:none"><p style="{OS}; font-size:22px; color:{RED}">STEP {no}</p><p style="font-size:26px; font-weight:700">{title}</p><p style="font-size:19px; color:{SUB}; line-height:1.4; margin-top:4px; word-break:keep-all">{sub}</p></div>
      <div class="pvis" style="width:{W}px; height:{H}px; position:relative; flex:none; border-radius:8px; overflow:hidden; background:#0C090D">{vis}</div>
      <p class="pmet" style="{OS}; font-size:28px; font-weight:600; color:{mc}; line-height:1.2; text-align:right; flex:1">{metric}</p>
    </div>'''
v1 = f'<img src="{b64img("spec48.jpg")}" style="width:100%; height:100%; display:block"><p style="position:absolute; right:10px; top:6px; font-size:16px; color:{INK2}">24kHz</p><p style="position:absolute; right:10px; bottom:4px; font-size:16px; color:{INK2}">0</p>'
v2 = (f'<div class="phatch" style="position:absolute; left:0; right:0; top:0; height:66.7%; background:repeating-linear-gradient(135deg,#1A1418 0 10px,#231B22 10px 20px); display:flex; align-items:center; justify-content:center"><p style="font-size:20px; color:{SUB}">8~24kHz 버림 — 이 대역 에너지는 전체의 <b style="color:{INK}">0.07%</b></p></div>'
      f'<img src="{b64img("spec16.jpg")}" style="position:absolute; left:0; bottom:0; width:100%; height:33.3%; display:block"><p style="position:absolute; right:10px; bottom:{H*0.333-20:.0f}px; font-size:16px; color:{GOLD}">8kHz</p>')
v3 = (f'<div style="position:absolute; inset:9px 0">{wave_svg(raw["peaks"], W, H-18, "#8C7F90")}</div>'
      f'<div class="pcut pcl" style="position:absolute; left:0; top:0; bottom:0; width:{t0*100:.1f}%; background:rgba(12,9,13,.78); border-right:2px dashed {RED}"></div>'
      f'<div class="pcut pcr" style="position:absolute; right:0; top:0; bottom:0; width:{(1-t1)*100:.1f}%; background:rgba(12,9,13,.78); border-left:2px dashed {RED}"></div>'
      f'<p style="position:absolute; left:{(1-t1)*50+t1*100-6:.0f}%; top:6px; font-size:17px; color:{RED}">잘라냄</p>'
      f'<p style="position:absolute; left:4px; top:6px; font-size:17px; color:{RED}">잘라냄</p>')
v4 = (f'<div style="position:absolute; inset:9px 0">{wave_svg(nrm["peaks"], W, H-18, GOLD)}</div>'
      f'<div style="position:absolute; left:0; right:0; top:{9 + (H-18)*(1-0.95)/2:.0f}px; border-top:1px dashed {INK2}"></div>'
      f'<p style="position:absolute; right:8px; top:0px; font-size:15px; color:{INK2}">-1 dBFS</p>')
playbtns = f'''<div style="display:flex; gap:12px; margin-left:auto">
      <div data-audio="aud-raw" data-dur="{raw['dur']}" class="pbtn" style="display:flex; align-items:center; gap:10px; background:{CARD2}; border:1px solid {LINE}; border-radius:999px; padding:10px 20px; cursor:pointer"><span style="color:{INK2}; font-size:20px">▶ 원본 듣기</span><span style="{OS}; color:{SUB}; font-size:18px">{raw['dur']}s</span></div>
      <div data-audio="aud-angry2" data-dur="{AUD['angry']['dur']}" class="pbtn" style="display:flex; align-items:center; gap:10px; background:{CARD2}; border:1px solid {GOLD}; border-radius:999px; padding:10px 20px; cursor:pointer"><span style="color:{GOLD}; font-size:20px">▶ 전처리 후</span><span style="{OS}; color:{SUB}; font-size:18px">{AUD['angry']['dur']}s</span></div>
    </div>'''
body = f'''  <div style="display:flex; align-items:center; gap:20px; margin-top:-6px">
    <p style="font-size:23px; color:{INK2}">실제 학습 클립 1개로 본 전처리 — “이번에는 만나면 진짜 제대로 얘기 한번 해볼라고.” (분노 · 5/5)</p>
    {playbtns}
  </div>
  <div style="display:flex; flex-direction:column; gap:12px">
    {step(1, "원본", "AI-Hub 녹음 그대로<br>48kHz mono 16bit", v1, "48kHz<br>5.12초")}
    {step(2, "16kHz 리샘플", "WavLM 입력 규격<br>파일 크기 1/3", v2, "16kHz<br>0~8kHz")}
    {step(3, "앞뒤 무음 제거", "30dB 이하 조용한 구간<br>감정 없는 소리 제거", v3, "5.12초<br>→ 2.98초", RED)}
    {step(4, "DC 제거 · 피크 정규화", "녹음 크기 차이를<br>감정으로 착각하지 않게", v4, "peak 0.94<br>→ 0.89")}
  </div>
  {audio_tag('aud-raw', 'raw')}{audio_tag('aud-angry2', 'angry')}'''
slides["prepviz"] = sec("prepviz", "02", "전처리 — 48kHz 원본이 16kHz 학습 입력이 되기까지", body,
"""■ 한 줄로: 실제 클립 하나가 전처리 4단계를 거치며 어떻게 바뀌는지 그대로 보여주는 장. 오른쪽 위 버튼으로 전·후를 들려줄 수 있어.
■ STEP 1 원본: 위아래가 주파수(0~24kHz), 좌우가 시간(5.12초). 밝을수록 소리가 큰 곳.
■ STEP 2 16kHz: 모델(WavLM)이 16kHz로 배운 모델이라 맞춰줘. 그러면 8kHz 위는 사라지는데, 이 클립에서 그 대역 에너지는 0.07%뿐이라 감정 정보 손실이 거의 없어. 용량은 3분의 1.
■ STEP 3 무음 제거: 앞뒤 조용한 구간(빨간 점선 밖)을 잘라서 5.12초 → 2.98초. 감정이 없는 구간을 모델이 배우지 않게.
■ STEP 4 정규화: 가장 큰 소리를 -1dBFS로 맞춰. 마이크마다 녹음 크기가 다른데, 그걸 "크게 말함 = 화남"으로 오해하지 않게.
■ 이렇게 말하면 돼: "버튼 눌러서 들어보시면, 앞뒤 공백만 빠지고 목소리는 그대로입니다." """, nozone=True)

# ───────────────────────── 6. 전처리 깔때기 + 길이 분포 ─────────────────────────
FUN = [("원본", 43991, "CSV 3종 전체", "#6C5F70"), ("라벨 필터", 39188, "동점·전원 불일치 4,803개 제외", "#8C7A4A"),
       ("오디오 처리", 39180, "0.8초 미만 등 8개 제외", "#B8913E"), ("train", 31162, "79명", GOLD), ("val", 3178, "16명", "#6FD08C"), ("test", 4840, "16명", "#5B84D6")]
fmx = 43991
fun = ''
for i, (n, v, s, c) in enumerate(FUN):
    fun += f'''<div style="display:flex; align-items:center; gap:14px">
        <p style="width:140px; flex:none; text-align:right; font-size:22px; font-weight:700; color:{INK}; white-space:nowrap">{n}</p>
        <div class="hbar" style="height:46px; width:{v/fmx*420:.0f}px; flex:none; background:{c}; border-radius:0 8px 8px 0"></div>
        <div style="white-space:nowrap"><p data-count style="{OS}; font-size:26px; font-weight:600; color:{INK}">{v:,}</p><p style="font-size:17px; color:{SUB}">{s}</p></div></div>'''
HIST = [69, 750, 2104, 3270, 3715, 4014, 3499, 3478, 2977, 2523, 2334, 2050, 1554, 1318, 1000, 900, 680, 528, 451, 349, 275, 238, 1104]
hm = max(HIST); hw = 700; hh = 300; hb = hw / len(HIST)
hist = f'<svg width="{hw}" height="{hh+40}" style="display:block; overflow:visible">' + ''.join(
    f'<rect class="vbar" x="{i*hb+1:.1f}" y="{hh - v/hm*hh:.1f}" width="{hb-3:.1f}" height="{v/hm*hh:.1f}" rx="3" fill="{GOLD if 0.5+i*0.5 < 8 else RED}"/>' for i, v in enumerate(HIST))
x8 = (8 - 0.5) / 0.5 * hb
hist += f'<line x1="{x8:.1f}" y1="-30" x2="{x8:.1f}" y2="{hh}" stroke="{INK2}" stroke-dasharray="6 5"/><text x="{x8-10:.1f}" y="-16" fill="{INK2}" font-size="19" font-family="Noto Sans KR, Arial, sans-serif" text-anchor="end">8초 초과 11.4% → 학습 때 잘라 사용</text>'
for s in (1, 2, 4, 6, 8, 10, 12):
    hist += f'<text x="{(s-0.5)/0.5*hb:.1f}" y="{hh+28}" fill="{SUB}" font-size="18" font-family="Oswald, Arial, sans-serif" text-anchor="middle">{s}s{"+" if s==12 else ""}</text>'
hist += '</svg>'
body = f'''  <div style="display:flex; gap:36px; align-items:stretch">
    <div style="flex:1.05; display:flex; flex-direction:column; gap:18px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:28px 30px">
      <p style="font-size:26px; font-weight:700">몇 개가 어디서 빠졌나 — AI-Hub</p>
      <div style="display:flex; flex-direction:column; gap:14px">{fun}</div>
      <p style="font-size:20px; color:{SUB}; margin-top:auto">버린 4,811개는 모두 이유를 셀 수 있다 · 같은 목소리는 train/val/test 중 한 곳에만</p>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; gap:14px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:28px 30px">
      <div style="display:flex; align-items:baseline; gap:16px"><p style="font-size:26px; font-weight:700">전처리 후 길이 분포</p><p style="{OS}; font-size:24px; color:{SUB}; margin-left:auto">평균 4.9초 · 중앙값 4.3초</p></div>
      <div style="flex:1; display:flex; align-items:flex-end; padding-top:30px">{hist}</div>
      <p style="font-size:20px; color:{SUB}">0.5초 간격 · 39,180클립 · 12초 이상은 마지막 칸에 모음</p>
    </div>
  </div>
  <div style="display:flex; gap:14px">
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px"><p style="font-size:22px; color:{INK2}"><b style="color:{INK}">길이 상한 8초</b> — 88.6%가 들어오는 지점. 긴 클립은 잘라 쓴다</p></div>
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px"><p style="font-size:22px; color:{INK2}"><b style="color:{INK}">캐시 1회 생성</b> — 모든 실험이 공유 · 원본은 읽기 전용</p></div>
  </div>'''
slides["prepfunnel"] = sec("prepfunnel", "02", "전처리 결과 — 43,991개 중 4,811개를 왜 버렸나", body,
"""■ 한 줄로: 전처리를 거치며 데이터가 몇 개 남았는지(왼쪽), 남은 소리 길이가 어떤지(오른쪽).
■ 왼쪽: 4만 4천 개에서 5명 의견이 동점이거나 거의 안 맞은 4,803개를 빼고, 너무 짧거나 읽을 수 없는 8개를 더 뺐어. 남은 39,180개를 사람 단위로 학습 31,162 / 검증 3,178 / 시험 4,840으로 나눴어.
■ 오른쪽: 무음 제거 후 길이. 대부분 2~6초. 8초 선(점선)을 넘는 11.4%는 버리지 않고 학습할 때 8초만 잘라서 써. 그래서 8초를 상한으로 정했어 — 이 그래프가 근거야.
■ 이렇게 말하면 돼: "길이 상한 8초는 감으로 정한 게 아니라 분포를 보고 88.6%가 들어오는 지점으로 정했습니다." """)

# ───────────────────────── 7. 불균형 → 해소 ─────────────────────────
AIH = {'sadness': 12833, 'angry': 5690, 'neutral': 4769, 'happy': 3087, 'fear': 2108, 'disgust': 1897, 'surprise': 778}
SKT = {'sadness': 7143, 'angry': 7456, 'neutral': 9133, 'happy': 6600, 'fear': 6649, 'disgust': 319, 'surprise': 2700}  # merge 균형 추출 계산값 (≈)
order = ['sadness', 'angry', 'neutral', 'happy', 'fear', 'disgust', 'surprise']
tot = {k: AIH[k] + SKT[k] for k in order}; tm = max(tot.values())
def colbars(data, extra=None, h=300, w=60):
    out = ''
    for k in order:
        a = data[k]; b = extra[k] if extra else 0
        out += f'''<div style="display:flex; flex-direction:column; align-items:center; gap:6px; justify-content:flex-end; height:{h+70}px">
          <p style="{OS}; font-size:18px; color:{INK2}">{(a+b):,}</p>
          <div style="display:flex; flex-direction:column; width:{w}px">
            {f'<div class="sktbar" style="height:{b/tm*h:.0f}px; background:repeating-linear-gradient(135deg,{EMO[k][1]} 0 6px,#120E14 6px 10px); border-radius:6px 6px 0 0; opacity:.9"></div>' if b else ''}
            <div class="vbar{' basebar' if b else ''}" style="height:{a/tm*h:.0f}px; background:{EMO[k][1]}; border-radius:{'0' if b else '6px 6px'} 0 0"></div>
          </div>
          <p style="font-size:20px; font-weight:700; color:{EMO[k][1]}">{EMO[k][0]}</p></div>'''
    return out
eq = ''.join(f'''<div style="display:flex; flex-direction:column; align-items:center; gap:6px; justify-content:flex-end; height:370px">
          <p class="eqlab" style="{OS}; font-size:18px; color:{INK2}">14%</p>
          <div class="eqbar" data-from="{AIH[k]/tm*300:.0f}" style="width:40px; height:{300/7*1.9:.0f}px; background:{EMO[k][1]}; border-radius:6px 6px 0 0"></div>
          <p style="font-size:17px; font-weight:700; color:{EMO[k][1]}; white-space:nowrap">{EMO[k][0]}</p></div>''' for k in order)
def fix(t, d):
    return f'<div style="background:{CARD2}; border-radius:12px; padding:14px 18px"><p style="font-size:22px; font-weight:700; color:{GOLD}">{t}</p><p style="font-size:19px; color:{INK2}; line-height:1.4; margin-top:4px; word-break:keep-all">{d}</p></div>'
body = f'''  <div style="display:flex; gap:22px; align-items:stretch">
    <div style="flex:1.2; display:flex; flex-direction:column; gap:10px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:24px 26px">
      <div style="display:flex; align-items:baseline"><p style="font-size:25px; font-weight:700">① 문제 — AI-Hub train</p><p data-count style="{OS}; font-size:38px; color:{RED}; margin-left:auto">16.5 : 1</p></div>
      <div style="display:flex; gap:10px; justify-content:space-between">{colbars(AIH)}</div>
      <p style="font-size:19px; color:{SUB}">슬픔 12,833 vs 놀람 778 · 31,162클립</p>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; gap:10px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:24px 26px">
      <p style="font-size:25px; font-weight:700">② 학습 때 — 균형 샘플러</p>
      <div style="display:flex; gap:6px; justify-content:space-between">{eq}</div>
      <p style="font-size:19px; color:{SUB}; word-break:keep-all">적은 감정을 더 자주 뽑아 모델은 7감정을 같은 비율로 본다</p>
    </div>
    <div style="flex:1.2; display:flex; flex-direction:column; gap:10px; background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:24px 26px">
      <div style="display:flex; align-items:baseline"><p style="font-size:25px; font-weight:700">③ 데이터로 — SKT 4만 추가</p><p class="ratio9" style="{OS}; font-size:38px; color:#6FD08C; margin-left:auto">9 : 1</p></div>
      <div style="display:flex; gap:10px; justify-content:space-between">{colbars(AIH, SKT)}</div>
      <p style="font-size:19px; color:{SUB}">빗금 = SKT 추가분 · 놀람 778 → 3,478 · 공포 2,108 → 8,757</p>
    </div>
  </div>
  <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:14px">
    {fix("지표: UAR", "감정별 재현율의 평균. 슬픔만 찍으면 점수가 안 나온다")}
    {fix("손실: CB-Focal", "적은 감정·헷갈리는 샘플의 오답에 더 큰 벌점")}
    {fix("정답: soft 라벨", "5명 투표 비율을 같이 학습 — 애매함을 인정")}
    {fix("다음: 혐오 보강", "SKT에도 혐오가 적다 (319) → 자체 녹음·방언 데이터")}
  </div>'''
slides["imbal"] = sec("imbal", "02", "불균형 16.5:1 을 9:1 로", body,
"""■ 한 줄로: 감정별 데이터 양이 16배 넘게 차이 나는 문제를 세 겹으로 풀고 있다.
■ ① 문제: 학습 데이터에서 슬픔 12,833개, 놀람 778개. 16.5배 차이.
■ ② 학습할 때: 적은 감정을 더 자주 뽑아서 모델 입장에선 7감정을 똑같이 1/7씩 보게 해 (균형 샘플러).
■ ③ 데이터로: SKT에서 4만 개를 감정·화자별로 골고루 뽑아 추가. 놀람 778 → 3,478, 공포 2,108 → 8,757. 불균형이 약 9:1로 줄어. (빗금 부분이 SKT. 서버 manifest 실측값과 일치)
■ 아래 네 칸: 채점을 UAR로, 틀리면 벌점을 차등으로, 5명 의견 비율도 같이 학습. 혐오는 SKT에도 적어서(319개) 다음 과제로 남아 있어.
■ 이렇게 말하면 돼: "불균형은 지표, 샘플링, 데이터 추가 세 단계로 풀고 있고, 혐오는 아직 남은 과제입니다." """)

# ───────────────────────── 8. 무엇을 학습시켰나 ─────────────────────────
def box(tag, title, lines, vis='', col=GOLD):
    return f'''<div class="tbox" style="flex:1; display:flex; flex-direction:column; gap:10px; background:{CARD}; border:1px solid {LINE}; border-top:4px solid {col}; border-radius:14px; padding:20px 22px">
      <p style="{OS}; font-size:20px; color:{col}; letter-spacing:.05em">{tag}</p>
      <p style="font-size:29px; font-weight:800; line-height:1.2; white-space:nowrap">{title}</p>
      {vis}
      <div style="display:flex; flex-direction:column; gap:6px">{''.join(f'<p style="font-size:22px; line-height:1.45; color:{INK2}; word-break:keep-all">{l}</p>' for l in lines)}</div>
    </div>'''
vote = ''.join(f'<div style="display:flex; flex-direction:column; align-items:center; gap:4px"><div class="vdot" style="width:30px; height:30px; border-radius:50%; background:{EMO[v][1]}"></div><p style="font-size:14px; color:{SUB}">{i+1}</p></div>' for i, v in enumerate(['neutral', 'angry', 'neutral', 'neutral', 'angry']))
vis_in = f'<div style="background:#0C090D; border-radius:8px; padding:8px 0">{wave_svg(AUD["angry"]["peaks"], 250, 60, GOLD)}</div>'
vis_lab = f'''<div style="display:flex; gap:8px">{vote}</div>
      <div style="display:flex; height:22px; border-radius:6px; overflow:hidden"><div class="sseg" style="width:60%; background:#A7A1AB"></div><div class="sseg" style="width:40%; background:{RED}"></div></div>
      <p style="font-size:17px; color:{SUB}">중립 0.6 · 분노 0.4</p>'''
arrow2 = f'<p class="tarr" style="align-self:center; font-size:34px; color:#6C5F70">→</p>'
body = f'''  <div style="display:flex; gap:12px; align-items:stretch">
    {box("INPUT", "소리 파형만", ["16kHz · 최대 8초", "텍스트·연기 지시 제외"], vis_in)}
    {arrow2}
    {box("LABEL", "5명이 느낀 감정", ["다수결 = 정답 (중립)", "투표 비율 = soft 라벨"], vis_lab, "#A7A1AB")}
    {arrow2}
    {box("MODEL", "WavLM + 헤드", ["사전학습 12층 가중합", "감정 실린 구간에 가중", "→ 7감정 확률"], '', RED)}
    {arrow2}
    {box("TRAIN", "통째로 파인튜닝", ["train 31,162 · 79명", "batch 32 · 10 epoch", "CB-Focal + soft KL", "RTX 4090 · bf16"], '', "#5B84D6")}
    {arrow2}
    {box("TEST", "처음 듣는 목소리로", ["test 4,840 · 16명", "학습에 없던 화자만", "지표 UAR", "(감정별 재현율 평균)"], '', "#6FD08C")}
  </div>
  <p style="font-size:24px; font-weight:700; color:{INK2}; margin-top:18px">결과 — 같은 모델 구조, 데이터만 바꿔가며</p>
  <div style="display:flex; gap:16px">
    <div style="flex:1; background:{CARD2}; border-radius:14px; padding:28px 26px; display:flex; align-items:center; gap:22px"><p data-count style="{OS}; font-size:54px; font-weight:600; color:{GOLD}">0.734</p><p style="font-size:21px; color:{INK2}; line-height:1.4">고신뢰 2.5만 학습<br><span style="color:{SUB}">시험지가 달라 직접 비교 X</span></p></div>
    <div style="flex:1; background:{CARD2}; border-radius:14px; padding:28px 26px; display:flex; align-items:center; gap:22px"><p data-count style="{OS}; font-size:54px; font-weight:600; color:{INK}">0.675</p><p style="font-size:21px; color:{INK2}; line-height:1.4">전체 3.9만 학습 · 전체 test<br><span style="color:{SUB}">놀람 F1 0.44 → 0.63</span></p></div>
    <div style="flex:1; background:#2A2112; border:2px solid {GOLD}; border-radius:14px; padding:28px 26px; display:flex; align-items:center; gap:22px"><p data-count style="{OS}; font-size:54px; font-weight:600; color:{GOLD}">0.695</p><p style="font-size:21px; color:{INK2}; line-height:1.4">+ SKT 4만 혼합 + 로짓 보정<br><span style="color:{SUB}">보정 전 0.663 · WAR 0.721</span></p></div>
  </div>'''
slides["trained"] = sec("trained", "03", "무엇을 학습시켰나 — WavLM 9,497만 파라미터", body,
"""■ 한 줄로: 소리 파형을 넣고, 5명이 느낀 감정을 정답으로, WavLM을 통째로 다시 훈련시켰다.
■ INPUT: 모델이 받는 건 소리 파형 하나뿐. 문장 글자나 연기 지시는 절대 안 넣어.
■ LABEL: 예시처럼 5명 중 3명이 중립, 2명이 분노라고 들었으면 정답은 중립, 그리고 "중립 60% · 분노 40%"라는 비율도 같이 가르쳐.
■ MODEL: WavLM(12층)의 층마다 나온 정보를 섞어 쓰고, 문장에서 감정이 실린 구간에 더 무게를 둬서 요약한 뒤 7감정 확률로 바꿔.
■ TRAIN / TEST: 학습은 79명 목소리로, 시험은 한 번도 못 들어본 16명 목소리로.
■ 아래 점수: 0.734는 시험지가 달라서 직접 비교하면 안 돼. 0.675와 0.695는 같은 시험지(test 4,840개).
■ 오른쪽 금색 칸(9/22 결과): SKT 4만 개를 섞었더니 UAR은 0.663으로 오히려 조금 내려갔어. 대신 정밀도가 크게 올랐어 — 모델이 "확실할 때만" 희소 감정을 고르고, 애매하면 슬픔으로 몰았거든. 그래서 슬픔 쏠림을 펴는 로짓 보정(확률을 학습 데이터 비율로 나누기, 강도는 검증셋으로만 결정)을 붙였더니 0.695. 재학습 없이 후처리 한 줄로 +0.03.
■ 같은 보정을 기존 모델에 해도 0.697로 비슷하지만, 그쪽은 전체 정확도(WAR)가 0.667로 크게 떨어져. SKT 섞은 모델은 0.721을 유지해. 그래서 서비스엔 SKT 혼합 + 보정을 쓴다.
■ 이렇게 말하면 돼: "입력은 소리만, 정답은 사람이 느낀 감정, 시험은 처음 듣는 목소리 — 이 세 가지 원칙으로 학습했습니다." """)

# ───────────────────────── 9. 간트 차트 ─────────────────────────
import datetime as dt
D0 = dt.date(2026, 9, 14); DN = 21  # 9/14 ~ 10/4
TODAY = (dt.date(2026, 9, 22) - D0).days
G = [("데이터", "수집 · EDA · 라벨 재정의", 0, 2, "done"),
     ("데이터", "전처리 · 화자 독립 분할", 1, 2, "done"),
     ("모델", "기준 모델 · 백본 비교", 1, 4, "done"),
     ("검증", "외부 검증 · 경량화 실측", 2, 3, "done"),
     ("데이터", "SKT 확보 · 서버 구축", 3, 5, "done"),
     ("발표", "기획발표 준비 · 발표", 6, 3, "done"),
     ("모델", "SKT 혼합 학습 · 비율 곡선", 8, 4, "now"),
     ("검증", "방언 편향 평가 · 보정", 10, 5, "plan"),
     ("검증", "전화망 음질 시험", 10, 2, "plan"),
     ("데이터", "자체 녹음 (실제 대화체)", 12, 5, "plan"),
     ("서비스", "데모 (FastAPI · Supabase)", 11, 8, "plan"),
     ("발표", "최종 발표 자료 · 리허설", 17, 4, "plan")]
GC = {"데이터": GOLD, "모델": RED, "검증": "#6FD08C", "발표": "#E58BC0", "서비스": "#5B84D6"}
LW = 470; CW = (1664 - LW) / DN; RH = 50
head = ''.join(f'<div style="position:absolute; left:{LW + i*CW:.1f}px; width:{CW:.1f}px; top:0; text-align:center"><p style="{OS}; font-size:17px; color:{GOLD if i==TODAY else (SUB if (D0+dt.timedelta(i)).weekday()<5 else DIM)}">{(D0+dt.timedelta(i)).day}</p></div>' for i in range(DN))
wk = ''.join(f'<div style="position:absolute; left:{LW + i*CW:.1f}px; top:28px; bottom:0; width:{CW*2:.1f}px; background:rgba(255,255,255,.025)"></div>' for i in range(DN) if (D0+dt.timedelta(i)).weekday() == 5)
grow = ''
for r, (cat, name, s, n, st) in enumerate(G):
    y = 40 + r * RH; c = GC[cat]
    style = {"done": f"background:{c}", "now": f"background:repeating-linear-gradient(135deg,{c} 0 10px,{c}99 10px 20px); box-shadow:0 0 0 2px {c}", "plan": f"background:transparent; border:2px dashed {c}"}[st]
    grow += (f'<p style="position:absolute; left:0; top:{y+8}px; width:{LW-20}px; font-size:21px; color:{INK if st!="plan" else INK2}; white-space:nowrap"><span style="display:inline-block; width:84px; font-size:17px; font-weight:700; color:{c}">{cat}</span>{name}</p>'
             f'<div class="gbar g{st}" style="position:absolute; left:{LW + s*CW + 2:.1f}px; top:{y+6}px; width:{n*CW - 4:.1f}px; height:{RH-16}px; border-radius:8px; {style}"></div>')
H_ = 40 + len(G) * RH + 10
months = f'<p style="position:absolute; left:{LW}px; top:-30px; font-size:18px; color:{SUB}">9월</p><p style="position:absolute; left:{LW + 17*CW:.1f}px; top:-30px; font-size:18px; color:{SUB}">10월</p>'
gantt = f'''<div style="position:relative; height:{H_}px; margin-top:30px">
    {wk}{months}{head}{grow}
    <div class="gtoday" style="position:absolute; left:{LW + TODAY*CW + CW/2:.1f}px; top:28px; bottom:-8px; border-left:3px solid {GOLD}"></div>
    <p style="position:absolute; left:{LW + TODAY*CW + CW/2 + 8:.1f}px; top:{H_-4}px; font-size:18px; font-weight:700; color:{GOLD}">오늘 9/22 · 기획발표</p>
  </div>'''
leg = ''.join(f'<div style="display:flex; align-items:center; gap:8px"><div style="width:30px; height:16px; border-radius:4px; {s}"></div><p style="font-size:19px; color:{INK2}">{t}</p></div>' for t, s in [("완료", f"background:{SUB}"), ("진행 중", f"background:repeating-linear-gradient(135deg,{SUB} 0 6px,{SUB}66 6px 12px)"), ("계획", f"border:2px dashed {SUB}")])
body = f'''{gantt}
  <div style="display:flex; gap:26px; align-items:center; margin-top:18px">{leg}<p style="font-size:19px; color:{SUB}; margin-left:auto">주말은 옅은 띠 · 서버 학습 시간에 따라 1~2일 이동 가능 · 최종 발표일 확정 후 조정</p></div>'''
slides["gantt"] = sec("gantt", "", "일정 — 간트 차트", body,
"""■ 한 줄로: 3주 일정. 왼쪽 절반(완료)은 데이터·모델 기초, 오른쪽 절반(계획)은 검증과 서비스.
■ 금색 세로선이 오늘(9/22). 그 왼쪽은 다 끝났고, SKT 혼합 학습이 지금 서버에서 돌고 있어(빗금).
■ 다음 순서: SKT 섞은 효과 채점 → 방언 편향 평가와 보정 → 전화망 음질 시험 → 자체 녹음 → FastAPI·Supabase·Docker로 데모 → 최종 발표 준비.
■ 데모가 가장 길게(8일) 잡혀 있는 이유: 백엔드·DB·화면을 다 만들어야 해서.
■ 이렇게 말하면 돼: "기초 작업은 끝났고, 이제 검증과 서비스 구현 단계로 넘어갑니다." """)

for k, v in slides.items():
    open(os.path.join(SRC, k + ".html"), "w", encoding="utf-8").write(v)
    print(k, len(v))
