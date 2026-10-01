# -*- coding: utf-8 -*-
"""최종 발표본 — '정확도를 올리려고 한 것' 3장 (표 · 점수 곡선 · 실패에서 배운 것 — 좋아 보이는 숫자를 버린 3번)"""
import os
SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a047086af0ac/project"  # placeholder, replaced below
SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"

INK = "#F5F0EA"; INK2 = "#D2C8CD"; SUB = "#ADA1A7"; DIM = "#7A6E74"
RED = "#E8433F"; GOLD = "#F2B63D"; GREEN = "#6FD08C"; BLUE = "#5B84D6"
CARD = "#1C1620"; CARD2 = "#241C29"; LINE = "#362C38"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"


def sec(sid, badge, title, body, notes, bg="#120E14"):
    b = (f'<p style="{OS}; font-size:34px; font-weight:600; color:{INK}; background:{RED}; border-radius:12px; padding:10px 24px">{badge}</p>' if badge else '')
    return f'''<section id="{sid}" data-transition="push" style="background:{bg}; color:{INK}; font-family:'Noto Sans KR', Arial, sans-serif; padding:100px 128px 116px; display:flex; flex-direction:column; gap:24px">
  <div style="display:flex; align-items:center; gap:28px">
    {b}
    <h2 style="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif; font-size:64px; font-weight:400; line-height:1.15; color:{INK}">{title}</h2>
  </div>
{body}
  <aside>{notes}</aside>
</section>
'''

# ─────────────────── 1. 시도 · 가설 · 결과 표 ───────────────────
ROWS = [
    ("라벨을 다시 정의", "'상황' 컬럼은 연기 지시일 뿐", "지시와 사람이 느낀 감정 <b style='color:#F5F0EA'>68.1%</b>만 일치", "5명 다수결 + 투표 비율", GOLD, "채택"),
    ("화자 단위로 분할", "랜덤이면 목소리를 외운다", "val 0.741 → test <b style='color:#F5F0EA'>0.734</b> 유지", "점수 부풀림 차단", GOLD, "채택"),
    ("UAR · CB-Focal · 균형 샘플러", "불균형 13.6:1 을 그냥 두면 다수 감정만 맞힌다", "놀람 F1 0.44 → <b style='color:#F5F0EA'>0.63</b>", "소수 감정을 포기하지 않음", GOLD, "채택"),
    ("백본 3종 비교", "제일 센 모델이 제일 좋을까", "0.287 → 0.573 → <b style='color:#F5F0EA'>0.734</b>", "선형 프로브로 원인 분리", GOLD, "채택"),
    ("두 모델 앙상블", "섞으면 더 오르지 않을까", "내부 +0.011, <b style='color:#F5F0EA'>외부 검증 0</b>", "근거 없는 복잡도는 버린다", DIM, "기각"),
    ("SKT 15만 확보 → 4만 혼합", "희소 감정을 데이터로 보강", "UAR 0.675 → <b style='color:#F5F0EA'>0.663</b> · WAR +0.016", "데이터 추가 ≠ 성능 향상", BLUE, "부분"),
    ("로짓 보정 (τ=0.6)", "슬픔 쏠림을 펴면 회복될까", "0.663 → <b style='color:#F5F0EA'>0.695</b> · 재학습 0분", "τ 는 검증셋으로만 결정", GREEN, "채택"),
    ("중립을 뺀 6감정 + 보류", "잔여 범주를 없애면 깔끔할까", "오탐 증가 (F1 0.79 → <b style='color:#F5F0EA'>0.78</b>)", "표기만 '감정 신호 없음'으로", DIM, "기각"),
    ("SKT 중립 제외 재학습", "나레이션 중립이 개념을 오염시킨다", "0.643 하락 · 중립 정밀도 <b style='color:#F5F0EA'>0.46</b>", "샘플러와 상호작용 발견", DIM, "기각"),
]
hdr = ''.join(f'<p style="flex:{w}; font-size:20px; font-weight:700; color:{SUB}">{t}</p>'
              for t, w in (("무엇을 했나", 1.35), ("왜 (가설)", 1.5), ("결과 (숫자)", 1.35), ("남긴 것", 1.25), ("", .42)))
