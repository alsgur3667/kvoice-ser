# -*- coding: utf-8 -*-
# 05 대시보드 화면 예시 (s05c) — 서비스 통계 + 모델 모니터링 · 예시 데이터
import random, math
from gen_demo import SD, BG, CARD, BD, TX, SUB, MUT, RED, GOLD, EMO, DECK_INK, DECK_INK2, icon, frame, callout, card, side, stat
random.seed(7)
ORDER = ['angry', 'disgust', 'fear', 'sadness', 'surprise', 'neutral', 'happy']

# ① 일별 감정 분포 (7일 · 100% 누적 막대)
DAYS = ['9/16', '9/17', '9/18', '9/19', '9/20', '9/21', '9/22']
CALLS = [96, 112, 104, 88, 41, 37, 128]
def dist(d):
    base = {'angry': 11, 'disgust': 3, 'fear': 3, 'sadness': 14, 'surprise': 2, 'neutral': 49, 'happy': 18}
    if d == 6: base.update(angry=17, sadness=16, neutral=44, happy=13)
    if d in (4, 5): base.update(angry=7, neutral=53, happy=21)
    v = {k: max(1, x + random.randint(-2, 2)) for k, x in base.items()}; t = sum(v.values())
    return {k: x / t for k, x in v.items()}
def daily_svg(W=620, H=250):
    bw = 54; gap = (W - 40 - bw * 7) / 6; out = []
    for d in range(7):
        x = 40 + d * (bw + gap); y = H - 26; ds = dist(d)
        for k in ORDER:
            h = ds[k] * (H - 50)
            out.append(f'<rect class="dseg" x="{x:.1f}" y="{y-h:.1f}" width="{bw}" height="{h:.1f}" fill="{EMO[k][1]}"/>'); y -= h
        out.append(f'<text x="{x+bw/2:.1f}" y="{H-6}" text-anchor="middle" font-size="13" fill="{SUB}" font-family="Oswald, sans-serif">{DAYS[d]}</text>')
        out.append(f'<text x="{x+bw/2:.1f}" y="15" text-anchor="middle" font-size="12.5" fill="{MUT}" font-family="Oswald, sans-serif">{CALLS[d]}건</text>')
    for p in (0, 50, 100):
        yy = H - 26 - p / 100 * (H - 50)
        out.append(f'<text x="30" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="{MUT}" font-family="Oswald, sans-serif">{p}%</text>')
    return f'<svg width="{W}" height="{H}" style="display:block; overflow:visible">{"".join(out)}</svg>'

# ② 시간대별 부정 감정 비율 (히트 스트립)
HOURS = list(range(9, 19))
NEG = [18, 21, 24, 31, 22, 26, 29, 35, 27, 20]
def hour_strip():
    cells = ''.join(f'<div class="hcell" style="flex:1; display:flex; flex-direction:column; align-items:center; gap:4px">'
                    f'<div style="width:100%; height:42px; border-radius:6px; background:rgba(232,67,63,{0.12 + (v-15)/22*0.8:.2f})"></div>'
                    f'<p style="font-size:12px; color:{SUB}; font-family:Oswald,sans-serif">{h}시</p></div>' for h, v in zip(HOURS, NEG))
    return f'<div style="display:flex; gap:5px">{cells}</div>'

# ③ 상담사별 부정 감정 통화 비율
AGENTS = [('상담사 A', 34, 41), ('상담사 B', 27, 38), ('상담사 C', 22, 45), ('상담사 D', 16, 36), ('상담사 E', 12, 29)]
def agent_bars():
    return ''.join(f'''<div style="display:flex; align-items:center; gap:10px">
      <p style="width:66px; font-size:13.5px; color:{TX}">{n}</p>
      <div style="flex:1; height:14px; background:#F0ECE9; border-radius:7px"><div class="pbar" style="width:{v/40*100:.0f}%; height:14px; border-radius:7px; background:{RED if v >= 30 else ("#F08A7E" if v >= 20 else "#F4B9B2")}"></div></div>
      <p style="width:40px; text-align:right; font-size:14px; font-weight:700; color:{TX}; font-family:Oswald,sans-serif">{v}%</p>
      <p style="width:48px; text-align:right; font-size:12.5px; color:{MUT}">{c}건</p></div>''' for n, v, c in AGENTS)

