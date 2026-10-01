# -*- coding: utf-8 -*-
"""발표본용 새 슬라이드: toc(재구성) · demo(시연 브리지) · built(구현 현황) · growth(한계와 성장) · close"""
SD = '/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides'

INK='#120E14'; INK2='#1C1620'; BD='#362C38'; TX='#F5F0EA'; SUB='#B5A9AE'; MUT='#8E8188'
RED='#E8433F'; GOLD='#F2B63D'; GREEN='#6FD08C'; BLUE='#9BB7E8'; DEEP='#2A2130'
F = "font-family:'Noto Sans KR', Arial, sans-serif"
BH = "font-family:'Black Han Sans', 'Noto Sans KR', sans-serif"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"

def sec(sid, bg, color, inner, notes, trans="push", extra=""):
    return (f'<section id="{sid}" data-transition="{trans}" style="background:{bg}; color:{color}; {F}; '
            f'padding:128px 128px 160px; display:flex; flex-direction:column; gap:34px{extra}">'
            f'{inner}<aside>{notes}</aside></section>')

def head(num, title, color=TX):
    return (f'<div style="display:flex; align-items:center; gap:28px">'
            f'<p style="{OS}; font-size:34px; font-weight:600; color:#F5F0EA; background:{RED}; '
            f'border-radius:12px; padding:10px 24px">{num}</p>'
            f'<h2 style="{BH}; font-size:72px; font-weight:400; line-height:1.15; color:{color}">{title}</h2></div>')

def eyebrow(t, c=GOLD):
    return f'<p style="{OS}; font-size:26px; font-weight:600; letter-spacing:6px; text-transform:uppercase; color:{c}">{t}</p>'

def card(title, body, bg=INK, bd=BD, tc=TX, bc=SUB, extra=""):
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:10px; background:{bg}; '
            f'border:1px solid {bd}; border-radius:16px; padding:26px{extra}">'
            f'<h3 style="font-size:29px; font-weight:700; line-height:1.25; color:{tc}">{title}</h3>'
            f'<p style="font-size:25px; font-weight:400; line-height:1.5; color:{bc}">{body}</p></div>')

def stat(label, value, sub, vc=TX):
    return (f'<div style="flex:1; background:{INK}; border:1px solid {BD}; border-radius:16px; padding:24px 28px">'
            f'<p style="font-size:24px; color:{MUT}">{label}</p>'
            f'<p style="{OS}; font-size:54px; font-weight:600; line-height:1.15; color:{vc}">{value}</p>'
            f'<p style="font-size:22px; line-height:1.35; color:{SUB}">{sub}</p></div>')

def foot(t, c='#7A6E74'):
    return f'<p style="position:absolute; left:128px; bottom:64px; width:1664px; font-size:24px; color:{c}">{t}</p>'

def arrow(w=48, h=24, c=RED):
    return f'<x-shape kind="arrow-right" style="width:{w}px; height:{h}px; background:{c}; align-self:center"></x-shape>'