rows = ''
for i, (a, b, c, d, col, tag) in enumerate(ROWS):
    bg = CARD if i % 2 == 0 else "#181219"
    rows += f'''<div class="erow" style="display:flex; gap:14px; align-items:center; background:{bg}; border-left:5px solid {col}; border-radius:10px; padding:13px 18px">
      <p style="flex:1.35; font-size:22px; font-weight:700; color:{INK}; word-break:keep-all">{a}</p>
      <p style="flex:1.5; font-size:20px; line-height:1.35; color:{SUB}; word-break:keep-all">{b}</p>
      <p style="flex:1.35; font-size:20px; line-height:1.35; color:{INK2}; word-break:keep-all">{c}</p>
      <p style="flex:1.25; font-size:20px; line-height:1.35; color:{INK2}; word-break:keep-all">{d}</p>
      <p style="flex:.42; text-align:right"><span style="font-size:17px; font-weight:700; color:{'#120E14' if col in (GOLD, GREEN) else INK}; background:{col}; border-radius:999px; padding:4px 12px; white-space:nowrap">{tag}</span></p>
    </div>'''
body = f'''  <p style="font-size:24px; color:{INK2}; margin-top:-6px">8가지를 시도해 <b style="color:{INK}">5개 채택 · 3개 기각</b> — 버린 3개도 그대로 남긴다</p>
  <div style="display:flex; gap:14px; padding:0 18px">{hdr}</div>
  <div style="display:flex; flex-direction:column; gap:7px">{rows}</div>'''
open(os.path.join(SRC, "effort1.html"), "w", encoding="utf-8").write(sec(
    "effort1", "03", "정확도를 올린 방법 — 라벨 재정의 · 화자 분할 · 불균형 보정", body,
    """■ 한 줄로: 아홉 번의 시도. 여섯은 채택, 셋은 기각. 기각한 것도 숨기지 않고 적었어.
■ 읽는 법: 왼쪽부터 '무엇을 했나 → 왜 그렇게 생각했나 → 숫자로 어떻게 나왔나 → 무엇을 얻었나'. 오른쪽 배지가 채택/기각.
■ 강조할 세 줄:
- 라벨 재정의: 데이터에 붙어 있던 정답을 그대로 안 믿고 다시 만든 것. 여기서 모든 게 시작됐어.
- 로짓 보정: 재학습 0분으로 UAR을 0.663에서 0.695로. 제일 가성비 좋은 수.
- 기각 3건: 앙상블(외부 검증에서 이득 0), 중립 제거(오탐 증가), SKT 중립 제외(샘플러와 충돌). 해보고 아니어서 버린 것들이야.
■ 이렇게 말하면 돼: "좋아 보이는 아이디어를 전부 숫자로 확인했고, 아닌 건 버렸습니다." """))

# ─────────────────── 2. 점수 곡선 ───────────────────
PTS = [
    ("emotion2vec+\n프리즈", 0.287, "고신뢰", DIM, "센 모델이라고 좋은 특징은 아니었다"),
    ("emotion2vec base\n프리즈", 0.573, "고신뢰", DIM, "SSL 원본으로 바꾸자 2배"),
    ("WavLM 파인튜닝\n고신뢰 2.5만", 0.734, "고신뢰", GOLD, "기준 모델"),
    ("WavLM 파인튜닝\n전체 3.9만", 0.675, "전체", BLUE, "시험지가 더 어려움"),
    ("+ SKT 4만 혼합", 0.663, "전체", BLUE, "데이터를 늘렸는데 내려감"),
    ("+ 로짓 보정", 0.695, "전체", GREEN, "재학습 없이 +0.032"),
]
W, H = 1520, 400
x0, y0 = 90, 30
lo, hi = 0.25, 0.78
def X(i): return x0 + i * ((W - x0 - 60) / (len(PTS) - 1))
def Y(v): return y0 + (hi - v) / (hi - lo) * H
grid = ''.join(f'<line x1="{x0-40}" y1="{Y(v):.0f}" x2="{W-20}" y2="{Y(v):.0f}" stroke="#2A2230" stroke-width="1"/>'
               f'<text x="{x0-52}" y="{Y(v)+7:.0f}" text-anchor="end" font-size="19" fill="{DIM}" font-family="Oswald, Arial, sans-serif">{v:.1f}</text>'
               for v in (0.3, 0.4, 0.5, 0.6, 0.7))
seg = ''
for i in range(len(PTS) - 1):
    dash = ' stroke-dasharray="7 6"' if PTS[i][2] != PTS[i + 1][2] else ''
    seg += (f'<path class="ecurve" d="M{X(i):.0f} {Y(PTS[i][1]):.0f} L{X(i+1):.0f} {Y(PTS[i+1][1]):.0f}" fill="none" '
            f'stroke="{PTS[i+1][3]}" stroke-width="4" stroke-linecap="round"{dash}/>')
