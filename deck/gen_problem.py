# -*- coding: utf-8 -*-
"""01 문제 정의 2장 — 갈등이 어떻게 시작되는지(일상 장면) + 왜 놓치는지(계기)"""
import os
SD = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"

INK='#120E14'; CARD='#1C1620'; CARD2='#241C29'; LINE='#362C38'
TX='#F5F0EA'; SUB='#D6C9CE'; MUT='#8E8188'; DIM='#6C5F70'
RED='#E8433F'; GOLD='#F2B63D'; BLUE='#9BB7E8'
F = "font-family:'Noto Sans KR', Arial, sans-serif"
BH = "font-family:'Black Han Sans', 'Noto Sans KR', sans-serif"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"

def head(num, title):
    return (f'<div style="display:flex; align-items:center; gap:28px">'
            f'<p style="{OS}; font-size:34px; font-weight:600; color:{TX}; background:{RED}; '
            f'border-radius:12px; padding:10px 24px">{num}</p>'
            f'<h2 style="{BH}; font-size:66px; font-weight:400; line-height:1.15; color:{TX}">{title}</h2></div>')

def foot(t):
    return f'<p style="position:absolute; left:128px; bottom:60px; width:1664px; font-size:22px; color:#7A6E74">{t}</p>'

# ══════════════════════════════════════════════════════════════
# A. 갈등은 갑자기 터지지 않는다 — 일상 장면 3개
# ══════════════════════════════════════════════════════════════
dumbbell = f'''<svg class="pfig pfig0" viewBox="0 0 440 118" style="width:100%; height:118px; overflow:visible">
  <line x1="14" y1="96" x2="426" y2="96" stroke="#2E2634" stroke-width="1"/>
  <g {OS.replace("font-family:","font-family=").replace(", 'Arial Narrow', sans-serif","")}
     font-family="Oswald, sans-serif" font-size="16" fill="{DIM}" text-anchor="middle">
    <text x="14" y="116">60</text><text x="151" y="116">70</text><text x="288" y="116">80</text><text x="426" y="116">90%</text></g>
  <line class="dgline" x1="160" y1="62" x2="295" y2="62" stroke="#5A4E60" stroke-width="5" stroke-linecap="round"/>
  <circle class="dgd" cx="160" cy="62" r="15" fill="{RED}" stroke="{CARD}" stroke-width="2"/>
  <circle class="dgd" cx="295" cy="62" r="15" fill="{GOLD}" stroke="{CARD}" stroke-width="2"/>
  <text class="dglab" x="160" y="30" text-anchor="middle" font-family="'Noto Sans KR',sans-serif" font-size="21" font-weight="700" fill="{TX}">아내 70.7</text>
  <text class="dglab" x="295" y="30" text-anchor="middle" font-family="'Noto Sans KR',sans-serif" font-size="21" font-weight="700" fill="{TX}">남편 80.5</text>
</svg>'''

vals = [2130, 3155, 5823, 7774, 10158, 12253]
yrs = ["'19", "'20", "'21", "'22", "'23", "'24"]
bw, gap = 54, 18
bars = ''.join(
    f'<rect class="pbar" x="{i*(bw+gap)+8}" y="{96 - v/12253*78:.0f}" width="{bw}" height="{v/12253*78:.0f}" rx="5" '
    f'fill="{RED if i==5 else "#5A3238"}"/>'
    f'<text class="pblab" x="{i*(bw+gap)+8+bw/2}" y="114" text-anchor="middle" font-family="Oswald, sans-serif" '
    f'font-size="16" fill="{DIM}">{yrs[i]}</text>' for i, v in enumerate(vals))
barchart = (f'<svg class="pfig pfig1" viewBox="0 0 440 118" style="width:100%; height:118px; overflow:visible">{bars}'
            f'<text class="pblab" x="8" y="{96 - 2130/12253*78 - 10:.0f}" font-family="Oswald, sans-serif" font-size="17" fill="{MUT}">2,130</text>'
            f'<text class="pbtop" x="{5*(bw+gap)+8+bw/2}" y="{96 - 78 - 10:.0f}" text-anchor="middle" font-family="Oswald, sans-serif" '
            f'font-size="19" font-weight="600" fill="{RED}">12,253</text></svg>')