# ④ 위험 통화 목록
RISK = [('#0922-118', '14:42', '상담사 A', '분노 1분 12초 지속', '중립 → 분노 → 분노', '확인 필요', RED),
        ('#0922-097', '13:05', '상담사 C', '분노 48초 · 혐오', '분노 → 혐오 → 슬픔', '확인 필요', RED),
        ('#0922-071', '11:38', '상담사 B', '슬픔 2분 · 급하강', '중립 → 슬픔', '케어 연결', '#5B84D6'),
        ('#0922-054', '10:51', '상담사 A', '분노 36초', '분노 → 중립 → 기쁨', '해결됨', '#1E7F4E')]
def risk_table():
    hd = ''.join(f'<p style="flex:{w}; font-size:12.5px; color:{MUT}">{t}</p>' for t, w in (('통화', 1.1), ('시각', .6), ('상담사', .8), ('위험 구간', 1.6), ('감정 흐름', 1.8), ('상태', .9)))
    rows = ''.join(f'''<div class="rrow" style="display:flex; align-items:center; gap:8px; padding:9px 10px; border-top:1px solid {BD}; {"background:#FFF5F4" if i == 0 else ""}">
      <p style="flex:1.1; font-size:14px; font-weight:700; color:{TX}; font-family:Oswald,sans-serif">{a}</p>
      <p style="flex:.6; font-size:13.5px; color:{SUB}; font-family:Oswald,sans-serif">{b}</p>
      <p style="flex:.8; font-size:13.5px; color:{TX}">{c}</p>
      <p style="flex:1.6; font-size:13.5px; color:{RED}; font-weight:700">{d}</p>
      <p style="flex:1.8; font-size:13.5px; color:{SUB}">{e}</p>
      <p style="flex:.9"><span style="font-size:12.5px; font-weight:700; color:{g}; background:{g}1A; border-radius:999px; padding:3px 10px; white-space:nowrap">{f}</span></p></div>''' for i, (a, b, c, d, e, f, g) in enumerate(RISK))
    return f'<div style="display:flex; gap:8px; padding:0 10px 6px">{hd}</div>{rows}'

# ⑤ 모델 모니터링
def spark(vals, W, H, color, lo, hi, thr=None, fill=True):
    n = len(vals); pts = [(i / (n - 1) * W, H - (v - lo) / (hi - lo) * H) for i, v in enumerate(vals)]
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    area = f'<path d="{d} L{W} {H} L0 {H} Z" fill="{color}" opacity=".10"/>' if fill else ''
    t = ''
    if thr is not None:
        ty = H - (thr - lo) / (hi - lo) * H
        t = f'<line x1="0" y1="{ty:.1f}" x2="{W}" y2="{ty:.1f}" stroke="{RED}" stroke-dasharray="4 4" stroke-width="1.5"/>'
    return f'<svg width="{W}" height="{H}" style="display:block; overflow:visible">{area}{t}<path class="tl-line" d="{d}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"/></svg>'