dots = ''
for i, (name, v, ts, col, note) in enumerate(PTS):
    up = i in (0, 1, 2, 5)
    dots += (f'<circle class="edot" cx="{X(i):.0f}" cy="{Y(v):.0f}" r="{13 if col in (GOLD, GREEN) else 9}" fill="{col}" stroke="#120E14" stroke-width="3"/>'
             f'<text x="{X(i):.0f}" y="{Y(v) - 26 if up else Y(v) + 38:.0f}" text-anchor="middle" font-size="30" font-weight="600" fill="{col}" font-family="Oswald, Arial, sans-serif">{v:.3f}</text>')
labels = ''.join(
    f'<div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:4px">'
    f'<p style="font-size:19px; font-weight:700; color:{p[3] if p[3] != DIM else INK2}; text-align:center; line-height:1.25; white-space:pre-line">{p[0]}</p>'
    f'<p style="font-size:16px; color:{DIM}; text-align:center; line-height:1.3; word-break:keep-all">{p[4]}</p></div>' for p in PTS)
body = f'''  <p style="font-size:24px; color:{INK2}; margin-top:-6px">화자 독립 test UAR · <b style="color:{GOLD}">금색·초록</b>은 채택한 모델 · 점선은 <b style="color:{INK}">시험지가 바뀐 구간</b> (직접 비교 불가)</p>
  <div style="background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:26px 30px 18px">
    <svg width="{W}" height="{H + 90}" style="display:block; overflow:visible">{grid}{seg}{dots}</svg>
    <div style="display:flex; gap:10px; margin-top:12px; padding:0 30px">{labels}</div>
  </div>
  <div style="display:flex; gap:14px">
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px"><p style="font-size:21px; color:{INK2}"><b style="color:{INK}">0.287 → 0.734</b> · 백본을 바꾸고 라벨을 다시 만들자 2.5배 (고신뢰 test)</p></div>
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 22px"><p style="font-size:21px; color:{INK2}"><b style="color:{INK}">0.675 → 0.695</b> · 전체 test 에서 SKT 혼합 + 보정으로 회복·상승</p></div>
    <div style="flex:1; background:#2A1A1C; border-left:5px solid {RED}; border-radius:12px; padding:16px 22px"><p style="font-size:21px; color:{INK2}">시험지가 다르면 <b style="color:{INK}">같은 선에 놓지 않는다</b></p></div>
  </div>'''
open(os.path.join(SRC, "effort2.html"), "w", encoding="utf-8").write(sec(
    "effort2", "03", "점수 이동 — 0.287에서 0.695까지", body,
    """■ 한 줄로: 여섯 번의 실험으로 점수가 어떻게 움직였는지 한 줄 그래프.
■ 읽는 법: 왼쪽 두 점은 특징만 뽑아 쓴 방식(0.287 → 0.573). 세 번째가 통째로 파인튜닝한 기준 모델 0.734.
■ 중요한 주의: 세 번째와 네 번째 사이는 점선이야. 시험지(test 셋)가 바뀌었거든. 고신뢰 test(3,329개)에서 전체 test(4,840개)로 옮기면서 문제가 어려워진 거지, 모델이 나빠진 게 아니야. 이 각주를 꼭 말해야 해.
■ 마지막 두 점: SKT를 섞었더니 0.663으로 오히려 내려갔고, 로짓 보정으로 0.695까지 올렸어. 같은 시험지 안에서의 비교라 이건 정직한 상승이야.
■ 이렇게 말하면 돼: "점수를 올린 것도 중요하지만, 비교 가능한 조건을 지키는 게 더 중요했습니다." """))