dots = ''.join(
    f'<circle class="ppl" data-i="{i}" cx="{28 + (i%10)*44}" cy="{38 + (i//10)*46}" r="15" fill="{RED if i in (0,1) else "#3A3140"}"/>'
    for i in range(10))
people = (f'<svg class="pfig pfig2" viewBox="0 0 440 118" style="width:100%; height:118px; overflow:visible">{dots}'
          f'<text class="pplab" x="28" y="106" font-family="\'Noto Sans KR\',sans-serif" font-size="21" font-weight="700" fill="{GOLD}">'
          f'관계가 없어서가 아니다</text></svg>')

SCENES = [
    ("집 · 저녁 식탁", "“괜찮아. 신경 쓰지 마.”",
     "말은 괜찮다고 했지만 목소리는 아니었다. 그날의 대화를 두 사람은 <b style='color:" + GOLD + "'>서로 다르게 기억한다.</b>",
     "<span data-count>9.8</span><span style='font-size:30px'>%p</span>", "같은 결혼생활, 다른 만족도", dumbbell),
    ("상담센터 · 통화 3분", "“네… 알겠습니다.”",
     "같은 설명을 세 번째 하던 참이었다. 고객이 <b style='color:" + GOLD + "'>어디서 돌아섰는지는 통화가 끝난 뒤에야</b> 안다.",
     "<span data-count>5.8</span><span style='font-size:30px'>배</span>", "직장 내 괴롭힘 신고 · 5년", barchart),
    ("매일 하는 안부 전화", "“별일 없어.”",
     "매일 통화하는데도 <b style='color:" + GOLD + "'>“아무도 나를 잘 알지 못한다”</b>고 답한 사람이 16.2%다.",
     "<span data-count>21.1</span><span style='font-size:30px'>%</span>", "국민 5명 중 1명이 외로움", people),
]

cards = ''
for tag, line, desc, big, cap, fig in SCENES:
    cards += (f'<div class="pcard" style="flex:1; display:flex; flex-direction:column; gap:12px; background:{CARD}; '
              f'border:1px solid {LINE}; border-radius:18px; padding:26px 28px">'
              f'<p class="ptag" style="{OS}; font-size:20px; font-weight:600; letter-spacing:3px; color:{GOLD}">{tag}</p>'
              f'<p class="pquote" style="{BH}; font-size:40px; line-height:1.25; color:{TX}">{line}</p>'
              f'<p style="font-size:24px; font-weight:400; line-height:1.55; color:{SUB}; min-height:112px" class="pdesc">{desc}</p>'
              f'<div class="pdiv" style="height:1px; background:{LINE}"></div>'
              f'<div class="pnumrow" style="display:flex; align-items:baseline; gap:12px">'
              f'<p class="pbig" style="{OS}; font-size:52px; font-weight:600; line-height:1; color:{TX}">{big}</p>'
              f'<p class="pcap" style="font-size:21px; color:{MUT}">{cap}</p></div>'
              f'{fig}</div>')

