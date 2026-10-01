# -*- coding: utf-8 -*-
"""03 실험한 모델 — 수치가 한눈에 보이는 비교"""
import os
SD = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"
INK='#120E14'; CARD='#1C1620'; CARD2='#241C29'; LINE='#362C38'
TX='#F5F0EA'; SUB='#D6C9CE'; MUT='#8E8188'; DIM='#6C5F70'
RED='#E8433F'; GOLD='#F2B63D'; BLUE='#9BB7E8'; GREEN='#6FD08C'
F="font-family:'Noto Sans KR', Arial, sans-serif"
BH="font-family:'Black Han Sans', 'Noto Sans KR', sans-serif"
OS="font-family:Oswald, 'Arial Narrow', sans-serif"

# (모델, 방식, UAR, 표기, 해석, 상태, 색)
ROWS = [
 ("emotion2vec+ large", "특징 고정 · 백본 안 건드림", 0.287, "0.287",
  "이미 자체 분류기로 학습된 모델 — 임베딩이 전이되지 않았다", "기각", DIM),
 ("emotion2vec base", "특징 고정 · 백본 안 건드림", 0.573, "0.573",
  "SSL 원본으로 바꾸자 <b>2배</b> · 시드마다 ±0.07 흔들림", "기각", BLUE),
 ("WavLM-base+ · 고신뢰 2.5만", "전체 파인튜닝", 0.734, "0.734",
  "<b>기준 모델</b> · WAR 0.817 · 처음 보는 화자에서도 유지", "기준 모델", GOLD),
 ("WavLM × emotion2vec 앙상블", "확률 가중평균 0.7/0.3", 0.745, "0.745",
  "내부 +0.011인데 <b>외부 검증 이득 0</b> — 복잡도만 늘어 기각", "기각", DIM),
 ("WavLM-base+ · 전체 4.4만", "전체 파인튜닝", 0.675, "0.675*",
  "시험지가 더 어려운 쪽 · 놀람 F1 0.44 → <b>0.63</b>", "다음 단계", BLUE),
 ("+ SKT 4만 혼합 · 로짓 보정", "이어학습 + τ0.6 보정", 0.695, "0.695*",
  "재학습 없이 <b>+0.032</b> · WAR 0.721 유지 → <b>서빙 모델</b>", "서빙 모델", GREEN),
]
MAX = 0.80
rows = ''
for name, how, v, label, why, state, col in ROWS:
    picked = state in ("기준 모델", "서빙 모델")
    pct = v / MAX * 100
    rows += (f'<div class="mrow" style="display:flex; align-items:center; gap:18px; background:{CARD2 if picked else CARD}; '
             f'border:1px solid {col if picked else LINE}; border-radius:12px; padding:15px 20px">'
             f'<div style="width:400px; flex:none">'
             f'<p style="font-size:23px; font-weight:700; line-height:1.2; color:{TX}">{name}</p>'
             f'<p style="font-size:18px; color:{MUT}; margin-top:2px">{how}</p></div>'
             f'<div style="width:300px; flex:none; position:relative; height:26px; background:#241C29; border-radius:6px; overflow:hidden">'
             f'<div class="mbar" style="position:absolute; left:0; top:0; height:100%; width:{pct:.1f}%; background:{col}; '
             f'border-radius:6px; opacity:{".95" if picked else ".55"}"></div></div>'
             f'<p class="mnum" data-count style="{OS}; font-size:36px; font-weight:600; line-height:1; color:{col}; '
             f'width:118px; flex:none; text-align:right">{label}</p>'
             f'<p style="flex:1; font-size:20px; font-weight:400; line-height:1.35; color:{SUB}">{why}</p>'
             f'<p class="mbadge" style="{OS}; font-size:18px; font-weight:600; letter-spacing:1px; white-space:nowrap; '
             f'color:{INK if picked else MUT}; background:{col if picked else "transparent"}; '
             f'border:1px solid {col if picked else LINE}; border-radius:999px; padding:3px 12px; flex:none">{state}</p></div>')

body = (f'<div style="display:flex; align-items:center; gap:24px">'
        f'<p style="{OS}; font-size:30px; font-weight:600; color:{TX}; background:{RED}; border-radius:10px; padding:8px 20px">03</p>'
        f'<h2 style="{BH}; font-size:52px; font-weight:400; line-height:1.15; color:{TX}">'
        f'모델 6개를 돌려 0.287에서 0.695까지</h2></div>'
        f'<p style="font-size:23px; font-weight:400; line-height:1.4; color:{SUB}; margin-top:-6px">'
        f'막대는 화자 독립 test <b style="color:{TX}">UAR</b> (7클래스 랜덤 추측 = 0.143). '
        f'<b style="color:{GOLD}">점수가 제일 높은 걸 고른 게 아니라, 외부 검증까지 통과한 걸 골랐다.</b></p>'
        f'<div style="display:flex; flex-direction:column; gap:11px">{rows}</div>'
        f'<div class="mnote" style="display:flex; align-items:center; gap:18px; background:{CARD2}; '
        f'border-left:5px solid {RED}; border-radius:12px; padding:12px 20px">'
        f'<p style="{OS}; font-size:20px; letter-spacing:3px; color:{RED}; white-space:nowrap">주의</p>'
        f'<p style="font-size:21px; font-weight:400; line-height:1.35; color:{TX}">'
        f'* 표시한 두 줄은 <b>시험지가 다르다</b> — 위 네 줄은 고신뢰 test(n=3,329), * 는 전체 test(n=4,840). '
        f'<b style="color:{GOLD}">0.734와 0.695를 같은 선에 놓고 비교하면 안 된다.</b></p></div>'
        f'<p style="position:absolute; left:128px; bottom:38px; width:1664px; font-size:19px; color:#7A6E74">'
        f'주 지표 UAR = 감정별 재현율의 평균 (개수가 적은 감정도 똑같이 한 표) · 전체 수치는 work/tb 및 compare 리포트 실측</p>')

note = """■ 한 줄로: 여섯 개를 돌렸고, 제일 높은 걸 고른 게 아니라 외부 검증까지 통과한 걸 골랐어.
■ 막대 길이가 UAR이야. 랜덤이 0.143이니까 첫 줄 0.287은 랜덤의 두 배밖에 안 되는 거야.
- emotion2vec+ large 0.287: 제일 유명한 모델인데 꼴찌. 이미 자기 방식으로 분류 훈련이 끝난 모델이라 특징이 전이가 안 됐어.
- emotion2vec base 0.573: 같은 계열 원본. 바꾸자마자 두 배.
- WavLM 고신뢰 0.734: 통째로 파인튜닝한 기준 모델.
- 앙상블 0.745: 제일 높아. 근데 외부 검증에서 이득이 0이라 버렸어. 이 줄이 이 장의 핵심이야 — 숫자가 제일 높은 걸 안 골랐다는 것.
- 아래 두 줄(*)은 시험지가 다른 전체 데이터 기준이야. 0.734랑 직접 비교하면 안 돼. 그 안에서는 0.675 → 0.695로 올렸고, 그게 지금 서빙 모델이야.
■ 이렇게 말하면 돼: "가장 높은 점수(0.745)를 버리고 0.734를 택한 이유가 이 장의 요지입니다." """

open(os.path.join(SD, "models.html"), "w", encoding="utf-8").write(
    f'''<section id="models" data-transition="push" style="background:{INK}; color:{TX}; {F}; padding:74px 128px 118px; display:flex; flex-direction:column; gap:14px">
{body}
  <aside>{note}</aside>
</section>''')
print("models 재생성 완료")
