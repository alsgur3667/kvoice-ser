# -*- coding: utf-8 -*-
# 04 예시화면 상세: s04a(전체 화면 흐름) + s04b(분석 결과 화면 상세)
import math, random
SD='/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides'

# ---- 앱 UI 팔레트 (밝은 제품 화면) ----
BG='#F6F4F2'; CARD='#FFFFFF'; BD='#E7E2DE'; TX='#1E1A22'; SUB='#6B6470'; MUT='#A39CA6'
RED='#E8433F'; GOLD='#F2B63D'
EMO = {  # 감정 색 (앱 전체에서 동일)
 'angry':('분노','#E8433F'), 'sadness':('슬픔','#5B84D6'), 'neutral':('중립','#A7A1AB'),
 'happy':('기쁨','#F2B63D'), 'fear':('공포','#9B7BD6'), 'disgust':('혐오','#4FA37A'), 'surprise':('놀람','#E58BC0'),
}
DECK_INK='#F5F0EA'; DECK_INK2='#B5A9AE'

def icon(n,c,s=18): return f'<x-icon name="{n}" style="width:{s}px; height:{s}px; color:{c}"></x-icon>'

def frame(x,y,w,h,url,inner,extra=''):
    return (f'<div style="position:absolute; left:{x}px; top:{y}px; width:{w}px; height:{h}px; background:{BG}; border-radius:14px; '
            f'overflow:hidden; box-shadow:0 30px 80px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.06){extra}">'
            f'<div style="height:38px; background:#ECE8E4; border-bottom:1px solid {BD}; display:flex; align-items:center; gap:8px; padding:0 14px">'
            f'<span style="width:11px;height:11px;border-radius:50%;background:#FF5F57;display:block"></span>'
            f'<span style="width:11px;height:11px;border-radius:50%;background:#FEBC2E;display:block"></span>'
            f'<span style="width:11px;height:11px;border-radius:50%;background:#28C840;display:block"></span>'
            f'<p style="margin-left:14px; flex:1; max-width:60%; background:#FFFFFF; border:1px solid {BD}; border-radius:7px; padding:3px 12px; '
            f'font-size:13px; color:{SUB}; font-family:Oswald, sans-serif; letter-spacing:.3px">{url}</p></div>'
            f'<div style="height:{h-38}px; display:flex">{inner}</div></div>')

def callout(n, l=-13, t=-13):
    return (f'<p style="position:absolute; left:{l}px; top:{t}px; width:30px; height:30px; border-radius:50%; background:{RED}; color:#fff; '
            f'font-family:Oswald, sans-serif; font-size:17px; font-weight:600; display:flex; align-items:center; justify-content:center; '
            f'box-shadow:0 0 0 3px #fff, 0 4px 10px rgba(0,0,0,.25); z-index:3">{n}</p>')

def card(inner, extra='', n=None):
    c = callout(n) if n else ''
    return (f'<div style="position:relative; background:{CARD}; border:1px solid {BD}; border-radius:14px; padding:16px 18px{extra}">{c}{inner}</div>')

# ======================================================================
# 예시 데이터: 3분 12초 상담 통화, 3초 창 · 1.5초 간격 → 127개 구간
# ======================================================================
DUR=192
def seg(t):
    # (감정, valence, arousal, 신뢰도)
    if t<38:   return 'neutral', 0.05+0.05*math.sin(t/5), 0.30, 0.82
    if t<60:   return 'neutral',-0.12-0.004*(t-38), 0.40, 0.74
    if t<63:   return 'angry',  -0.45, 0.70, 0.58      # 전환부: 판단 보류
    if t<96:   return 'angry',  -0.72+0.06*math.sin(t/3), 0.86, 0.86
    if t<104:  return 'disgust',-0.60, 0.62, 0.71
    if t<118:  return 'angry',  -0.52, 0.66, 0.77
    if t<121:  return 'sadness',-0.48, 0.45, 0.61      # 판단 보류
    if t<150:  return 'sadness',-0.46+0.05*math.sin(t/4), 0.28, 0.83
    if t<170:  return 'neutral',-0.08+0.004*(t-150), 0.33, 0.80
    return 'happy', 0.30+0.01*(t-170), 0.50, 0.79
wins=[(i*1.5, seg(i*1.5+1.5)) for i in range(int((DUR-3)/1.5)+1)]

def tlabel(s): return f'{int(s//60)}:{int(s%60):02d}'