LAT = [1.62, 1.71, 1.58, 1.66, 1.93, 1.74, 1.69, 1.81, 1.77, 1.72, 1.85, 1.79, 1.74, 1.8]
UNK = [3.1, 3.4, 3.0, 3.6, 3.9, 3.5, 4.2, 4.0, 4.6, 4.4, 5.1, 4.9, 5.4, 5.8]
CONF = [2, 3, 5, 8, 11, 14, 18, 22, 27, 30]  # 신뢰도 0.5~1.0 히스토그램
def conf_hist(W=330, H=56):
    bw = W / len(CONF); m = max(CONF)
    bars = ''.join(f'<rect class="dseg" x="{i*bw+2:.1f}" y="{H - v/m*H:.1f}" width="{bw-4:.1f}" height="{v/m*H:.1f}" rx="2" fill="{"#C9C2CC" if i < 4 else "#6B6470"}"/>' for i, v in enumerate(CONF))
    x07 = 4 * bw
    return (f'<svg width="{W}" height="{H+16}" style="display:block; overflow:visible">{bars}'
            f'<line x1="{x07:.1f}" y1="-4" x2="{x07:.1f}" y2="{H}" stroke="{RED}" stroke-dasharray="4 3" stroke-width="1.5"/>'
            f'<text x="{x07+4:.1f}" y="6" font-size="11.5" fill="{RED}" font-family="Noto Sans KR, sans-serif">0.70 기준</text>'
            f'<text x="0" y="{H+14}" font-size="11.5" fill="{MUT}" font-family="Oswald, sans-serif">0.5</text>'
            f'<text x="{W}" y="{H+14}" text-anchor="end" font-size="11.5" fill="{MUT}" font-family="Oswald, sans-serif">1.0</text></svg>')
def mon_item(title, val, unit, sub, vis, col=TX):
    return (f'<div style="display:flex; flex-direction:column; gap:5px; padding:9px 0; border-top:1px solid {BD}">'
            f'<div style="display:flex; align-items:baseline; gap:8px"><p style="font-size:14px; font-weight:700; color:{TX}">{title}</p>'
            f'<p style="margin-left:auto; font-size:22px; font-weight:800; color:{col}; font-family:Oswald,sans-serif">{val}<span style="font-size:14px; color:{MUT}"> {unit}</span></p></div>'
            f'<p style="font-size:12.5px; color:{MUT}; margin-top:-6px">{sub}</p>{vis}</div>')
monitor = (
    f'<div style="display:flex; align-items:center; gap:8px">{icon("Activity", TX, 18)}<p style="font-size:17px; font-weight:800; color:{TX}">모델 모니터링</p>'
    f'<p style="margin-left:auto; display:flex; align-items:center; gap:6px; font-size:12.5px; color:#1E7F4E"><span class="live" style="width:8px; height:8px; border-radius:50%; background:#28C840; display:block"></span>정상</p></div>'
    f'<div style="display:flex; gap:8px; margin:10px 0 4px">'
    f'<div style="flex:1; background:{BG}; border-radius:9px; padding:8px 10px"><p style="font-size:12px; color:{SUB}">서빙 모델</p><p style="font-size:15px; font-weight:800; color:{TX}; font-family:Oswald,sans-serif">v1.2 · mix40k</p></div>'
    f'<div style="flex:1; background:{BG}; border-radius:9px; padding:8px 10px"><p style="font-size:12px; color:{SUB}">워커 · 큐</p><p style="font-size:15px; font-weight:800; color:{TX}; font-family:Oswald,sans-serif">3대 · 대기 2건</p></div></div>'
    + mon_item('처리 지연 (3분 통화)', '1.8', '초', 'p95 · 최근 14일', spark(LAT, 330, 46, '#5B84D6', 1.4, 2.1))
    + mon_item('신뢰도 분포', '81', '%', '0.70 이상 비율 · 오늘', conf_hist())
    + mon_item('판단 보류 비율', '5.8', '%', '14일째 상승 — 5% 넘으면 재학습 검토', spark(UNK, 330, 52, RED, 2.5, 6.5, thr=5.0), RED)
    + f'<div style="background:#FDECEB; border:1px solid #F6C9C6; border-radius:10px; padding:10px 12px; margin-top:4px">'
      f'<p style="display:flex; align-items:center; gap:6px; font-size:13px; color:{RED}; font-weight:700">{icon("Warning", RED, 15)}재학습 신호</p>'
      f'<p style="font-size:13px; color:{SUB}; line-height:1.45; margin-top:2px">보류 비율이 기준 5%를 넘었다 · 새로 들어온 목소리를 모델이 낯설어함 → 보류 구간을 모아 라벨링 후 재학습</p></div>'
)

