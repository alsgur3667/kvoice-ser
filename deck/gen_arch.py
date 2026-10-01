# -*- coding: utf-8 -*-
"""시연 직전 — 실제로 돌아가는 구성 1장"""
import os
SD = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project/slides"

INK='#120E14'; CARD='#1C1620'; CARD2='#241C29'; LINE='#362C38'
TX='#F5F0EA'; SUB='#D6C9CE'; MUT='#8E8188'; DIM='#6C5F70'
RED='#E8433F'; GOLD='#F2B63D'; BLUE='#9BB7E8'; GREEN='#6FD08C'
F = "font-family:'Noto Sans KR', Arial, sans-serif"
BH = "font-family:'Black Han Sans', 'Noto Sans KR', sans-serif"
OS = "font-family:Oswald, 'Arial Narrow', sans-serif"

def step(n, t, d):
    bg = GOLD if n else 'transparent'
    fg = INK if n else 'transparent'
    return (f'<div class="astep" style="display:flex; gap:12px; align-items:flex-start">'
            f'<p class="anum" style="{OS}; font-size:20px; font-weight:600; color:{fg}; background:{bg}; '
            f'border-radius:8px; padding:2px 10px; flex:none; margin-top:3px">{n or "·"}</p>'
            f'<p style="font-size:20px; font-weight:400; line-height:1.38; color:{SUB}">'
            f'<b style="color:{TX}; font-weight:700">{t}</b><br>{d}</p></div>')

def box(tag, title, sub, steps, color):
    return (f'<div class="abox" style="flex:1; display:flex; flex-direction:column; gap:10px; background:{CARD}; '
            f'border:1px solid {LINE}; border-top:3px solid {color}; border-radius:16px; padding:18px 22px">'
            f'<p class="atag" style="{OS}; font-size:19px; font-weight:600; letter-spacing:2px; color:{color}">{tag}</p>'
            f'<h3 style="font-size:27px; font-weight:700; line-height:1.2; color:{TX}">{title}</h3>'
            f'<p style="font-size:19px; color:{MUT}; margin-top:-4px">{sub}</p>'
            f'<div style="height:1px; background:{LINE}"></div>'
            f'<div style="display:flex; flex-direction:column; gap:9px">{"".join(steps)}</div></div>')

arrow = f'<x-shape kind="arrow-right" style="width:52px; height:26px; background:{RED}; align-self:center"></x-shape>'

web = box("web · nginx", "브라우저 화면", "정적 서빙 + /api 프록시", [
    step("1", "녹취 업로드", "현장(상담·교육·가족) · 지역 선택 · 100MB 제한"),
    step("6", "결과 화면 렌더", "3초 구간 타임라인 · 대시보드는 10초마다 갱신"),
    step("7", "구간 클릭 재생", "서명 URL을 받아 그 지점부터 — 버킷은 비공개"),
], BLUE)

api = box("api · FastAPI", "요청을 받는 서버", "uvicorn · 비동기 접수", [
    step("2", "원본 저장 + 작업 등록", "Storage 업로드 후 analyses 행 생성 (status=queued)"),
    step("", "즉시 접수 응답", "분석을 기다리지 않고 id를 먼저 돌려준다"),
    step("", "조회 · 통계 API", "/analyses · /stats · /feedback · 서명 URL 발급"),
], GOLD)

wk = box("worker", "실제 추론", "같은 이미지, 실행 명령만 다름", [
    step("3", "큐에서 집어온다", "2초마다 queued 1건 claim — API와 분리"),
    step("4", "전처리 → 추론", "16kHz · 3초 창 / 1.5초 간격 · WavLM (CPU)"),
    step("5", "규칙 적용 · 저장", "현장·지역 매핑 + 임계값 0.70 → segments · done"),
], GREEN)

sb_items = [("PostgreSQL", "analyses · segments · feedback — 작업 상태와 결과"),
            ("Storage", "원본 녹취 (비공개 버킷) · 서명 URL로만 재생"),
            ("접근 통제", "RLS 전면 차단 · 서버 전용 secret 키는 브라우저로 안 나간다")]
sb = ''.join(f'<div style="flex:1; background:{CARD2}; border-radius:12px; padding:16px 20px">'
             f'<p style="font-size:22px; font-weight:700; color:{GOLD}">{t}</p>'
             f'<p style="font-size:19px; font-weight:400; line-height:1.35; color:{SUB}; margin-top:3px">{d}</p></div>'
             for t, d in sb_items)