# ══════════════════════════════════════════════════════════════════
# 1. 목차 — 시연을 축으로 다시 짠다
# ══════════════════════════════════════════════════════════════════
ROWS = [
    ("01", "problem", "주제선정이유", "갈등은 어떻게 시작되나 · 왜 만들었나 · 왜 음성인가 · 감정별 음성 듣기", "p.3–6", False),
    ("02", "s01", "데이터 수집과 EDA", "왜 이 데이터인가 · 구성 · 수집 여정 · EDA 3장 · 전처리 · 불균형", "p.7–17", False),
    ("03", "wave", "모델 학습과 개선", "왜 파형인가 · 모델 6개 비교 · <b style=\"color:" + GOLD + "\">텐서보드로 찾은 문제</b> · 외부 검증", "p.18–26", False),
    ("04", "s05b", "아키텍쳐", "FastAPI · Supabase · Docker — 대시보드까지 포함한 전체 구성", "p.27", False),
    ("▶", "demo", "시연", "직접 올리고, 3초마다 감정이 그려지고, 그 구간을 들어봅니다", "p.28", True),
    ("04", "built", "구현과 성장", "구현 현황 · 정확도의 한계와 성장 구조 · 진행 경과 · AI와 일한 방식", "p.29–33", False),
]
rows = ""
for num, goto, title, desc, pg, hi in ROWS:
    bg = "#2A1418" if hi else INK2
    bd = RED if hi else BD
    nc = GOLD if hi else RED
    rows += (f'<div data-goto="{goto}" style="display:flex; align-items:center; gap:30px; background:{bg}; '
             f'border:{"2px" if hi else "1px"} solid {bd}; border-radius:16px; padding:22px 32px">'
             f'<p style="{OS}; font-size:52px; font-weight:600; line-height:1; color:{nc}; width:78px">{num}</p>'
             f'<div style="flex:1; display:flex; flex-direction:column; gap:4px">'
             f'<h3 style="{BH}; font-size:38px; font-weight:400; line-height:1.2; color:{TX}">{title}</h3>'
             f'<p style="font-size:23px; font-weight:400; color:{MUT}">{desc}</p></div>'
             f'<p style="{OS}; font-size:24px; color:#6C5F70">{pg}</p></div>')

toc = (f'<div style="width:500px; display:flex; flex-direction:column; justify-content:center; gap:26px">'
       f'{eyebrow("Contents")}'
       f'<h1 style="{BH}; font-size:132px; font-weight:400; line-height:1; color:{TX}">목차</h1>'
       f'<hr style="width:160px; height:0px; border-top:7px solid {RED}">'
       f'<p style="font-size:30px; font-weight:400; line-height:1.5; color:{SUB}">왜 이 문제인가에서 시작해<br>'
       f'어떻게 만들었고<br><b style="color:{GOLD}">직접 보여드린 뒤</b><br>어디로 가는지까지.</p></div>'
       f'<div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:12px">{rows}</div>')
open(SD + '/toc.html', 'w', encoding='utf-8').write(
    f'<section id="toc" data-transition="fade" style="background:{INK}; color:{TX}; {F}; '
    f'padding:128px 128px 160px; display:flex; gap:80px; align-items:stretch">{toc}'
    '<aside>■ 한 줄로: 문제 → 데이터 → 모델 → 시연 → 앞으로.\n'
    '■ 시연이 가운데 있는 게 포인트야. 모델 성적까지 말하고 바로 실물을 보여준 다음, 한계와 계획으로 마무리해.\n'
    '■ 이렇게 말하면 돼: "설명만 드리지 않고, 중간에 직접 돌려서 보여드리겠습니다."</aside></section>')

# ══════════════════════════════════════════════════════════════════
# 2. 시연 브리지 — 여기서 브라우저로 전환
# ══════════════════════════════════════════════════════════════════
steps = ""
for n, t, d in (("①", "통화 한 건을 올립니다", "적용 현장과 화자 지역을 먼저 고릅니다<br>상담센터 · 교육 · 돌봄 / 수도권 · 경상 · 전라…"),
                ("②", "3초마다 감정이 그려집니다", "감정 흐름 · 급변 지점 · 위험 구간<br>확신이 낮은 구간은 ‘판단 보류’로 비워둡니다"),
                ("③", "그 구간을 실제로 들어봅니다", "그래프를 누르면 그 지점부터 재생됩니다<br>지역 보정 전/후도 바로 비교합니다")):
    steps += (f'<div style="flex:1; display:flex; flex-direction:column; gap:14px; background:#F6D9D3; '
              f'border-radius:18px; padding:30px">'
              f'<p style="{OS}; font-size:44px; font-weight:600; line-height:1; color:{RED}">{n}</p>'
              f'<h3 style="font-size:32px; font-weight:700; line-height:1.3; color:#1A0B0C">{t}</h3>'
              f'<p style="font-size:24px; font-weight:400; line-height:1.55; color:#5A1512">{d}</p></div>')

