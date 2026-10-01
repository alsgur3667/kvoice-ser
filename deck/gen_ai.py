# -*- coding: utf-8 -*-
"""최종 발표본 — 'AI와 일한 방식' 1장"""
import os
SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"
INK="#F5F0EA"; INK2="#D2C8CD"; SUB="#ADA1A7"; DIM="#7A6E74"
RED="#E8433F"; GOLD="#F2B63D"; GREEN="#6FD08C"; BLUE="#5B84D6"; PURP="#B79CEB"
CARD="#1C1620"; CARD2="#241C29"; LINE="#362C38"
OS="font-family:Oswald, 'Arial Narrow', sans-serif"

def role(who, color, what, items):
    li=''.join(f'<p style="font-size:18px; line-height:1.4; color:{INK2}; word-break:keep-all">· {t}</p>' for t in items)
    return f'''<div class="rcard" style="flex:1; display:flex; flex-direction:column; gap:8px; background:{CARD}; border:1px solid {LINE}; border-top:4px solid {color}; border-radius:14px; padding:13px 18px">
      <p style="font-size:26px; font-weight:800; color:{color}">{who}</p>
      <p style="font-size:20px; color:{SUB}; margin-top:-4px">{what}</p>
      <div style="display:flex; flex-direction:column; gap:5px; border-top:1px solid {LINE}; padding-top:10px">{li}</div></div>'''

def case(n, title, flow, num, numlabel, color):
    return f'''<div class="ccard" style="display:flex; align-items:center; gap:18px; background:{CARD}; border-left:5px solid {color}; border-radius:12px; padding:8px 20px">
      <p style="{OS}; font-size:22px; font-weight:600; color:{color}; width:34px">{n}</p>
      <div style="flex:1.25"><p style="font-size:22px; font-weight:700; color:{INK}; word-break:keep-all">{title}</p></div>
      <p style="flex:1.9; font-size:19px; line-height:1.4; color:{SUB}; word-break:keep-all">{flow}</p>
      <div style="width:210px; text-align:right"><p style="{OS}; font-size:30px; font-weight:600; color:{color}">{num}</p>
      <p style="font-size:16px; color:{DIM}">{numlabel}</p></div></div>'''

def rule(n, t, d):
    return f'''<div style="flex:1; background:{CARD2}; border-radius:12px; padding:10px 16px">
      <p style="font-size:19px; font-weight:700; color:{GOLD}">{n} {t}</p>
      <p style="font-size:17px; line-height:1.35; color:{INK2}; margin-top:3px; word-break:keep-all">{d}</p></div>'''

body = f'''  <div class="spdband" style="display:flex; align-items:stretch; gap:16px; background:{CARD2}; border:2px solid {GOLD}; border-radius:16px; padding:14px 20px; margin-top:-2px">
    <div style="display:flex; align-items:center; gap:14px; flex:none; padding-right:20px; border-right:1px solid {LINE}">
      <p class="bigdays" data-count style="{OS}; font-size:54px; font-weight:600; line-height:1; color:{GOLD}">16일</p>
      <p style="font-size:19px; line-height:1.3; color:{INK2}">9/14 → 9/30<br>2명 · 부트캠프 병행</p>
    </div>
    <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:4px">
      <p style="font-size:22px; font-weight:400; line-height:1.35; color:{INK}">
        같은 범위를 AI 없이 했다면 — <b>EDA·라벨 검증 2주 + 학습 파이프라인 3주 + 서비스 구현 3주 + 발표자료 2주</b>
        <span style="color:{SUB}">(팀 추정)</span></p>
      <p style="font-size:22px; font-weight:700; line-height:1.3; color:{GOLD}">≈ 10주 걸릴 일을 16일에 — 학습 실험 10회 · 코드 5,120줄 · 문서 6종 · 발표 33장</p>
    </div>
  </div>
  <div style="display:flex; gap:16px">
    {role("사람", GOLD, "무엇을 왜 할지", ["가설 세우기 · 우선순위 결정", "지표·평가 규칙 정의", "결과 해석과 채택·기각 판단"])}
    {role("AI", BLUE, "어떻게 빨리 할지", ["분석·학습 스크립트 작성", "33장 발표자료 코드 생성", "개발기록·런북 문서화"])}
    {role("함께", GREEN, "막혔을 때", ["이상한 숫자 원인 추적", "에러 로그 해석 · 대안 제시", "반례 찾기 — 서로 검증"])}
  </div>
  <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px">
    {case("01", "라벨 의심 → 교차 검증", "“상황 컬럼이 정답이 맞나?” → 5명 투표와 교차표·엔트로피 즉시 계산", "68.1%", "불일치 발견 → 라벨 재정의", GOLD)}
    {case("02", "이상 점수 추적", "기준보다 높게 나온 점수 → 화자·파일 단위 대조 스크립트", "1,494개", "학습한 파일이 시험지에 · 누수 차단", RED)}
    {case("03", "아이디어 → 검증까지", "“쏠림을 펴면?” → 로짓 보정 스크립트 + τ 탐색 자동화", "+0.03", "재학습 0분 · UAR 0.663 → 0.695", GREEN)}
    {case("04", "발표자료를 코드로", "슬라이드를 HTML 생성기로 — 수치는 manifest 에서 자동 주입", "33장", "손으로 옮겨 적은 수치 0건", PURP)}
  </div>
  <div style="display:flex; gap:14px; margin-top:4px">
    {rule("규칙 1", "숫자는 실측만", "AI가 적은 값도 다시 계산해 확인")}
    {rule("규칙 2", "AI 제안도 기각한다", "SKT 중립 제외 가설 — 실험 후 수치로 기각")}
    {rule("규칙 3", "이해한 코드만 채택", "동작을 설명 못 하면 쓰지 않는다")}
    {rule("규칙 4", "원본은 서버 밖으로", "음성 원본은 반출하지 않고 서버에서 처리")}
  </div>'''