body_a = (head("01", "신호는 통화 중에 지나가고, 결과만 남는다")
          + f'<p style="font-size:29px; font-weight:400; line-height:1.5; color:{SUB}; margin-top:-8px">'
            f'아래 세 장면 모두 <b style="color:{TX}">말투에 신호가 있었지만, 통화 중에는 아무도 알아채지 못했다.</b></p>'
          + f'<div style="display:flex; gap:22px; align-items:stretch">{cards}</div>'
          + f'<div class="pcommon" style="display:flex; align-items:center; gap:18px; background:{CARD2}; border-left:5px solid {RED}; '
            f'border-radius:12px; padding:20px 26px">'
            f'<p style="{OS}; font-size:21px; letter-spacing:3px; color:{RED}">COMMON</p>'
            f'<p style="font-size:27px; font-weight:400; line-height:1.4; color:{TX}">세 장면 공통 — '
            f'<b>신호는 그 자리에서 지나가고, 남는 건 신고·이탈 같은 결과뿐이다.</b></p></div>'
          + foot('출처 — 결혼생활 만족도: 통계청 「2024년 사회조사」 · 외로움·고립감: 국가데이터처 「2024 한국의 사회지표」 · '
                 '직장 내 괴롭힘: 고용노동부 제출자료(2025), <b>접수 신고 건수</b> 기준이며 발생 건수가 아님'))

open(os.path.join(SD, "problem.html"), "w", encoding="utf-8").write(
    f'''<section id="problem" data-transition="push" style="background:{INK}; color:{TX}; {F}; padding:120px 128px 150px; display:flex; flex-direction:column; gap:22px">
{body_a}
  <aside>■ 한 줄로: 갈등은 어느 날 갑자기가 아니라, 신호를 놓친 결과다.
■ 장면 세 개를 순서대로 읽어줘. 통계부터 말하지 말고 장면부터.
- 집: "괜찮아"라고 말했지만 목소리는 아니었어. 그런데 그날 대화를 두 사람이 다르게 기억해. 같은 결혼생활인데 만족도가 남편 80.5%, 아내 70.7%야.
- 상담센터: 고객이 어느 지점에서 돌아섰는지는 통화가 끝난 뒤에야 알아. 그리고 관계가 틀어진 건 신고나 퇴사 같은 결과로만 드러나. 신고가 5년 만에 5.8배가 됐어.
- 안부 전화: 매일 통화하는데도 5명 중 1명이 외롭다고 하고, 16.2%는 아무도 나를 모른다고 답했어. 관계가 없어서가 아니야.
■ 주의: 괴롭힘 숫자는 '신고 건수'지 발생 건수가 아니야. 각주에 써놨고, 말할 때도 "신고가"라고 정확히 말할 것.
■ 이렇게 말하면 돼: "세 장면 다 같은 구조입니다. 틀어진 순간은 지나가고 결과만 남습니다."</aside>
</section>''')

# ══════════════════════════════════════════════════════════════
# B. 왜 그 순간을 놓치나 → 그래서 우리가 만든 것
# ══════════════════════════════════════════════════════════════
REASONS = [
    ("01", "말은 남고 말투는 사라진다",
     "기억도 기록도 <b>“무슨 말을 했는지”</b>만 남긴다. 정작 감정은 <b style='color:" + GOLD + "'>“어떻게 말했는지”</b>에 실려 있다.",
     "같은 “괜찮아요”도 톤·속도·떨림이 다르면 다른 뜻이다"),
    ("02", "대화 중에는 보이지 않는다",
     "당사자는 듣고 <b>답하느라 바쁘다.</b> 신호를 알아채는 건 대개 <b style='color:" + GOLD + "'>지나고 나서다.</b>",
     "“그때 좀 이상하긴 했지” — 항상 사후에 나오는 말"),
    ("03", "녹음이 있어도 다시 듣지 않는다",
     "3분짜리 통화를 <b>처음부터 다시 듣는 사람은 없다.</b> 어디를 들어야 할지 모르니까.",
     "쌓인 녹취는 사실상 열리지 않는 서랍이다"),
]
rcards = ''
for n, t, d, sub in REASONS:
    rcards += (f'<div class="rcard" style="flex:1; display:flex; flex-direction:column; gap:12px; background:{CARD}; '
               f'border:1px solid {LINE}; border-radius:18px; padding:28px 30px">'
               f'<p class="rnum" style="{OS}; font-size:40px; font-weight:600; line-height:1; color:{RED}">{n}</p>'
               f'<h3 class="rtit" style="font-size:31px; font-weight:700; line-height:1.3; color:{TX}">{t}</h3>'
               f'<p class="rdesc" style="font-size:24px; font-weight:400; line-height:1.6; color:{SUB}">{d}</p>'
               f'<p class="rsub" style="font-size:21px; color:{MUT}; margin-top:auto">{sub}</p></div>')