main = (
    f'<div style="flex:1; padding:18px 22px; display:flex; flex-direction:column; gap:14px; min-width:0">'
    f'<div style="display:flex; align-items:center; gap:12px">'
    f'<div style="flex:1"><p style="font-size:13px; color:{MUT}">대시보드 › 상담센터</p>'
    f'<p style="font-size:22px; font-weight:800; color:{TX}">최근 7일 · 9/16 – 9/22</p></div>'
    f'<p style="display:flex; align-items:center; gap:6px; font-size:13.5px; color:#1E7F4E; background:#E4F5EC; border-radius:999px; padding:6px 12px"><span class="live" style="width:8px; height:8px; border-radius:50%; background:#28C840; display:block"></span>실시간 반영</p>'
    + ''.join(f'<p style="font-size:13.5px; color:{"#fff" if t=="7일" else SUB}; background:{TX if t=="7일" else CARD}; border:1px solid {TX if t=="7일" else BD}; border-radius:8px; padding:6px 12px">{t}</p>' for t in ('오늘', '7일', '30일'))
    + f'<p style="display:flex; align-items:center; gap:6px; font-size:13.5px; color:{TX}; border:1px solid {BD}; background:{CARD}; border-radius:8px; padding:6px 12px">{icon("Download", TX, 15)}CSV</p></div>'
    f'<div style="position:relative; display:flex; gap:12px">{callout(1)}'
    + stat('분석한 통화', '606건', '7일 합계 · 오늘 128건')
    + stat('위험 통화', '23건 · 3.8%', '분노·혐오 30초 이상 지속', RED)
    + stat('부정 감정 비율', '31%', '지난주 대비 +4%p')
    + stat('평균 감정 전환', '4.2회', '통화 1건당') +
    '</div>'
    f'<div style="flex:1; display:flex; gap:14px; min-height:0">'
    f'<div style="flex:1; display:flex; flex-direction:column; gap:14px; min-width:0">'
    f'<div style="display:flex; gap:14px">'
    + card(f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px"><p style="font-size:16px; font-weight:800; color:{TX}">일별 감정 분포</p><p style="font-size:12.5px; color:{MUT}">3초 구간 기준 · 위 숫자 = 통화 수</p></div>'
           + daily_svg(560, 232)
           + f'<div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:8px">' + ''.join(f'<div style="display:flex; align-items:center; gap:4px"><span style="width:10px;height:10px;border-radius:2px;background:{EMO[k][1]};display:block"></span><p style="font-size:12px; color:{SUB}">{EMO[k][0]}</p></div>' for k in ORDER) + '</div>',
           '; flex:1.15', 2)
    + card(f'<p style="font-size:16px; font-weight:800; color:{TX}">상담사별 부정 감정 통화</p><p style="font-size:12.5px; color:{MUT}; margin-bottom:12px">통화 중 부정 구간 30% 이상인 비율</p>'
           f'<div style="display:flex; flex-direction:column; gap:12px">{agent_bars()}</div>'
           f'<p style="font-size:13px; font-weight:700; color:{TX}; margin:16px 0 8px">시간대별 부정 감정</p>{hour_strip()}',
           '; flex:1', 3)
    + '</div>'
    + card(f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px"><p style="font-size:16px; font-weight:800; color:{TX}">위험 통화</p>'
           f'<p style="font-size:12.5px; color:{MUT}">누르면 그 통화의 감정 타임라인 · 위험 구간으로 바로 이동</p>'
           f'<p style="margin-left:auto; font-size:13px; color:{RED}; font-weight:700">전체 23건 ›</p></div>{risk_table()}', '; flex:1', 4)
    + '</div>'
    + f'<div style="width:380px; display:flex">' + card(monitor, '; flex:1; display:flex; flex-direction:column', 5) + '</div>'
    + '</div></div>')

