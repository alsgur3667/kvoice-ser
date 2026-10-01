# -*- coding: utf-8 -*-
"""텐서보드 실측 기록 — 무엇을 보고 무엇을 고쳤나 (실제 event 파일 값)"""
import os
SD = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"

INK='#120E14'; CARD='#1C1620'; CARD2='#241C29'; LINE='#362C38'
TX='#F5F0EA'; SUB='#D6C9CE'; MUT='#8E8188'; DIM='#6C5F70'
RED='#E8433F'; GOLD='#F2B63D'; BLUE='#9BB7E8'; GREEN='#6FD08C'
F = "font-family:'Noto Sans KR', Arial, sans-serif"
BH = "font-family:'Black Han Sans', 'Noto Sans KR', sans-serif"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"
TF = 'font-family="Oswald, sans-serif"'

# ── 실측값 (work/tb event 파일에서 그대로 읽음)
LOSS = [1.1624, 0.6440, 0.4663, 0.3821, 0.3346, 0.3023, 0.2822]
VUAR = [0.4664, 0.5933, 0.6053, 0.6039, 0.6030, 0.6174, 0.6032]
LW0  = [.0671,.0650,.0660,.0676,.0691,.0755,.0793,.0863,.0868,.0863,.0864,.0831,.0816]
LW1  = [.0293,.0301,.0282,.0333,.0370,.0481,.0601,.0805,.1056,.1532,.1581,.1579,.0784]
THR  = [30,35,40,45,50,55,60,65,70,75,80,85,90,95]
COV  = [.9988,.9934,.9739,.9510,.9156,.8744,.8315,.7762,.7230,.6663,.5993,.5203,.4139,.2445]
ACC  = [.8174,.8201,.8294,.8402,.8550,.8712,.8837,.9036,.9202,.9396,.9524,.9677,.9811,.9926]

W, H = 500, 272
L, R, T, B = 46, 486, 30, 232

def pts(vals, lo, hi, cls=""):
    n = len(vals)
    out = []
    for i, v in enumerate(vals):
        x = L + (R - L) * i / (n - 1)
        y = B - (B - T) * (v - lo) / (hi - lo)
        out.append(f"{x:.1f},{y:.1f}")
    return " ".join(out)

def dots(vals, lo, hi, color, cls):
    n = len(vals); o = ''
    for i, v in enumerate(vals):
        x = L + (R - L) * i / (n - 1)
        y = B - (B - T) * (v - lo) / (hi - lo)
        o += f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" stroke="{CARD}" stroke-width="2"/>'
    return o

grid = ''.join(f'<line x1="{L}" y1="{T+(B-T)*k/4:.0f}" x2="{R}" y2="{T+(B-T)*k/4:.0f}" stroke="#2A2230" stroke-width="1"/>' for k in range(5))

# ① 손실은 계속 내려가는데 val 은 2에폭부터 평평
c1 = (f'<svg class="tbfig" viewBox="0 0 {W} {H}" style="width:100%; height:{H}px">{grid}'
      + ''.join(f'<text {TF} font-size="15" fill="{DIM}" text-anchor="middle" x="{L+(R-L)*i/6:.0f}" y="{B+22}">ep{i}</text>' for i in range(7))
      + f'<polyline class="tbline tbl1" points="{pts(LOSS,0.2,1.25)}" fill="none" stroke="{RED}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
      + f'<polyline class="tbline tbl2" points="{pts(VUAR,0.42,0.66)}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
      + dots(VUAR, 0.42, 0.66, GOLD, 'tbdot')
      + f'<rect class="tbzone" x="{L+(R-L)*2/6:.0f}" y="{T}" width="{(R-L)*4/6:.0f}" height="{B-T}" fill="{GOLD}" opacity=".08"/>'
      + f'<text {TF} font-size="17" fill="{RED}" x="{L}" y="{T-8}">train loss 1.162</text>'
      + f'<text {TF} font-size="17" fill="{RED}" text-anchor="end" x="{R}" y="{B-26}">0.282</text>'
      + f'<text {TF} font-size="17" fill="{GOLD}" x="{L}" y="{B-6}">val UAR 0.466</text>'
      + f'<text {TF} font-size="17" font-weight="600" fill="{GOLD}" text-anchor="end" x="{R}" y="{T-8}">best ep5 = 0.617</text>'
      + f'<text font-family="\'Noto Sans KR\',sans-serif" font-size="17" fill="{TX}" text-anchor="middle" x="{L+(R-L)*4/6:.0f}" y="{T+96}">여기서부터 안 오른다</text>'
      + '</svg>')