body = (f'<div style="display:flex; align-items:center; gap:28px">'
        f'<p style="{OS}; font-size:30px; font-weight:600; color:{TX}; background:{RED}; border-radius:10px; padding:8px 20px">04</p>'
        f'<h2 style="{BH}; font-size:52px; font-weight:400; line-height:1.15; color:{TX}">'
        f'실제로 돌아가는 구성 — FastAPI · Supabase · Docker</h2></div>'
        f'<p class="asubline" style="font-size:24px; font-weight:400; line-height:1.4; color:{SUB}; margin-top:-6px">'
        f'<b style="color:{TX}">docker compose up</b> 한 번에 컨테이너 세 개가 뜬다. 다음 장부터 '
        f'<b style="color:{GOLD}">이 구성 위에서 실제로 돌려본다.</b></p>'
        f'<div style="display:flex; gap:16px; align-items:stretch">{web}{arrow}{api}{arrow}{wk}</div>'
        f'<div class="asb" style="background:{CARD}; border:1px solid {GOLD}; border-radius:14px; padding:13px 20px; '
        f'display:flex; flex-direction:column; gap:12px">'
        f'<p style="{OS}; font-size:21px; letter-spacing:3px; color:{GOLD}">SUPABASE — 데이터베이스 · 파일 저장소</p>'
        f'<div style="display:flex; gap:14px">{sb}</div></div>'
        f'<div class="afact" style="display:flex; align-items:center; gap:18px; background:{CARD2}; '
        f'border-left:5px solid {RED}; border-radius:12px; padding:11px 20px">'
        f'<p style="{OS}; font-size:20px; letter-spacing:3px; color:{RED}; white-space:nowrap">실측</p>'
        f'<p style="font-size:22px; font-weight:400; line-height:1.35; color:{TX}">'
        f'GPU 없이 CPU로 — <b>69초 통화 → 45구간 · 추론 36.8초</b> · 모델은 워커가 뜰 때 best.pt를 한 번만 읽고, '
        f'<b style="color:{GOLD}">worker 컨테이너만 늘리면 처리량이 늘어난다.</b></p></div>'
        f'<p style="position:absolute; left:128px; bottom:38px; width:1664px; font-size:19px; color:#7A6E74">'
        f'로그인·실시간 push는 아직 없다 — 지금은 서버 전용 키로만 접근하고, 브라우저가 상태를 조회하는 방식이다</p>')

note = """■ 한 줄로: 지금 보여드릴 화면이 어떤 구성 위에서 도는지 30초만.
■ 컨테이너 셋: 화면(nginx), 요청 받는 서버(FastAPI), 실제 추론하는 워커. docker compose up 한 번에 같이 떠.
■ 흐름: ①올리면 → ②원본은 Storage에, 작업은 DB에 'queued'로 적고 바로 응답을 돌려줘(기다리게 안 해) → ③워커가 2초마다 큐를 보고 집어가 → ④16kHz로 바꾸고 3초씩 잘라 WavLM으로 추론 → ⑤현장·지역 규칙과 임계값 0.70을 적용해 구간 결과 저장 → ⑥화면이 상태를 조회해 타임라인을 그리고 → ⑦구간을 클릭하면 서명 URL로 그 지점부터 재생돼.
■ 포인트 셋만 말하면 돼: (1) 업로드와 추론을 분리해서 화면이 안 멈춘다, (2) GPU 없이 CPU로 돈다, (3) 워커 컨테이너만 늘리면 처리량이 는다.
■ 정직하게: 로그인과 실시간 push는 아직 없어. 지금은 서버 전용 키로만 Supabase에 붙고 RLS는 전면 차단, 화면은 조회 방식이야. 물어보면 그대로 말하고 다음 단계라고 하면 돼.
■ 이렇게 넘어가면 돼: "이 구성이 지금 이 노트북에서 돌고 있습니다. 바로 올려보겠습니다." → 브라우저로 전환."""

open(os.path.join(SD, "arch.html"), "w", encoding="utf-8").write(
    f'''<section id="arch" data-transition="push" style="background:{INK}; color:{TX}; {F}; padding:74px 128px 118px; display:flex; flex-direction:column; gap:14px">
{body}
  <aside>{note}</aside>
</section>''')
print("arch 생성 완료")