facts = ""
for l, v in (("지금 구동", "노트북 1대 · 컨테이너 3개"), ("모델", "WavLM 파인튜닝 · mix40k"),
             ("실측", "69초 통화 → 추론 37초 (CPU)"), ("저장", "Supabase · 3초 구간 전부")):
    facts += (f'<div style="flex:1; background:#FBECE8; border-radius:14px; padding:18px 22px">'
              f'<p style="font-size:22px; color:#8A3A33">{l}</p>'
              f'<p style="font-size:27px; font-weight:700; color:#1A0B0C">{v}</p></div>')

demo = (f'{eyebrow("Live Demo", "#5A1512")}'
        f'<h1 style="{BH}; font-size:104px; font-weight:400; line-height:1.06; color:#1A0B0C">'
        f'설명은 여기까지,<br>직접 보여드리겠습니다</h1>'
        f'<div style="display:flex; gap:22px; align-items:stretch">{steps}</div>'
        f'<div style="display:flex; gap:14px; align-items:stretch">{facts}</div>'
        + foot('예시 데이터가 아니라 방금 올린 파일을 실제로 분석합니다 · 화면의 모든 수치는 그 분석 결과입니다', '#5A1512'))
open(SD + '/demo.html', 'w', encoding='utf-8').write(
    sec('demo', RED, '#1A0B0C', demo,
        '■ 여기서 브라우저로 전환해. 슬라이드는 이 장에 멈춰둬.\n'
        '■ 순서: ① 현장·지역 고르고 파일 올리기 ② 분석 끝나면 감정 흐름 설명 ③ 급변 지점 클릭해서 재생 ④ 지역 보정 ON/OFF 비교\n'
        '■ 시간이 없으면 ③까지만. 보정 비교는 사투리 질문이 나오면 그때 보여줘도 돼.\n'
        '■ 분석에 30~90초 걸려. 기다리는 동안 "지금 3초 창 127개를 CPU로 돌리는 중"이라고 설명하면 자연스러워.\n'
        '■ 혹시 안 되면: 예시 통화로 화면 구성만 보여주고 넘어가. 당황하지 말 것.',
        trans='fade'))

# ══════════════════════════════════════════════════════════════════
# 3. 구현 현황 — 방금 본 게 이렇게 돈다
# ══════════════════════════════════════════════════════════════════
flow = ""
for i, (t, d, hi) in enumerate([
        ("브라우저", "파일 업로드<br>결과 화면", False),
        ("FastAPI", "업로드 접수<br>작업 등록", False),
        ("Supabase", "음성 저장(비공개)<br>결과 3테이블", True),
        ("워커", "16kHz → 3초 창<br>WavLM 추론", False),
        ("결과 화면", "감정 흐름 · 재생<br>오분류 신고", False)]):
    if i:
        flow += arrow(44, 22)
    bg = '#3B2E1A' if hi else INK
    bd = GOLD if hi else BD
    tc = GOLD if hi else TX
    flow += (f'<div style="flex:1; display:flex; flex-direction:column; gap:8px; background:{bg}; '
             f'border:{"2px" if hi else "1px"} solid {bd}; border-radius:16px; padding:24px">'
             f'<h3 style="font-size:28px; font-weight:700; color:{tc}">{t}</h3>'
             f'<p style="font-size:24px; font-weight:400; line-height:1.45; color:{SUB}">{d}</p></div>')

stack = ""
for n in ("FastAPI", "Supabase(Postgres+Storage)", "Docker Compose ×3", "nginx", "WavLM-base-plus"):
    stack += (f'<p style="font-size:24px; font-weight:600; color:{TX}; background:{DEEP}; '
              f'border:1px solid {BD}; border-radius:999px; padding:10px 20px">{n}</p>')

reasons = ""
for lead, body in (("추론을 따로 뺐다", "업로드 응답은 즉시, 무거운 추론은 뒤에서"),
                   ("음성은 비공개 저장", "듣기는 1시간짜리 임시 링크로만"),
                   ("해석 규칙은 서버에", "화면만 바꾼 눈속임이 아니다")):
    reasons += (f'<p style="flex:1; font-size:21px; line-height:1.35; color:{SUB}; background:{INK}; '
                f'border:1px solid {BD}; border-radius:14px; padding:12px 18px">'
                f'<b style="color:{TX}">{lead}</b> — {body}</p>')