# ----------------------------------------------------------------------
# 감정 흐름 그래프 (s04b 메인)
# ----------------------------------------------------------------------
def timeline_svg(W, H, sel=(69,72), compact=False):
    L, R, T = (44, 10, 14)
    band_h = 26 if not compact else 14
    PH = H - T - band_h - 30           # 곡선 영역 높이
    X = lambda s: L + (W-L-R)*s/DUR
    Y = lambda v: T + PH*(1-(v+1)/2)
    out=[f'<svg viewBox="0 0 {W} {H}" style="width:100%; height:{H}px; display:block">']
    # 위험 구간 (분노 지속) 배경
    out.append(f'<rect x="{X(60)}" y="{T}" width="{X(118)-X(60)}" height="{PH}" fill="{RED}" opacity=".07"/>')
    # 격자
    for v,lab in ((1,'긍정'),(0,'0'),(-1,'부정')):
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(v)}" y2="{Y(v)}" stroke="{BD}" stroke-width="1"/>')
        if not compact: out.append(f'<text x="{L-8}" y="{Y(v)+4}" text-anchor="end" font-size="12" fill="{MUT}">{lab}</text>')
    # 긍부정 곡선 + 면
    pts=[(X(s+1.5), Y(e[1])) for s,e in wins]
    d='M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)
    area=d+f' L{pts[-1][0]:.1f} {Y(0):.1f} L{pts[0][0]:.1f} {Y(0):.1f} Z'
    out.append(f'<defs><linearGradient id="vg{W}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD}" stop-opacity=".35"/>'
               f'<stop offset=".5" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="{RED}" stop-opacity=".30"/></linearGradient></defs>')
    out.append(f'<path d="{area}" fill="url(#vg{W})"/>')
    out.append(f'<path class="tl-line" d="{d}" fill="none" stroke="{TX}" stroke-width="2.2" stroke-linejoin="round"/>')
    # 감정 띠 (구간별 대표 감정)
    by=T+PH+8
    bw=(W-L-R)*1.5/DUR
    for s,e in wins:
        c=EMO[e[0]][1]
        if e[3] < 0.70:   # 판단 보류: 빗금
            out.append(f'<rect x="{X(s):.1f}" y="{by}" width="{bw+.6:.1f}" height="{band_h}" fill="#D9D4D0"/>')
            out.append(f'<rect x="{X(s):.1f}" y="{by}" width="{bw+.6:.1f}" height="{band_h}" fill="url(#hatch)"/>')
        else:
            out.append(f'<rect x="{X(s):.1f}" y="{by}" width="{bw+.6:.1f}" height="{band_h}" fill="{c}"/>')
    out.insert(1, '<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                  f'<line x1="0" y1="0" x2="0" y2="6" stroke="#9A939D" stroke-width="2"/></pattern></defs>')
    # 시간축
    for s in range(0, DUR+1, 30):
        out.append(f'<text x="{X(s)}" y="{by+band_h+18}" text-anchor="middle" font-size="12" fill="{MUT}" font-family="Oswald, sans-serif">{tlabel(s)}</text>')
    if not compact:
        # 급변 지점 마커
        for s,lab,c in ((62,'분노 급상승',RED),(120,'슬픔으로 전환','#5B84D6'),(170,'진정·해결',GOLD)):
            out.append(f'<line x1="{X(s)}" x2="{X(s)}" y1="{T}" y2="{by+band_h}" stroke="{c}" stroke-width="1.5" stroke-dasharray="4 3"/>')
            out.append(f'<rect x="{X(s)+4}" y="{T+2}" width="{len(lab)*13+30}" height="22" rx="11" fill="{c}"/>')
            out.append(f'<text x="{X(s)+14}" y="{T+17}" font-size="12.5" font-weight="700" fill="#fff">⚑ {lab}</text>')
        # 선택 구간 + 재생 헤드
        out.append(f'<rect x="{X(sel[0])}" y="{T}" width="{X(sel[1])-X(sel[0])}" height="{by+band_h-T}" fill="{TX}" opacity=".10"/>')
        out.append(f'<line x1="{X(sel[0])}" x2="{X(sel[0])}" y1="{T-4}" y2="{by+band_h+4}" stroke="{TX}" stroke-width="2"/>')
        out.append(f'<circle cx="{X(sel[0])}" cy="{T-4}" r="5" fill="{TX}"/>')
    out.append('</svg>')
    return ''.join(out)

def wave_svg(W,H,play_s=69,fixed=False):
    random.seed(3)
    wcss = f'{W}px' if fixed else '100%'
    n=min(160, W//4); out=[f'<svg viewBox="0 0 {W} {H}" style="width:{wcss}; height:{H}px; display:block">']
    bw=W/n
    for i in range(n):
        s=DUR*i/n; a=seg(s+.1)[2]
        h=max(3,(0.25+a*0.75)*H*(0.35+0.65*random.random()))
        c = TX if s<=play_s else '#CFC9CD'
        out.append(f'<rect x="{i*bw+bw*.2:.1f}" y="{(H-h)/2:.1f}" width="{bw*.6:.1f}" height="{h:.1f}" rx="1.5" fill="{c}"/>')
    out.append('</svg>'); return ''.join(out)

# ======================================================================
# s04b — 분석 결과 화면 상세
# ======================================================================
def side(active='내 녹취'):
    items=[('Plus','새 분석'),('List','내 녹취'),('Grid','대시보드'),('Settings','설정')]
    rows=''.join(
        f'<div style="display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:9px; '
        f'{"background:#FDECEB; color:"+RED+"; font-weight:700" if t==active else "color:"+SUB}">{icon(ic, RED if t==active else SUB, 18)}'
        f'<p style="font-size:15px">{t}</p></div>' for ic,t in items)
    return (f'<div style="width:196px; background:{CARD}; border-right:1px solid {BD}; padding:18px 12px; display:flex; flex-direction:column; gap:4px">'
            f'<div style="display:flex; align-items:center; gap:8px; padding:0 8px 16px">'
            f'<p style="width:28px;height:28px;border-radius:8px;background:{RED};color:#fff;display:flex;align-items:center;justify-content:center;'
            f'font-family:Oswald,sans-serif;font-weight:600;font-size:15px">K</p>'
            f'<p style="font-family:\'Black Han Sans\',sans-serif; font-size:17px; color:{TX}; white-space:nowrap">보이스 코리안</p></div>{rows}'
            f'<div style="margin-top:auto; padding:12px; background:{BG}; border-radius:10px">'
            f'<p style="font-size:12.5px; color:{SUB}">적용 현장</p><p style="font-size:15px; font-weight:700; color:{TX}">상담센터</p>'
            f'<p style="font-size:12px; color:{MUT}; margin-top:4px">매핑 규칙 v1 · 임계값 0.70</p></div></div>')

def stat(lbl, val, sub, col=TX):
    return (f'<div style="flex:1; background:{CARD}; border:1px solid {BD}; border-radius:12px; padding:12px 16px">'
            f'<p style="font-size:13px; color:{SUB}">{lbl}</p>'
            f'<p style="font-size:24px; font-weight:800; color:{col}; line-height:1.3; white-space:nowrap">{val}</p>'
            f'<p style="font-size:12.5px; color:{MUT}">{sub}</p></div>')

def probbars():
    P=[('angry',.71),('disgust',.11),('sadness',.08),('neutral',.05),('fear',.03),('surprise',.01),('happy',.01)]
    return ''.join(
        f'<div style="display:flex; align-items:center; gap:10px"><p style="width:34px; font-size:13.5px; color:{SUB}">{EMO[k][0]}</p>'
        f'<div style="flex:1; height:12px; background:#F0ECE9; border-radius:6px"><div class="pbar" style="width:{max(v*100,1.5):.1f}%; height:12px; border-radius:6px; background:{EMO[k][1]}"></div></div>'
        f'<p style="width:38px; text-align:right; font-size:13.5px; font-weight:700; color:{TX}; font-family:Oswald,sans-serif">{int(v*100)}%</p></div>' for k,v in P)

def legend_row():
    return ''.join(f'<div style="display:flex; align-items:center; gap:5px"><span style="width:12px;height:12px;border-radius:3px;background:{c};display:block"></span>'
                   f'<p style="font-size:12.5px; color:{SUB}">{n}</p></div>' for n,c in EMO.values()) + \
           (f'<div style="display:flex; align-items:center; gap:5px"><span style="width:12px;height:12px;border-radius:3px;display:block;'
            f'background:repeating-linear-gradient(45deg,#D9D4D0 0 3px,#9A939D 3px 5px)"></span><p style="font-size:12.5px; color:{SUB}">판단 보류</p></div>')

main_b = (
 f'<div style="flex:1; padding:18px 22px; display:flex; flex-direction:column; gap:14px; min-width:0">'
 # 헤더
 f'<div style="display:flex; align-items:center; gap:14px">'
 f'<div style="flex:1"><p style="font-size:13px; color:{MUT}">내 녹취 › 상담 통화</p>'
 f'<p style="font-size:22px; font-weight:800; color:{TX}">고객 상담 #0921-003 · 2026-09-21 14:03 · 3분 12초</p></div>'
 f'<p style="display:flex; align-items:center; gap:6px; font-size:14px; color:#1E7F4E; background:#E4F5EC; border-radius:999px; padding:6px 12px">{icon("CheckCircle","#1E7F4E",16)}분석 완료</p>'
 f'<p style="display:flex; align-items:center; gap:6px; font-size:14px; color:{TX}; border:1px solid {BD}; background:{CARD}; border-radius:9px; padding:7px 12px">{icon("Download",TX,16)}리포트</p>'
 f'<p style="display:flex; align-items:center; gap:6px; font-size:14px; color:#fff; background:{TX}; border-radius:9px; padding:7px 12px">{icon("Share","#fff",16)}공유</p></div>'
 # 요약 카드
 f'<div style="position:relative; display:flex; gap:12px">{callout(1)}'
 + stat('감정 흐름','중립 → 분노 → 슬픔 → 진정','대표 감정이 바뀐 순서')
 + stat('감정 전환','5회','1분당 1.6회')
 + stat('위험 구간','1곳 · 56초','1:00 – 1:56 · 분노 지속', RED)
 + stat('판단 보류','3%','신뢰도 0.70 미만 구간') +
 '</div>'
 # 본문: 타임라인 + 상세
 f'<div style="flex:1; display:flex; gap:14px; min-height:0">'
 # 타임라인 카드
 f'<div style="flex:1; display:flex; flex-direction:column; gap:10px; min-width:0">'
 + card(
     f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:6px"><p style="font-size:17px; font-weight:800; color:{TX}">감정 흐름</p>'
     f'<p style="font-size:13px; color:{MUT}">선: 긍정 ↔ 부정 · 띠: 3초마다 대표 감정</p>'
     f'<div style="margin-left:auto; display:flex; gap:6px">'
     f'<p style="font-size:13px; color:#fff; background:{TX}; border-radius:7px; padding:4px 10px">긍부정</p>'
     f'<p style="font-size:13px; color:{SUB}; border:1px solid {BD}; border-radius:7px; padding:4px 10px">각성도</p>'
     f'<p style="font-size:13px; color:{SUB}; border:1px solid {BD}; border-radius:7px; padding:4px 10px">7감정</p></div></div>'
     + f'<div style="position:relative">{callout(3, 318, 34)}' + timeline_svg(1000, 390) + '</div>'
     + f'<div style="display:flex; flex-wrap:wrap; gap:12px; margin-top:6px">{legend_row()}</div>',
   '; flex:1', 2)
 + card(
     f'<div style="display:flex; align-items:center; gap:14px">'
     f'<p style="width:44px;height:44px;border-radius:50%;background:{RED};display:flex;align-items:center;justify-content:center">{icon("Pause","#fff",20)}</p>'
     f'<p style="font-family:Oswald,sans-serif; font-size:16px; color:{TX}; white-space:nowrap">1:09 <span style="color:{MUT}">/ 3:12</span></p>'
     f'<div style="flex:1">{wave_svg(700,46)}</div>'
     f'<p style="font-size:13px; color:{SUB}; border:1px solid {BD}; border-radius:7px; padding:4px 10px; white-space:nowrap">1.0×</p>'
     f'<p style="display:flex; align-items:center; gap:5px; font-size:13px; color:{RED}; font-weight:700; white-space:nowrap">{icon("Skip",RED,15)}다음 급변 구간</p></div>',
   '; padding:12px 18px', 4)
 + '</div>'
 # 상세 패널
 + f'<div style="width:390px; display:flex">'
 + card(
     f'<p style="font-size:13px; color:{MUT}">선택 구간</p>'
     f'<p style="font-size:21px; font-weight:800; color:{TX}; font-family:Oswald,\'Noto Sans KR\',sans-serif">1:09 – 1:12</p>'
     f'<div style="display:flex; align-items:center; gap:10px; margin:10px 0 12px">'
     f'<p style="font-size:30px; font-weight:800; color:{RED}">분노</p>'
     f'<p style="font-size:14px; color:{SUB}">신뢰도 <b style="color:{TX}; font-family:Oswald,sans-serif; font-size:17px">0.86</b></p></div>'
     f'<div style="display:flex; flex-direction:column; gap:8px">{probbars()}</div>'
     f'<div style="display:flex; gap:10px; margin:14px 0">'
     f'<div style="flex:1; background:{BG}; border-radius:10px; padding:10px 12px"><p style="font-size:12.5px; color:{SUB}">긍부정</p>'
     f'<p style="font-size:20px; font-weight:800; color:{RED}; font-family:Oswald,sans-serif">−0.72</p></div>'
     f'<div style="flex:1; background:{BG}; border-radius:10px; padding:10px 12px"><p style="font-size:12.5px; color:{SUB}">각성도</p>'
     f'<p style="font-size:20px; font-weight:800; color:{TX}; font-family:Oswald,sans-serif">0.84</p></div></div>'
     f'<div style="background:#FDECEB; border:1px solid #F6C9C6; border-radius:10px; padding:12px 14px">'
     f'<p style="display:flex; align-items:center; gap:6px; font-size:13px; color:{RED}; font-weight:700">{icon("Warning",RED,15)}상담센터 해석</p>'
     f'<p style="font-size:16px; font-weight:800; color:{TX}; margin-top:3px">에스컬레이션 권장</p>'
     f'<p style="font-size:13px; color:{SUB}; line-height:1.45; margin-top:2px">분노가 33초 이상 이어짐 · 상급자 연결 기준 충족</p></div>'
     f'<div style="display:flex; gap:8px; margin-top:auto; padding-top:12px">'
     f'<p style="flex:1; display:flex; align-items:center; justify-content:center; gap:6px; font-size:14px; font-weight:700; color:#fff; background:{RED}; border-radius:9px; padding:9px">{icon("Play","#fff",14)}이 구간 재생</p>'
     f'<p style="display:flex; align-items:center; justify-content:center; gap:6px; font-size:14px; color:{TX}; border:1px solid {BD}; border-radius:9px; padding:9px 12px">{icon("Flag",TX,14)}메모</p></div>',
   '; flex:1; display:flex; flex-direction:column', 5)
 + '</div></div></div>')

legend_b = ''.join(
  f'<p style="display:flex; align-items:center; gap:7px; font-size:17px; color:{DECK_INK2}"><span style="width:24px;height:24px;border-radius:50%;background:{RED};color:#fff;'
  f'font-family:Oswald,sans-serif;font-size:14px;display:flex;align-items:center;justify-content:center">{n}</span>{t}</p>'
  for n,t in ((1,'한 줄 요약'),(2,'감정 흐름 그래프'),(3,'급변 지점 자동 표시'),(4,'파형 · 재생'),(5,'구간 상세 · 현장 해석')))

s04b = (
 f'<section id="s04b" data-transition="push" style="background:#120E14; color:{DECK_INK}; font-family:\'Noto Sans KR\', Arial, sans-serif">\n'
 f'<div style="position:absolute; left:96px; top:44px; display:flex; align-items:center; gap:22px">'
 f'<p style="font-family:Oswald,\'Arial Narrow\',sans-serif; font-size:30px; font-weight:600; color:{DECK_INK}; background:{RED}; border-radius:12px; padding:7px 20px">04</p>'
 f'<h2 style="font-family:\'Black Han Sans\',\'Noto Sans KR\',sans-serif; font-size:52px; font-weight:400; color:{DECK_INK}">예시화면 상세 — 분석 결과</h2></div>\n'
 f'<div style="position:absolute; left:96px; top:118px; display:flex; gap:22px">{legend_b}</div>\n'
 + frame(96, 164, 1728, 850, 'k-voice.app/calls/0921-003', side() + main_b) +
 f'\n<p style="position:absolute; left:96px; top:1026px; font-size:17px; color:#7A6E74">화면 속 통화·수치는 설계용 예시 데이터입니다 · 실제 서비스에서는 워커가 3초 창 · 1.5초 간격으로 계산한 값이 그대로 채워진다</p>\n'
 '''<aside>■ 한 줄로: 분석이 끝나면 사용자가 실제로 보게 될 메인 화면. 번호 순서대로 설명하면 돼.
■ 쉽게 풀면:
① 맨 위 요약 카드: 3분 통화를 한 줄로 요약. "중립 → 분노 → 슬픔 → 진정" 흐름, 감정이 몇 번 바뀌었는지, 위험 구간이 어디인지, 모델이 확신 못 한 구간이 얼마나 되는지.
② 감정 흐름 그래프: 가운데 선은 기분이 좋은 쪽(위)이냐 나쁜 쪽(아래)이냐. 그 밑의 색 띠는 3초마다 제일 강한 감정. 빗금 친 회색은 '판단 보류' — 확신이 70% 안 돼서 억지로 답하지 않은 구간이야.
③ 깃발 표시: 감정이 확 바뀐 지점을 자동으로 찍어줘. 사용자가 3분을 다 들을 필요 없이 여기만 누르면 돼. 이게 우리 서비스의 핵심.
④ 파형 · 재생: 음성을 그대로 들을 수 있고, "다음 급변 구간" 버튼으로 튄 곳만 건너뛰며 들을 수 있어.
⑤ 구간 상세: 선택한 3초 구간의 7감정 확률, 긍부정·각성도, 신뢰도. 그리고 적용 현장(여기선 상담센터) 규칙으로 해석한 결과 — "에스컬레이션 권장".
■ 포인트: 같은 화면에서 왼쪽 아래 '적용 현장'만 교육·돌봄으로 바꾸면 ⑤의 해석 문구만 바뀌어. 모델은 그대로. 이게 범용성 장에서 말한 "엔진은 하나, 해석은 현장마다"가 화면에서 보이는 모습이야.
■ 주의: 화면 속 숫자는 예시야. 실제 측정값처럼 말하지 마. 각주에도 써놨어.
■ 이렇게 말하면 돼: "3분 통화를 다 들을 필요 없이, 깃발 찍힌 곳만 누르면 그 순간의 감정과 해석이 바로 나옵니다."</aside>\n</section>\n''')

# ======================================================================
# s04a — 전체 화면 흐름 (4개 화면)
# ======================================================================
FW, FH = 392, 620
def mini_side():
    return (f'<div style="width:46px; background:{CARD}; border-right:1px solid {BD}; display:flex; flex-direction:column; align-items:center; gap:14px; padding-top:14px">'
            f'<p style="width:24px;height:24px;border-radius:7px;background:{RED};color:#fff;display:flex;align-items:center;justify-content:center;font-family:Oswald,sans-serif;font-size:13px;font-weight:600">K</p>'
            + ''.join(icon(n,MUT,16) for n in ('Plus','List','Grid','Settings')) + '</div>')

def mbody(inner): return f'<div style="flex:1; padding:14px; display:flex; flex-direction:column; gap:10px; min-width:0">{inner}</div>'
def mt(t, s=''): return f'<p style="font-size:16px; font-weight:800; color:{TX}">{t}</p>' + (f'<p style="font-size:12px; color:{MUT}; margin-top:-8px">{s}</p>' if s else '')

# 1) 새 분석
scr1 = mini_side() + mbody(
  mt('새 분석','녹취를 올리거나 바로 녹음') +
  f'<div style="border:2px dashed #D6CFCB; border-radius:12px; background:{CARD}; padding:22px 10px; display:flex; flex-direction:column; align-items:center; gap:6px">'
  f'{icon("Upload",RED,28)}<p style="font-size:13.5px; font-weight:700; color:{TX}">파일을 끌어다 놓기</p><p style="font-size:11.5px; color:{MUT}">wav · mp3 · m4a · 최대 30분</p></div>'
  f'<div style="display:flex; align-items:center; gap:8px; background:{CARD}; border:1px solid {BD}; border-radius:10px; padding:10px 12px">'
  f'<p style="width:30px;height:30px;border-radius:50%;background:#FDECEB;display:flex;align-items:center;justify-content:center">{icon("Mic",RED,16)}</p>'
  f'<p style="font-size:13px; color:{TX}; font-weight:700">마이크로 녹음</p><p style="margin-left:auto; font-size:11.5px; color:{MUT}">00:00</p></div>'
  f'<p style="font-size:12px; color:{SUB}; margin-top:2px">적용 현장</p>'
  f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:6px">'
  + ''.join(f'<p style="font-size:12.5px; text-align:center; border-radius:8px; padding:7px 4px; {("background:"+TX+"; color:#fff; font-weight:700") if i==0 else ("border:1px solid "+BD+"; color:"+SUB+"; background:"+CARD)}">{t}</p>'
            for i,t in enumerate(('상담센터','교육','헬스케어·돌봄','AI 에이전트'))) +
  '</div>'
  f'<label style="display:flex; align-items:center; gap:6px; font-size:11.5px; color:{SUB}"><span style="width:13px;height:13px;border-radius:3px;background:{TX};display:block"></span>녹음 당사자 동의를 받았습니다</label>'
  f'<p style="margin-top:auto; text-align:center; font-size:14px; font-weight:800; color:#fff; background:{RED}; border-radius:10px; padding:11px">분석하기</p>')

# 2) 분석 중
steps=[('업로드',1),('전처리 · 16kHz 변환',1),('감정 분석 · 79 / 127 구간',2),('타임라인 · 급변 지점 계산',0)]
def stp(t,st):
    ic = icon('CheckCircle','#1E7F4E',16) if st==1 else (f'<span style="width:14px;height:14px;border-radius:50%;border:2.5px solid {RED};border-right-color:transparent;display:block"></span>' if st==2 else f'<span style="width:14px;height:14px;border-radius:50%;border:2px solid #D6CFCB;display:block"></span>')
    col = TX if st else MUT
    return f'<div style="display:flex; align-items:center; gap:9px">{ic}<p style="font-size:12.5px; color:{col}; {"font-weight:700" if st==2 else ""}">{t}</p></div>'
scr2 = mini_side() + mbody(
  mt('분석 중','페이지를 닫아도 계속 진행돼요') +
  f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:12px; padding:14px">'
  f'<div style="display:flex; align-items:baseline; gap:6px"><p style="font-family:Oswald,sans-serif; font-size:34px; font-weight:600; color:{TX}">62%</p><p style="font-size:12px; color:{MUT}">약 20초 남음</p></div>'
  f'<div style="height:9px; background:#F0ECE9; border-radius:5px; margin:8px 0 14px"><div class="pbar" style="width:62%; height:9px; background:{RED}; border-radius:5px"></div></div>'
  f'<div style="display:flex; flex-direction:column; gap:9px">{"".join(stp(t,s) for t,s in steps)}</div></div>'
  f'<p style="font-size:12px; color:{SUB}">지금까지 나온 흐름</p>'
  f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:12px; padding:8px 8px 0; overflow:hidden; position:relative">'
  + timeline_svg(340, 120, compact=True) +
  f'<div style="position:absolute; left:62%; top:0; bottom:0; right:0; background:linear-gradient(90deg, rgba(255,255,255,.4), #fff 30%)"></div></div>'
  f'<p style="display:flex; align-items:center; gap:6px; font-size:11.5px; color:#1E7F4E; background:#E4F5EC; border-radius:8px; padding:7px 10px">{icon("Bell","#1E7F4E",14)}Realtime 연결됨 · 새로고침 없이 갱신</p>')

# 3) 결과 (요약)
scr3 = mini_side() + mbody(
  mt('분석 결과','고객 상담 #0921-003 · 3분 12초') +
  f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:6px">'
  + ''.join(f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:9px; padding:7px 9px"><p style="font-size:11px; color:{MUT}">{a}</p><p style="font-size:14.5px; font-weight:800; color:{c}">{b}</p></div>'
            for a,b,c in (('감정 전환','5회',TX),('위험 구간','1곳',RED),('대표 감정','분노 → 슬픔',TX),('판단 보류','3%',TX))) +
  '</div>'
  f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:12px; padding:8px 8px 0">' + timeline_svg(340, 150, compact=True) + '</div>'
  f'<div style="display:flex; align-items:center; gap:8px; background:{CARD}; border:1px solid {BD}; border-radius:10px; padding:8px 10px">'
  f'<p style="width:26px;height:26px;border-radius:50%;background:{RED};display:flex;align-items:center;justify-content:center">{icon("Play","#fff",12)}</p>'
  f'<div style="flex:1; min-width:0; overflow:hidden">{wave_svg(250,26,fixed=True)}</div></div>'
  f'<div style="background:#FDECEB; border-radius:10px; padding:9px 11px"><p style="font-size:11.5px; color:{RED}; font-weight:700">1:00 – 1:56 · 에스컬레이션 권장</p>'
  f'<p style="font-size:11px; color:{SUB}">분노 지속 · 상급자 연결 기준 충족</p></div>'
  f'<p style="margin-top:auto; text-align:center; font-size:12.5px; color:{TX}; border:1px solid {BD}; border-radius:9px; padding:8px; background:{CARD}">상세 화면에서 구간별로 보기 →</p>')

# 4) 대시보드
rows=[('상담 #0921-003','3:12',1,RED,'분노→슬픔'),('상담 #0921-002','5:40',0,'#1E7F4E','중립 유지'),('상담 #0921-001','2:08',2,RED,'분노 반복'),
      ('상담 #0920-014','4:21',0,'#1E7F4E','기쁨 마무리'),('상담 #0920-013','6:02',1,GOLD,'공포→중립')]
def spark(seedv):
    random.seed(seedv); pts=[]; v=0
    for i in range(18): v=max(-1,min(1,v+random.uniform(-.35,.35))); pts.append(v)
    d='M'+' L'.join(f'{i*4.2:.1f} {10-8*p:.1f}' for i,p in enumerate(pts))
    return f'<svg viewBox="0 0 72 20" style="width:72px;height:20px"><path d="{d}" fill="none" stroke="{SUB}" stroke-width="1.4"/></svg>'
scr4 = mini_side() + mbody(
  mt('대시보드','이번 주 · 상담센터') +
  f'<div style="display:flex; gap:6px">'
  + ''.join(f'<div style="flex:1; background:{CARD}; border:1px solid {BD}; border-radius:9px; padding:7px 9px"><p style="font-size:11px; color:{MUT}">{a}</p>'
            f'<p style="font-size:17px; font-weight:800; color:{c}; font-family:Oswald,\'Noto Sans KR\',sans-serif">{b}</p></div>'
            for a,b,c in (('분석한 통화','128',TX),('위험 구간','23',RED),('평균 전환','3.4회',TX))) +
  '</div>'
  f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:10px; padding:9px 10px">'
  f'<p style="font-size:11.5px; color:{SUB}; margin-bottom:6px">요일별 위험 구간</p><div style="display:flex; align-items:end; gap:7px; height:46px">'
  + ''.join(f'<div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:2px"><div class="dbar" style="width:100%; height:{h}px; background:{RED if h>34 else "#E5C9C7"}; border-radius:3px"></div>'
            f'<p style="font-size:10px; color:{MUT}">{d}</p></div>' for d,h in (('월',18),('화',26),('수',40),('목',22),('금',30))) +
  '</div></div>'
  f'<div style="display:flex; align-items:center; gap:6px; background:{CARD}; border:1px solid {BD}; border-radius:8px; padding:6px 9px">{icon("Search",MUT,14)}<p style="font-size:11.5px; color:{MUT}">통화 검색 · 위험 구간만 보기</p></div>'
  f'<div style="background:{CARD}; border:1px solid {BD}; border-radius:10px; overflow:hidden">'
  + ''.join(f'<div style="display:flex; align-items:center; gap:7px; padding:7px 9px; {"border-top:1px solid "+BD if i else ""}">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{c};display:block"></span>'
            f'<div style="flex:1; min-width:0"><p style="font-size:12px; font-weight:700; color:{TX}; white-space:nowrap">{n}</p><p style="font-size:10.5px; color:{MUT}">{d} · {flow}</p></div>'
            f'{spark(i+7)}<p style="font-size:11px; font-weight:700; color:{RED if k else MUT}; width:22px; text-align:right">{k if k else "–"}</p></div>'
            for i,(n,d,k,c,flow) in enumerate(rows)) +
  '</div>')

def step_card(n, x, title, desc, scr, url):
    return (frame(x, 250, FW, FH, url, scr) +
            f'<div style="position:absolute; left:{x}px; top:{250+FH+22}px; width:{FW}px; display:flex; gap:12px; align-items:flex-start">'
            f'<p style="width:34px;height:34px;flex:none;border-radius:50%;background:{RED};color:#fff;font-family:Oswald,sans-serif;font-size:19px;font-weight:600;'
            f'display:flex;align-items:center;justify-content:center">{n}</p>'
            f'<div><p style="font-size:24px; font-weight:700; color:{DECK_INK}">{title}</p>'
            f'<p style="font-size:18px; font-weight:300; color:{DECK_INK2}; line-height:1.45; margin-top:2px">{desc}</p></div></div>')

GAP=(1728-4*FW)/3
xs=[96+i*(FW+GAP) for i in range(4)]
arrows=''.join(f'<x-shape kind="arrow-right" style="position:absolute; left:{xs[i]+FW+(GAP-30)/2:.0f}px; top:{250+FH/2-8}px; width:30px; height:16px; background:#6C5F70"></x-shape>' for i in range(3))

s04a = (
 f'<section id="s04a" data-transition="push" style="background:#120E14; color:{DECK_INK}; font-family:\'Noto Sans KR\', Arial, sans-serif">\n'
 f'<div style="position:absolute; left:96px; top:64px; display:flex; align-items:center; gap:24px">'
 f'<p style="font-family:Oswald,\'Arial Narrow\',sans-serif; font-size:32px; font-weight:600; color:{DECK_INK}; background:{RED}; border-radius:12px; padding:8px 22px">04</p>'
 f'<h2 style="font-family:\'Black Han Sans\',\'Noto Sans KR\',sans-serif; font-size:58px; font-weight:400; color:{DECK_INK}">예시화면 — 전체 흐름</h2></div>\n'
 f'<p style="position:absolute; left:98px; top:160px; font-size:24px; font-weight:300; color:{DECK_INK2}">올리고 → 기다리고 → 확인하고 → 모아본다. 사용자가 거치는 화면은 이 네 개가 전부다.</p>\n'
 + step_card(1, xs[0], '새 분석', '파일을 올리거나 녹음하고, 현장을 고른다', scr1, 'k-voice.app/new')
 + step_card(2, xs[1], '분석 중', '진행률과 중간 결과가 실시간으로 채워진다', scr2, 'k-voice.app/jobs/0921-003')
 + step_card(3, xs[2], '분석 결과', '한 줄 요약과 위험 구간 · 상세는 다음 장', scr3, 'k-voice.app/calls/0921-003')
 + step_card(4, xs[3], '대시보드', '쌓인 통화의 위험 구간과 추이를 본다', scr4, 'k-voice.app/dashboard')
 + arrows +
 f'\n<p style="position:absolute; left:96px; top:1026px; font-size:17px; color:#7A6E74">화면 속 통화·수치는 설계용 예시 데이터입니다 · 아키텍쳐 상세(①~⑧)의 흐름이 화면에서 이렇게 보인다</p>\n'
 '''<aside>■ 한 줄로: 사용자가 처음 들어와서 결과를 모아보기까지 거치는 화면 네 개.
■ 쉽게 풀면:
1) 새 분석: 녹취 파일을 끌어다 놓거나 마이크로 바로 녹음. 적용 현장(상담센터·교육·돌봄·AI 에이전트)을 고르고 "분석하기". 녹음 동의 체크박스도 넣었어 — 개인정보 질문 나오면 이걸 가리키면 돼.
2) 분석 중: 업로드하자마자 바로 이 화면으로 넘어가. 뒤에서 워커가 분석하는 동안 진행률이랑 지금까지 나온 흐름이 실시간으로 채워져(아키텍쳐 상세의 ⑦ Realtime). 페이지 닫아도 분석은 계속돼.
3) 분석 결과: 요약 카드 네 개 + 전체 흐름 그래프 + 위험 구간 알림. 여기서 누르면 다음 장의 상세 화면으로 가.
4) 대시보드: 이번 주에 분석한 통화들을 모아서, 위험 구간이 많은 요일이나 통화를 한눈에 봐. 관리자용.
■ 연결: 이 화면 네 개가 아키텍쳐 상세 장의 ①~⑧ 흐름이랑 그대로 맞물려. 1번 화면 = ① 업로드, 2번 화면 = ④~⑦, 3·4번 = ⑧ 조회.
■ 주의: 화면 속 숫자는 예시야.
■ 이렇게 말하면 돼: "올리고, 기다리고, 확인하고, 모아봅니다. 사용자가 보는 화면은 이 네 개가 전부입니다."</aside>\n</section>\n''')

open(f'{SD}/s04a.html','w',encoding='utf-8').write(s04a)
open(f'{SD}/s04b.html','w',encoding='utf-8').write(s04b)
print('written', len(s04a), len(s04b), 'windows', len(wins))