legend = ''.join(
    f'<p style="display:flex; align-items:center; gap:7px; font-size:17px; color:{DECK_INK2}"><span style="width:24px;height:24px;border-radius:50%;background:{RED};color:#fff;'
    f'font-family:Oswald,sans-serif;font-size:14px;display:flex;align-items:center;justify-content:center">{n}</span>{t}</p>'
    for n, t in ((1, '핵심 지표'), (2, '일별 감정 분포'), (3, '상담사 · 시간대'), (4, '위험 통화 → 타임라인'), (5, '모델 모니터링')))

s05c = (
    f'<section id="s05c" data-transition="push" style="background:#120E14; color:{DECK_INK}; font-family:\'Noto Sans KR\', Arial, sans-serif">\n'
    f'<div style="position:absolute; left:96px; top:44px; display:flex; align-items:center; gap:22px">'
    f'<p style="font-family:Oswald,\'Arial Narrow\',sans-serif; font-size:30px; font-weight:600; color:{DECK_INK}; background:{RED}; border-radius:12px; padding:7px 20px">05</p>'
    f'<h2 style="font-family:\'Black Han Sans\',\'Noto Sans KR\',sans-serif; font-size:52px; font-weight:400; color:{DECK_INK}">대시보드 — 쌓인 결과를 한눈에</h2></div>\n'
    f'<div style="position:absolute; left:96px; top:118px; display:flex; gap:22px">{legend}</div>\n'
    + frame(96, 164, 1728, 850, 'k-voice.app/dashboard', side('대시보드') + main) +
    f'\n<p style="position:absolute; left:96px; top:1026px; font-size:17px; color:#7A6E74">화면 속 수치는 설계용 예시 데이터입니다 · 아키텍쳐 ⑨ Stats API 가 Supabase(segments · results · metrics)를 집계해 채운다</p>\n'
    '''<aside>■ 한 줄로: 통화 한 건이 아니라, 쌓인 통화 전체를 보는 관리자 화면. 아키텍쳐 상세의 ⑨번이 이 화면이야.
■ 번호 순서대로:
① 핵심 지표: 기간 동안 분석한 통화 수, 위험 통화(분노·혐오가 30초 넘게 이어진 통화) 수, 부정 감정 비율, 통화당 감정이 몇 번 바뀌었는지.
② 일별 감정 분포: 하루하루 감정 비율이 어떻게 달라졌는지. 예시에선 월요일(9/22) 분노가 늘었지.
③ 상담사별·시간대별: 어떤 상담사가 힘든 통화를 많이 받는지, 몇 시에 부정 감정이 몰리는지. 상담사 보호·인력 배치에 쓰는 정보야. (평가용이 아니라 보호용이라는 점을 꼭 말해)
④ 위험 통화 목록: 누르면 앞에서 본 감정 타임라인 화면으로 가서 위험 구간부터 재생돼. 대시보드 → 타임라인으로 이어지는 흐름.
⑤ 모델 모니터링: 모델이 잘 돌고 있는지. 처리 속도, 신뢰도 분포, 그리고 '판단 보류 비율'. 보류가 계속 늘면 요즘 들어오는 목소리를 모델이 낯설어한다는 뜻이라, 그 구간들을 모아 라벨링하고 다시 학습해. 모델이 스스로 재학습 시점을 알려주는 구조.
■ 주의: 숫자는 전부 예시야. 실제 측정값처럼 말하지 마.
■ 이렇게 말하면 돼: "통화 하나는 타임라인으로, 통화 전체는 대시보드로 봅니다. 그리고 모델 상태도 같이 보면서 재학습 시점을 잡습니다."</aside>\n</section>\n''')
open(f'{SD}/s05c.html', 'w', encoding='utf-8').write(s05c)
print('s05c', len(s05c))