built = (head("04", "지금 보신 화면 — 컨테이너 3개 · 실측 37초")
         + eyebrow("설계도가 아니라 방금 시연한 그 구성 그대로")
         + f'<div style="display:flex; gap:14px; align-items:stretch">{flow}</div>'
         + f'<div style="display:flex; gap:14px; align-items:stretch">'
         + stat("컨테이너", "3개", "api · worker · web 분리")
         + stat("실측 추론", "37초", "69초 통화 · 45구간 · CPU", GOLD)
         + stat("저장", "3테이블", "통화 · 3초 구간 · 오분류 신고")
         + stat("확장", "worker ×N", "동시 요청은 큐로 순차 처리") + '</div>'
         + f'<div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center">'
         + f'<p style="font-size:25px; color:{SUB}">사용 기술</p>{stack}</div>'
         + f'<div style="display:flex; gap:14px; align-items:stretch">{reasons}</div>'
         + foot('업로드 100MB 제한 · 지원 형식 wav/mp3/m4a/flac/ogg · 코드와 화면은 재빌드 없이 반영되도록 구성'))
open(SD + '/built.html', 'w', encoding='utf-8').write(
    sec('built', INK2, TX, built,
        '■ 한 줄로: 방금 본 화면은 목업이 아니라 실제로 도는 시스템이다.\n'
        '■ 쉽게 풀면: 브라우저가 파일을 올리면 FastAPI가 받아서 음성은 Supabase 저장소에, 작업은 대기열에 넣어. '
        '워커가 그걸 집어다 16kHz로 바꾸고 3초씩 잘라 WavLM에 넣고, 결과를 DB에 쌓아. 화면은 그걸 그려.\n'
        '■ 왜 워커를 따로 뒀냐: 추론이 무거워서 같은 자리에서 하면 업로드가 끝날 때까지 화면이 멈춰. 분리하면 여러 건도 줄 세워 처리할 수 있고, 워커만 늘리면 동시 처리도 돼.\n'
        '■ 숫자: 69초 통화 = 45구간, CPU로 추론 37초. 서버 GPU면 훨씬 빨라.\n'
        '■ 이렇게 말하면 돼: "발표용 그림이 아니라 지금 이 노트북에서 돌고 있는 구성입니다."',
        extra='; padding:100px 128px 118px; gap:30px'))

# ══════════════════════════════════════════════════════════════════
# 4. 한계와 성장 — 쌓이면 좋아지는 구조
# ══════════════════════════════════════════════════════════════════
loop = ""
for i, (t, d) in enumerate([("서비스 사용", "통화가 분석된다"),
                            ("오분류 신고", "담당자가 ‘이건 분노 아님’ 한 번 누른다"),
                            ("라벨 축적", "현장에서 나온 진짜 데이터가 쌓인다"),
                            ("재학습", "신고 30건마다 추가 학습"),
                            ("정확도 향상", "그 현장 말투에 맞게 좋아진다")]):
    if i:
        loop += arrow(40, 20, GOLD)
    loop += (f'<div style="flex:1; display:flex; flex-direction:column; gap:8px; background:{INK}; '
             f'border:1px solid {BD}; border-radius:14px; padding:20px 22px">'
             f'<h3 style="font-size:26px; font-weight:700; color:{GOLD}">{t}</h3>'
             f'<p style="font-size:23px; font-weight:400; line-height:1.4; color:{SUB}">{d}</p></div>')

limits = ""
for t, d in (("성우 연기 음성", "실제 대화가 아니라 연기된 감정으로 배웠다"),
             ("화자 111그룹", "사람 수가 적어 목소리 다양성이 부족하다"),
             ("스튜디오 녹음", "전화망 8kHz · 잡음 환경은 아직 평가 못 했다")):
    limits += card(t, d, bg=INK, bc=SUB)