notes = """■ 기간: 맨 위 띠부터 말해. 9/14에 시작해 9/30 발표까지 16일이야. 데이터 보는 것부터 모델 학습, 서비스 구현, 발표자료까지 같은 범위를 AI 없이 했다면 팀 추정으로 10주쯤 걸릴 일이었어. 추정치라고 정확히 말하고, 대신 실측 가능한 숫자(실험 10회·코드 5,120줄·문서 6종·발표 33장)로 뒷받침해.\n■ 한 줄로: AI를 '대신 해주는 도구'가 아니라 '빠른 동료'로 썼고, 판단과 책임은 우리가 가졌다.
■ 역할 분담: 무엇을 왜 할지는 사람이, 어떻게 빨리 할지는 AI가. 막혔을 때는 같이 원인을 좁혀갔어.
■ 사례 4개 (전부 이번 프로젝트에서 실제로 있었던 것):
① 데이터에 붙어 있던 감정 라벨을 의심했고, 5명 투표와 대조하는 계산을 바로 돌려 68.1%를 찾았어.
② 점수가 기준보다 높게 나왔을 때 좋아하지 않고 파일 단위로 대조해서 1,494개 누수를 찾았어.
③ "쏠림을 펴면 어떨까"라는 아이디어를 스크립트로 만들어 재학습 없이 UAR을 0.03 올렸어.
④ 발표자료도 손으로 만든 게 아니라 생성 코드로 만들었어. 그래서 숫자가 바뀌면 다시 생성만 하면 되고, 옮겨 적다 틀릴 일이 없어.
■ 규칙 4개: 특히 '규칙 2'를 강조해. SKT 중립을 빼자는 건 AI가 제안한 가설이었는데, 실험해보니 틀려서 기각했어. AI 말을 그대로 따르지 않았다는 증거야.
■ 예상 질문: "AI가 다 한 거 아닌가요?" → 가설·지표·채택 기준은 저희가 정했고, AI가 낸 결론도 세 번 기각했습니다. 검증 루프가 있어서 틀린 제안이 걸러졌습니다.
■ 이렇게 말하면 돼: "속도는 AI에서, 판단과 책임은 저희가 가져갔습니다." """

html = f'''<section id="aiwork" data-transition="push" style="background:#120E14; color:{INK}; font-family:'Noto Sans KR', Arial, sans-serif; padding:74px 128px 80px; display:flex; flex-direction:column; gap:12px">
  <div style="display:flex; align-items:center; gap:28px">
    <p style="{OS}; font-size:34px; font-weight:600; color:{INK}; background:{RED}; border-radius:12px; padding:10px 24px">+</p>
    <h2 style="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif; font-size:56px; font-weight:400; line-height:1.15; color:{INK}">AI와 일한 방식 — 10주 걸릴 일을 16일에</h2>
  </div>
{body}
  <aside>{notes}</aside>
</section>
'''
open(os.path.join(SRC, "aiwork.html"), "w", encoding="utf-8").write(html)
print("aiwork", len(html))