# ② 레이어 가중치 — 균등 시작 → 상위층 쏠림
bw = (R - L) / 13 - 6
c2 = f'<svg class="tbfig" viewBox="0 0 {W} {H}" style="width:100%; height:{H}px">{grid}'
for i in range(13):
    x = L + (R - L) * i / 13 + 3
    h0 = (B - T) * LW0[i] / 0.17; h1 = (B - T) * LW1[i] / 0.17
    col = GOLD if LW1[i] > 0.10 else '#5A4E60'
    c2 += (f'<rect x="{x:.1f}" y="{B-h0:.1f}" width="{bw:.1f}" height="{h0:.1f}" rx="3" fill="#3A3140" opacity=".8"/>'
           f'<rect class="lwbar" x="{x:.1f}" y="{B-h1:.1f}" width="{bw:.1f}" height="{h1:.1f}" rx="3" fill="{col}"/>')
    if i % 2 == 0:
        c2 += f'<text {TF} font-size="14" fill="{DIM}" text-anchor="middle" x="{x+bw/2:.1f}" y="{B+22}">L{i:02d}</text>'
c2 += (f'<text {TF} font-size="17" fill="{MUT}" x="{L}" y="{T-8}">회색 = 학습 전(균등 0.067~0.087)</text>'
       f'<text {TF} font-size="17" font-weight="600" fill="{GOLD}" text-anchor="end" x="{R}" y="{T-8}">L09~L11 = 0.153~0.158</text></svg>')

# ③ 임계값 곡선 — 0.70 채택 근거
c3 = f'<svg class="tbfig" viewBox="0 0 {W} {H}" style="width:100%; height:{H}px">{grid}'
c3 += ''.join(f'<text {TF} font-size="15" fill="{DIM}" text-anchor="middle" x="{L+(R-L)*i/13:.0f}" y="{B+22}">{THR[i]/100:.1f}</text>' for i in (0,4,8,12))
xi = L + (R - L) * 8 / 13
c3 += (f'<line class="thrmark" x1="{xi:.0f}" y1="{T}" x2="{xi:.0f}" y2="{B}" stroke="{TX}" stroke-width="2" stroke-dasharray="5 5" opacity=".75"/>'
       f'<polyline class="tbline tbl3" points="{pts(COV,0.20,1.0)}" fill="none" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>'
       f'<polyline class="tbline tbl4" points="{pts(ACC,0.20,1.0)}" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linejoin="round"/>'
       f'<text {TF} font-size="17" fill="{BLUE}" x="{L}" y="{T-8}">커버리지 (판정한 비율)</text>'
       f'<text {TF} font-size="17" fill="{GREEN}" text-anchor="end" x="{R}" y="{T-8}">정확도 (맞힌 비율)</text>'
       f'<text {TF} font-size="18" font-weight="600" fill="{TX}" text-anchor="middle" x="{xi:.0f}" y="{T-8}">0.70 채택</text>'
       f'<text {TF} font-size="17" font-weight="600" fill="{BLUE}" text-anchor="end" x="{xi-10:.0f}" y="{T+92}">72.3%</text>'
       f'<text {TF} font-size="17" font-weight="600" fill="{GREEN}" x="{xi+10:.0f}" y="{T+56}">92.0%</text></svg>')

PANELS = [
    ("① 과적합 시작 지점", "train loss는 계속 내려가는데 val UAR은 <b>2에폭부터 평평</b>",
     "더 돌리면 좋아지는 게 아니라 외우는 중이었다", "ep5를 best로 저장하고 조기 종료", c1),
    ("② 어느 층을 쓰는지", "13개 레이어 가중치를 매 에폭 기록 — 균등하게 시작해 <b>상위층으로 쏠린다</b>",
     "감정은 음소가 아니라 상위 표현에 실려 있다", "레이어 가중합 구조를 그대로 유지하기로 확정", c2),
    ("③ 임계값을 정한 근거", "임계값 14개를 전부 기록 — 커버리지와 정확도의 교환비",
     "감으로 0.7을 고른 게 아니다", "0.70 채택 — 커버리지 72.3% · 정확도 92.0%", c3),
]