LIMITS = [
    ("01", "성우가 연기한 감정으로 배웠다",
     "AI-Hub·SKT 둘 다 스튜디오 연기·낭독 음성이다. 실제 통화의 흐릿한 말투는 배운 적이 없다.",
     "실전에서 더 틀린다", "자체 녹음 — 비성우·실제 대화체", RED),
    ("02", "목소리가 111명뿐이다",
     "학습 화자 79명 · 여성 73%. SKT를 4만 발화 섞어도 화자는 8명 늘었을 뿐이다.",
     "처음 듣는 목소리에 약하다", "현장 신고 데이터 축적 + 화자 확대", GOLD),
    ("03", "조용한 녹음만 들어봤다",
     "48kHz 스튜디오 음질. 전화망 8kHz·μ-law 압축·주변 소음은 아직 시험해 보지 않았다.",
     "실환경 하한선을 모른다", "전화망·잡음 주입 평가", BLUE),
]
lim = ""
for n, t, why, block, fix, col in LIMITS:
    lim += (f'<div class="lcard" style="flex:1; display:flex; flex-direction:column; gap:12px; background:{INK2}; '
            f'border:1px solid {BD}; border-top:4px solid {col}; border-radius:18px; padding:26px 28px">'
            f'<p style="{OS}; font-size:30px; font-weight:600; line-height:1; color:{col}">{n}</p>'
            f'<h3 style="font-size:31px; font-weight:700; line-height:1.28; color:{TX}">{t}</h3>'
            f'<p style="font-size:23px; font-weight:400; line-height:1.5; color:{SUB}; min-height:104px">{why}</p>'
            f'<p style="font-size:22px; color:{col}">→ {block}</p>'
            f'<div style="height:1px; background:{BD}"></div>'
            f'<p style="font-size:22px; line-height:1.4; color:{MUT}">'
            f'<b style="color:{TX}">푸는 방법</b><br>{fix}</p></div>')

growth = (head("04", "한계 3가지와, 쓸수록 좋아지는 구조")
          + f'<p style="font-size:27px; font-weight:400; line-height:1.45; color:{SUB}; margin-top:-10px">'
            f'점수를 더 올리는 문제가 아니라 <b style="color:{TX}">어떤 목소리를 안 들어봤나</b>의 문제다 — '
            f'셋 다 <b style="color:{GOLD}">데이터에서 온 한계</b>다.</p>'
          + f'<div style="display:flex; gap:20px; align-items:stretch">{lim}</div>'
          + f'<div class="gband" style="display:flex; align-items:center; gap:20px; background:#3B2E1A; '
            f'border:1px solid {GOLD}; border-radius:16px; padding:16px 24px; margin-top:4px">'
            f'<p style="{OS}; font-size:22px; letter-spacing:3px; color:{GOLD}; white-space:nowrap">그래서</p>'
            f'<p style="font-size:29px; font-weight:700; line-height:1.35; color:{TX}">'
            f'모델을 더 키우는 대신, <b style="color:{GOLD}">현장 목소리가 저절로 쌓이는 구조</b>를 서비스 안에 넣었다</p>'
            f'<p style="{OS}; font-size:19px; font-weight:600; letter-spacing:1px; color:{INK}; background:{GREEN}; '
            f'border-radius:999px; padding:5px 14px; white-space:nowrap; margin-left:auto">구현 완료</p></div>'
          + f'<div style="display:flex; gap:10px; align-items:stretch">{loop}</div>'
          + foot('신고 버튼은 이미 화면에 있고 신고는 DB(feedback)에 쌓인다 · 재학습 트리거는 누적 30건 · '
                 '현재는 데이터 축적 대기 상태'))