steps = ''
for ico, t in (("3초마다 읽는다", "통화 한 건을 3초 창으로 잘라 감정을 찍는다"),
               ("흐름을 그린다", "어디서 올라가고 꺾였는지 한 줄로 보인다"),
               ("그 구간만 듣는다", "클릭하면 그 지점부터 재생 — 10초면 확인된다")):
    steps += (f'<div class="stepbx" style="flex:1; background:#3B2E1A; border:1px solid {GOLD}; border-radius:14px; padding:18px 22px">'
              f'<p style="font-size:25px; font-weight:700; color:{GOLD}">{ico}</p>'
              f'<p style="font-size:22px; font-weight:400; line-height:1.45; color:{TX}; margin-top:6px">{t}</p></div>')

body_b = (head("01", "그래서 만든 것 — 통화를 3초마다 읽는다")
          + f'<p style="font-size:29px; font-weight:400; line-height:1.5; color:{SUB}; margin-top:-8px">'
            f'만들기 전에 먼저 따져봤다 — <b style="color:{TX}">왜 아무도 제때 알아채지 못하나?</b></p>'
          + f'<div style="display:flex; gap:22px; align-items:stretch">{rcards}</div>'
          + f'<div class="ansrow" style="display:flex; align-items:center; gap:20px; margin-top:4px">'
            f'<p class="anslab" style="{OS}; font-size:22px; letter-spacing:4px; color:{GOLD}; white-space:nowrap">OUR ANSWER</p>'
            f'<p class="anstxt" style="font-size:30px; font-weight:700; line-height:1.4; color:{TX}">'
            f'대화 내용이 아니라 <b style="color:{GOLD}">말투</b>를 읽어서, 감정이 틀어진 지점을 찾아준다</p></div>'
          + f'<div style="display:flex; gap:18px; align-items:stretch">{steps}</div>'
          + foot('녹취 내용을 저장하지 않고 소리만 분석한다 · 판단은 사람이 하고, 우리는 “여기를 보라”고 표시할 뿐이다'))

open(os.path.join(SD, "problem2.html"), "w", encoding="utf-8").write(
    f'''<section id="problem2" data-transition="push" style="background:{INK}; color:{TX}; {F}; padding:120px 128px 150px; display:flex; flex-direction:column; gap:22px">
{body_b}
  <aside>■ 한 줄로: 왜 놓치는지 세 가지 이유를 먼저 말하고, 그게 우리가 만든 것의 이유가 된다.
■ 세 가지 이유:
- 말은 남고 말투는 사라진다. 녹취록을 봐도 "괜찮아요"라고만 적혀 있어. 감정은 어떻게 말했는지에 실려 있는데 그게 안 남아.
- 대화 중에는 안 보여. 듣고 답하느라 바쁘니까. "그때 좀 이상하긴 했지"는 항상 나중에 나오는 말이야.
- 녹음이 있어도 안 들어. 3분을 처음부터 듣는 사람은 없어. 어디를 들어야 할지 모르니까.
■ 그래서 우리가 한 것: 3초마다 감정을 찍어서 흐름을 그리고, 틀어진 지점을 클릭하면 그 구간부터 재생돼. 10초면 확인돼.
■ 마지막 각주도 꼭 말해: 내용을 저장하지 않고 소리만 본다는 것, 판단은 사람이 한다는 것. 감시 도구로 오해받지 않으려면 여기서 못을 박아야 해.
■ 이렇게 말하면 돼: "못 듣는 게 아니라 어디를 들어야 할지 모르는 게 문제였습니다. 그 지점을 찾아주는 걸 만들었습니다."</aside>
</section>''')

print("problem / problem2 생성 완료")