cards = ''
for tag, line, found, act, fig in PANELS:
    cards += (f'<div class="tbcard" style="flex:1; display:flex; flex-direction:column; gap:12px; background:{CARD}; '
              f'border:1px solid {LINE}; border-radius:16px; padding:22px 24px">'
              f'<p class="tbtag" style="{OS}; font-size:23px; font-weight:600; letter-spacing:1px; color:{GOLD}">{tag}</p>'
              f'<p style="font-size:22px; font-weight:400; line-height:1.45; color:{SUB}; min-height:64px">{line}</p>'
              f'{fig}'
              f'<div style="height:1px; background:{LINE}; margin-top:2px"></div>'
              f'<p style="font-size:20px; color:{MUT}">{found}</p>'
              f'<p style="font-size:23px; font-weight:700; line-height:1.35; color:{TX}">→ {act}</p></div>')

body = (f'<div style="display:flex; align-items:center; gap:24px">'
        f'<p style="{OS}; font-size:30px; font-weight:600; color:{TX}; background:{RED}; border-radius:10px; padding:8px 20px">03</p>'
        f'<h2 style="{BH}; font-size:52px; font-weight:400; line-height:1.15; color:{TX}">텐서보드 — 학습을 눈으로 보고 고쳤다</h2></div>'
        f'<p style="font-size:24px; font-weight:400; line-height:1.4; color:{SUB}; margin-top:-6px">'
        f'점수만 본 게 아니라 <b style="color:{TX}">손실 · val 지표 · 레이어 가중치 13개 · 임계값 14단계</b>를 매 에폭 기록했다. '
        f'아래는 실제 기록에서 <b style="color:{GOLD}">문제를 찾아 고친 세 장면</b>이다.</p>'
        f'<div style="display:flex; gap:18px; align-items:stretch">{cards}</div>'
        f'<div class="tbfoot" style="display:flex; align-items:center; gap:18px; background:{CARD2}; '
        f'border-left:5px solid {RED}; border-radius:12px; padding:11px 20px">'
        f'<p style="{OS}; font-size:20px; letter-spacing:3px; color:{RED}; white-space:nowrap">기록 덕분에</p>'
        f'<p style="font-size:22px; font-weight:400; line-height:1.35; color:{TX}">'
        f'터진 실험도 남아 있다 — xlsr 한국어 백본은 <b>1스텝</b>, 초기 WavLM은 <b>10스텝</b>에서 멈춘 기록이 그대로 있고, '
        f'<b style="color:{GOLD}">무엇이 언제 죽었는지 추적할 수 있었다.</b></p></div>'
        f'<p style="position:absolute; left:128px; bottom:38px; width:1664px; font-size:19px; color:#7A6E74">'
        f'work/tb 실측 · 전체 데이터 모델(full_1731) 학습 곡선 · 임계값 곡선은 기준 모델(pilot_1006) test 기록</p>')

note = """■ 한 줄로: 점수표만 들고 온 게 아니라, 학습 중에 뭘 보고 뭘 고쳤는지 텐서보드 기록으로 보여주는 장이야.
■ ① 과적합: 손실은 끝까지 내려가는데(1.162→0.282) val UAR은 2에폭부터 0.60 근처에서 평평해. 더 돌리면 좋아지는 게 아니라 외우는 중이라는 뜻이라 ep5(0.6174)를 best로 잡고 끊었어.
■ ② 레이어 가중치: 우리 모델은 13개 층 출력을 가중합해서 써. 학습 전엔 전부 0.067~0.087로 균등한데, 끝나면 L09~L11이 0.15대로 올라가고 하위층은 절반으로 떨어져. 감정 정보가 상위 표현에 실려 있다는 걸 눈으로 확인한 거야.
■ ③ 임계값: 0.30부터 0.95까지 14단계 커버리지/정확도를 전부 기록해놨어. 0.70에서 커버리지 72.3% 정확도 92.0% — 그래서 0.70을 골랐어. 감이 아니야.
■ 아래 띠: 실패한 실험 기록도 남아 있다는 얘기. xlsr은 1스텝, 초기 실험은 10스텝에서 멈춘 게 텐서보드에 그대로 있어서 언제 죽었는지 추적할 수 있었어.
■ 질문 대비: "왜 full 모델 곡선이냐" → 기준 모델(pilot)은 2~3시간짜리라 곡선이 짧고, 전체 데이터 학습이 에폭이 많아 곡선이 잘 보여서. 임계값 곡선은 서빙 기준 모델 기록을 썼다고 말하면 돼."""

open(os.path.join(SD, "tb.html"), "w", encoding="utf-8").write(
    f'''<section id="tb" data-transition="push" style="background:{INK}; color:{TX}; {F}; padding:74px 128px 118px; display:flex; flex-direction:column; gap:14px">
{body}
  <aside>{note}</aside>
</section>''')
print("tb 생성 완료")