open(SD + '/growth.html', 'w', encoding='utf-8').write(
    sec('growth', INK, TX, growth,
        '■ 한 줄로: 남은 오차는 모델이 작아서가 아니라 안 들어본 목소리가 많아서다. 그래서 목소리가 쌓이는 구조를 만들었다.\n'
        '■ 앞에서 숫자는 충분히 말했으니 여기서는 반복하지 마. 이 장은 한계 세 개와 해결 구조만.\n'
        '■ 한계 1 (성우 연기): AI-Hub도 SKT도 연기·낭독이야. 실제 통화의 흐릿한 말투는 배운 적이 없어. → 자체 녹음이 다음 과제.\n'
        '■ 한계 2 (화자 111명): 학습 화자 79명, 여성 73%. SKT 4만을 섞어도 사람은 8명 늘었을 뿐이야. 처음 듣는 목소리에 약한 이유가 이거야.\n'
        '■ 한계 3 (조용한 녹음): 48kHz 스튜디오 음질만 봤어. 전화망 8kHz·잡음은 아직 시험 못 했고, 그래서 실환경 하한선을 모른다고 정직하게 말해.\n'
        '■ 그다음 띠가 핵심: 셋 다 데이터 문제라서, 모델을 키우는 대신 현장 데이터가 쌓이는 걸 서비스에 넣었어. 신고 버튼은 방금 시연에서 이미 봤고, DB에 쌓이고, 30건마다 재학습.\n'
        '■ 이렇게 말하면 돼: "지금 부족한 건 알고리즘이 아니라 목소리입니다. 그래서 쓸수록 목소리가 모이게 만들었습니다."',
        extra='; padding:92px 128px 118px; gap:22px'))

# ══════════════════════════════════════════════════════════════════
# 5. 마무리
# ══════════════════════════════════════════════════════════════════
takes = ""
for n, t, d in (("01", "소리만으로 읽습니다", "무슨 말을 했는지가 아니라 어떻게 말했는지. 대화 내용을 저장하지 않아도 됩니다"),
                ("02", "틀릴 수 있다고 말합니다", "확신이 낮으면 단정하지 않고 사람에게 넘깁니다"),
                ("03", "쓸수록 좋아집니다", "현장의 오분류 신고가 그대로 다음 학습 데이터가 됩니다")):
    takes += (f'<div style="flex:1; display:flex; flex-direction:column; gap:10px; background:#F6D9D3; '
              f'border-radius:16px; padding:28px">'
              f'<p style="{OS}; font-size:30px; font-weight:600; color:{RED}">{n}</p>'
              f'<h3 style="font-size:30px; font-weight:700; line-height:1.25; color:#1A0B0C">{t}</h3>'
              f'<p style="font-size:24px; font-weight:400; line-height:1.45; color:#5A1512">{d}</p></div>')

close = (eyebrow("Wrap up", "#5A1512")
         + f'<h1 style="{BH}; font-size:112px; font-weight:400; line-height:1.06; color:#1A0B0C">'
         f'말투에서 감정을 읽고,<br>모를 땐 모른다고 합니다</h1>'
         + f'<div style="display:flex; gap:22px; align-items:stretch">{takes}</div>'
         + f'<p style="font-size:36px; font-weight:700; line-height:1.4; color:#1A0B0C">감사합니다. 질문 받겠습니다.</p>'
         + foot('K-Voice · 고민혁 · 정해운 · WavLM 파인튜닝 · FastAPI · Supabase · Docker', '#5A1512'))
open(SD + '/close.html', 'w', encoding='utf-8').write(
    sec('close', RED, '#1A0B0C', close,
        '■ 세 문장으로 남겨: 소리로 읽는다 / 모르면 모른다고 한다 / 쓸수록 좋아진다.\n'
        '■ 질문이 나올 만한 것: 사투리(→ 지역 보정 화면), 중립이 왜 어렵나(→ 판단 보류), 정확도가 낮지 않나(→ 보류 허용 시 90%, 재학습 루프), 실시간 되나(→ CPU 37초, GPU면 11초).\n'
        '■ 마지막은 짧게. 길게 끌지 말고 질문으로 넘겨.', trans='fade'))

print('생성 완료: toc, demo, built, growth, close')
