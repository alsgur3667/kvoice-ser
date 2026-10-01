# -*- coding: utf-8 -*-
import re, json, os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import ICONS

SRC = "/tmp/claude-0/-home-claude/3b4a5ffc-1e60-5757-af81-f2bfc2cfeac3/scratchpad/artifact-files/45613172-3408-4f13-8cb5-a037086af0ac/project"
ORDER = ["cover","toc","problem","problem2","goal","voices",
         "s01","data","dtimeline","eda","edaheat","edadist","s01b",
         "s02","prepviz","prepfunnel","imbal",
         "wave","trained","models","tb","effort1","effort2","effort3","s03","general","s05b",
         "demo",                      # ← 여기서 브라우저로 전환해 실제 시연
         "built","growth","gantt","aiwork","close"]
TITLES = {
 "cover":"표지","toc":"목차","problem":"01 문제","problem2":"01 왜 만들었나","goal":"01 왜 음성인가","s01":"02 왜 이 데이터인가","eda":"02 EDA",
 "s01b":"세 번의 트레이드오프","data":"02 데이터 구성","s02":"02 EDA→전처리",
 "dtimeline":"02 날짜별 데이터","voices":"02 감정별 음성","edaheat":"02 EDA 지시vs느낀감정","edadist":"02 EDA 분포","prepviz":"02 전처리 과정","prepfunnel":"02 전처리 결과","imbal":"02 불균형","tb":"03 텐서보드","trained":"03 무엇을 학습","aiwork":"AI와 일한 방식","gantt":"04 간트 차트","effort1":"03 향상 노력","effort2":"03 점수 곡선","effort3":"03 실패에서 배운 것","wave":"03 왜 파형인가","cands":"03 후보 모델","models":"03 실험한 모델","s03":"03 외부 검증",
 "general":"03 범용성","s04":"04 예시화면","s04a":"04 화면 흐름","s04b":"04 결과 화면 상세","s05":"05 아키텍쳐","s05b":"04 아키텍쳐","s05c":"05 대시보드",
 "journey":"걸어온 길","week":"앞으로 일주일","close":"마무리",
 "demo":"▶ 시연","built":"04 구현 현황","growth":"04 한계와 성장"}

missing = set()

def icon_repl(m):
    attrs = m.group(1)
    name = re.search(r'name="([^"]+)"', attrs)
    style = re.search(r'style="([^"]*)"', attrs)
    name = name.group(1) if name else ""
    style = style.group(1) if style else ""
    if name not in ICONS:
        missing.add(name)
        inner = '<circle cx="12" cy="12" r="9"/>'
    else:
        inner = ICONS[name][1]
    st = style.strip().rstrip(';')
    st = st + "; flex:0 0 auto; display:block; overflow:visible"
    return ('<svg class="xi" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            'style="%s" aria-hidden="true">%s</svg>' % (st, inner))

ARROW_CLIP = "polygon(0% 28%, 58% 28%, 58% 0%, 100% 50%, 58% 100%, 58% 72%, 0% 72%)"

def shape_repl(m):
    attrs = m.group(1)
    style = re.search(r'style="([^"]*)"', attrs)
    style = style.group(1) if style else ""
    st = style.strip().rstrip(';')
    st += "; flex:0 0 auto; display:block; -webkit-clip-path:%s; clip-path:%s" % (ARROW_CLIP, ARROW_CLIP)
    return '<span class="xs" style="%s" aria-hidden="true"></span>' % st


# ---- 가독성 보정 (프로젝터 기준): 얇은 글씨 굵게, 흐린 회색 밝게, 작은 글씨 키우기 ----
NO_RESIZE = {"s04a", "s04b", "s05b"}   # 제품 화면 목업 · 조밀한 구성도는 크기 유지
COLOR_MAP = {
    "#B5A9AE": "#D2C8CD", "#b5a9ae": "#D2C8CD",   # 설명 글 회색
    "#8E8188": "#ADA1A7", "#8e8188": "#ADA1A7",   # 보조 회색
    "#7A6E74": "#9C9096", "#7a6e74": "#9C9096",   # 각주 회색
}
def legibility(raw, sid):
    raw = raw.replace("font-weight:300", "font-weight:400")
    for a, b in COLOR_MAP.items():
        raw = raw.replace(a, b)
    if sid not in NO_RESIZE:
        def bump(m):
            v = float(m.group(1))
            if 15 <= v <= 24:
                v += 2
            return "font-size:%gpx" % v
        raw = re.sub(r"font-size:\s*([\d.]+)px", bump, raw)
    return raw

slides = []
for sid in ORDER:
    raw = open(os.path.join(SRC, "slides", sid + ".html"), encoding="utf-8").read()
    # pull aside (speaker notes)
    notes = ""
    ma = re.search(r'<aside>(.*?)</aside>', raw, re.S)
    if ma:
        notes = ma.group(1)
        raw = raw[:ma.start()] + raw[ma.end():]
    raw = re.sub(r'<x-icon\b([^>]*?)\s*>\s*</x-icon>', icon_repl, raw)
    raw = re.sub(r'<x-icon\b([^>]*?)/>', icon_repl, raw)
    raw = re.sub(r'<x-shape\b([^>]*?)\s*>\s*</x-shape>', shape_repl, raw)
    raw = re.sub(r'<x-shape\b([^>]*?)/>', shape_repl, raw)
    # add class to the section tag
    raw = legibility(raw, sid)
    raw = re.sub(r'^\s*<section ', '<section class="slide" ', raw.strip(), count=1)
    slides.append({"id": sid, "html": raw.strip(), "notes": notes.strip(), "title": TITLES.get(sid, sid)})

if missing:
    print("MISSING ICONS:", missing)

notes_json = json.dumps({s["id"]: s["notes"] for s in slides}, ensure_ascii=False)
titles_json = json.dumps([{"id": s["id"], "t": s["title"]} for s in slides], ensure_ascii=False)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slides.json"), "w", encoding="utf-8").write(
    json.dumps(slides, ensure_ascii=False))
print("slides:", len(slides))