# ─────────────────── 3. 실패에서 배운 것 — 좋아 보이는 숫자를 버린 3번 ───────────────────
def fail(tag, title, what, how, lesson, col):
    return f'''<div class="fcard" style="flex:1; display:flex; flex-direction:column; gap:12px; background:{CARD}; border:1px solid {LINE}; border-top:4px solid {col}; border-radius:16px; padding:26px 28px">
      <p style="{OS}; font-size:20px; color:{col}; letter-spacing:.04em">{tag}</p>
      <p style="font-size:29px; font-weight:800; line-height:1.2; color:{INK}; word-break:keep-all">{title}</p>
      <div style="display:flex; flex-direction:column; gap:9px; border-top:1px solid {LINE}; padding-top:14px">
        <p style="font-size:20px; line-height:1.45; color:{INK2}; word-break:keep-all"><b style="color:{RED}">증상</b> {what}</p>
        <p style="font-size:20px; line-height:1.45; color:{INK2}; word-break:keep-all"><b style="color:{GOLD}">추적</b> {how}</p>
      </div>
      <p style="font-size:21px; font-weight:600; line-height:1.4; color:{col}; margin-top:auto; word-break:keep-all">→ {lesson}</p>
    </div>'''
body = f'''  <p style="font-size:24px; color:{INK2}; margin-top:-6px">숫자가 이상하면 좋아하지 않고 <b style="color:{INK}">추적했다</b> — 세 번 다 원인이 나왔다</p>
  <div style="display:flex; gap:20px; align-items:stretch">
    {fail("CASE 1 · 데이터 누수", "점수가 너무 잘 나왔다", "이어학습 모델이 test 에서 0.7145 — 기준(0.675)보다 높음", "test 화자 16명 중 11명이 학습 화자 · 4,840개 중 <b style='color:#F5F0EA'>1,494개가 학습한 파일</b>", "체크포인트는 split 과 한 쌍이다", RED)}
    {fail("CASE 2 · 숨은 변수", "데이터를 뺐더니 더 나빠졌다", "SKT 중립 제외 후 중립 정밀도 0.57 → <b style='color:#F5F0EA'>0.46</b>, 기쁨의 44%가 중립으로", "중립이 희소해지자 균형 샘플러가 같은 샘플을 3배 더 반복 → 중립 남발", "데이터 비율을 바꾸면 샘플링도 같이 바뀐다", "#B79CEB")}
    {fail("CASE 3 · 좋아 보이는 지표", "내부 점수만 올랐다", "앙상블 내부 +0.011 · 중립 제거 시 UAR +0.049 (둘 다 매력적)", "외부 검증에선 이득 0 · 중립 제거는 에스컬레이션 오탐 증가", "서비스 지표까지 확인하고 결정한다", BLUE)}
  </div>
  <div style="display:flex; gap:14px; margin-top:6px">
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:18px 24px"><p style="font-size:22px; color:{INK2}"><b style="color:{GOLD}">규칙 1</b> · 같은 시험지끼리만 비교한다</p></div>
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:18px 24px"><p style="font-size:22px; color:{INK2}"><b style="color:{GOLD}">규칙 2</b> · 임계값·τ 는 검증셋으로만 정한다</p></div>
    <div style="flex:1; background:{CARD2}; border-radius:12px; padding:18px 24px"><p style="font-size:22px; color:{INK2}"><b style="color:{GOLD}">규칙 3</b> · 점수가 좋아도 서비스 지표를 본다</p></div>
  </div>'''
open(os.path.join(SRC, "effort3.html"), "w", encoding="utf-8").write(sec(
    "effort3", "03", "실패에서 배운 것 — 좋아 보이는 숫자를 버린 3번", body,
    """■ 한 줄로: 세 번의 '어? 이상한데'를 끝까지 추적해서 원인을 찾은 기록.
■ CASE 1: 이어학습한 모델이 기준보다 점수가 높게 나왔어. 보통은 좋아하는데, 우리는 의심했고 파일 단위로 추적했더니 시험 문제 1,494개를 이미 학습한 상태였어. 기준 모델을 바꿔서 다시 쟀지.
■ CASE 2: SKT 중립(나레이션)이 개념을 오염시킨다고 보고 뺐는데 오히려 나빠졌어. 원인은 균형 샘플러 — 중립이 줄자 남은 중립을 3배 더 자주 보여주게 돼서 모델이 중립을 남발했어. 변수 하나만 바꿨다고 생각했는데 두 개가 움직인 거야.
■ CASE 3: 앙상블도 중립 제거도 숫자만 보면 매력적이었어. 그런데 외부 검증과 서비스 지표(오탐)를 보니 아니었고, 그래서 둘 다 버렸어.
■ 아래 규칙 3개: 이 세 사건에서 우리가 만든 실험 규칙이야.
■ 이렇게 말하면 돼: "점수가 예상보다 좋을 때 의심하는 습관이 이번 프로젝트에서 가장 크게 남았습니다." """))
print("effort1/2/3 written")
