# -*- coding: utf-8 -*-
import json, os
D = os.path.dirname(os.path.abspath(__file__))
slides = json.load(open(os.path.join(D, "slides.json"), encoding="utf-8"))
tpl = open(os.path.join(D, "template.html"), encoding="utf-8").read()

body = "\n".join(s["html"] for s in slides)
notes = json.dumps({s["id"]: s["notes"] for s in slides}, ensure_ascii=False)
titles = json.dumps([{"id": s["id"], "t": s["title"]} for s in slides], ensure_ascii=False)

out = tpl.replace("<!--SLIDES-->", body).replace("/*NOTES*/", notes).replace("/*TITLES*/", titles)
dst = "/mnt/user-data/outputs/voicekorean_deck.html"
os.makedirs("/mnt/user-data/outputs", exist_ok=True)
open(dst, "w", encoding="utf-8").write(out)
print(dst, len(out), "bytes")
