# -*- coding: utf-8 -*-
"""간트 차트 — 최종 발표본용. 전부 완료 상태로 채운다 (9/14 ~ 9/30)."""
import datetime as dt, os
SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"

INK = "#F5F0EA"; INK2 = "#D2C8CD"; SUB = "#ADA1A7"; DIM = "#7A6E74"
RED = "#E8433F"; GOLD = "#F2B63D"; LINE = "#362C38"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"

D0 = dt.date(2026, 9, 14); DN = 17            # 9/14 ~ 9/30
SHOW = (dt.date(2026, 9, 30) - D0).days       # 발표일 표시선

G = [("데이터", "AI-Hub 수집 · EDA · 라벨 재정의",        0, 3),
     ("데이터", "전처리 · 화자 독립 분할",                2, 2),
     ("모델",   "기준 모델 학습 · 백본 비교",             1, 4),
     ("검증",   "외부 검증 · 경량화 실측",                3, 3),
     ("데이터", "SKT 15만 확보 · 학습 서버 구축",         3, 5),
     ("발표",   "기획발표 준비 · 발표",                   6, 3),
     ("모델",   "SKT 혼합 학습 (mix40k)",                 8, 2),
     ("모델",   "중립 구조 분석 · 로짓 보정 τ0.6",        9, 2),
     ("서비스", "데모 화면 · 랜딩페이지 구현",           11, 3),
     ("서비스", "FastAPI · Supabase · Docker 연동",      13, 2),
     ("서비스", "모델 연결 · 음성 재생 · 대시보드",      14, 2),
     ("발표",   "최종 발표 자료 · 리허설",               14, 3)]
GC = {"데이터": GOLD, "모델": RED, "검증": "#6FD08C", "발표": "#E58BC0", "서비스": "#5B84D6"}

LW = 470; CW = (1664 - LW) / DN; RH = 46

head = ''.join(
    f'<div style="position:absolute; left:{LW + i*CW:.1f}px; width:{CW:.1f}px; top:0; text-align:center">'
    f'<p style="{OS}; font-size:17px; color:{GOLD if i==SHOW else (SUB if (D0+dt.timedelta(i)).weekday()<5 else DIM)}">'
    f'{(D0+dt.timedelta(i)).day}</p></div>' for i in range(DN))
wk = ''.join(
    f'<div style="position:absolute; left:{LW + i*CW:.1f}px; top:28px; bottom:0; width:{CW*2:.1f}px; '
    f'background:rgba(255,255,255,.025)"></div>'
    for i in range(DN) if (D0+dt.timedelta(i)).weekday() == 5)

grow = ''
for r, (cat, name, s, n) in enumerate(G):
    y = 36 + r * RH; c = GC[cat]
    grow += (f'<p style="position:absolute; left:0; top:{y+7}px; width:{LW-20}px; font-size:21px; color:{INK}; '
             f'white-space:nowrap"><span style="display:inline-block; width:84px; font-size:17px; font-weight:700; '
             f'color:{c}">{cat}</span>{name}</p>'
             f'<div class="gbar gdone" style="position:absolute; left:{LW + s*CW + 2:.1f}px; top:{y+5}px; '
             f'width:{n*CW - 4:.1f}px; height:{RH-14}px; border-radius:8px; background:{c}; '
             f'display:flex; align-items:center; justify-content:flex-end; padding-right:10px">'
             f'<span style="font-size:18px; font-weight:700; color:#120E14">✓</span></div>')

H_ = 36 + len(G) * RH + 8
months = (f'<p style="position:absolute; left:{LW}px; top:-28px; font-size:18px; color:{SUB}">9월</p>')

gantt = f'''<div style="position:relative; height:{H_}px; margin-top:24px">
    {wk}{months}{head}{grow}
    <div class="gtoday" style="position:absolute; left:{LW + SHOW*CW + CW/2:.1f}px; top:28px; bottom:-6px; border-left:3px solid {GOLD}"></div>
    <p style="position:absolute; left:{LW + SHOW*CW + CW/2 - 210:.1f}px; top:{H_-2}px; font-size:19px; font-weight:700; color:{GOLD}; text-align:right; width:200px">오늘 9/30 · 최종 발표</p>
  </div>'''

leg = ''.join(
    f'<div style="display:flex; align-items:center; gap:8px">'
    f'<div style="width:26px; height:14px; border-radius:4px; background:{c}"></div>'
    f'<p style="font-size:19px; color:{INK2}">{k}</p></div>' for k, c in GC.items())

body = f'''{gantt}
  <div style="display:flex; gap:24px; align-items:center; margin-top:14px">{leg}
    <p style="font-size:19px; color:{GOLD}; margin-left:auto; font-weight:700">16일 · 12개 작업 전부 완료</p></div>'''

notes = """■ 한 줄로: 2주 반 동안 12개 작업, 전부 끝냈다.
■ 색은 분야야. 노랑=데이터, 빨강=모델, 초록=검증, 파랑=서비스 구현, 분홍=발표.
■ 흐름을 말해: 앞 일주일은 데이터(수집·EDA·전처리·분할)와 기준 모델, 가운데는 SKT 혼합 학습과 로짓 보정, 뒤 일주일은 서비스 구현(화면 → FastAPI·Supabase·Docker → 모델 연결·재생·대시보드).
■ 기획발표(9/22) 이후 받은 피드백을 그 다음 주 작업에 그대로 반영했다는 점을 짚으면 좋아.
■ 이렇게 말하면 돼: "계획만 세운 게 아니라 마지막 서비스 구현까지 다 끝내고 왔습니다." """

sec = f'''<section id="gantt" data-transition="push" style="background:#120E14; color:{INK}; font-family:'Noto Sans KR', Arial, sans-serif; padding:104px 128px 120px; display:flex; flex-direction:column; gap:26px">
  <div style="display:flex; align-items:center; gap:28px">
    <p style="{OS}; font-size:34px; font-weight:600; color:{INK}; background:{RED}; border-radius:12px; padding:10px 24px">04</p>
    <h2 style="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif; font-size:66px; font-weight:400; line-height:1.15; color:{INK}">간트 차트</h2>
  </div>
{body}
  <aside>{notes}</aside>
</section>
'''
open(os.path.join(SRC, "gantt.html"), "w", encoding="utf-8").write(sec)
print("gantt 재생성:", len(sec), "bytes ·", len(G), "행 · 전부 완료")
