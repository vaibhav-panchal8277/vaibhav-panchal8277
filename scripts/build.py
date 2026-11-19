"""Build the SVG images for the GitHub profile README.

Every image is generated from the CONTENT block below, in a dark and a light
version, with the fonts it uses embedded as small subsets (GitHub shows README
SVGs as images, so they cannot load web fonts).

Edit CONTENT, then run from the repo root:

    python -m venv .venv && .venv/bin/pip install fonttools brotli
    .venv/bin/python scripts/build.py

Fonts (SIL Open Font License, see scripts/fonts/OFL-*.txt):
Inter Tight, JetBrains Mono and Newsreader, the same fonts as the portfolio.
"""
from __future__ import annotations

import base64
import io
import math
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"

# --------------------------------------------------------------------------
# Content. Every number here is from the resume or a re-run of the repos.
# --------------------------------------------------------------------------
CONTENT = {
    "hero": {
        "eyebrow": "AI/ML DEVELOPER · TESTGRID · GUJARAT, INDIA",
        "name": "Vaibhav Panchal",
        "line1": "I test AI until it breaks,",
        "line2_pre": "then ",
        "line2_em": "make it hold up",
        "line2_post": ".",
        "focus": ["LLM AGENTS", "RAG", "EVALUATION", "GUARDRAILS", "VISION"],
    },
    "links": [
        ("portfolio", "Portfolio", "out"),
        ("resume", "Résumé PDF", "down"),
        ("linkedin", "LinkedIn", "out"),
        ("medium", "Medium", "out"),
        ("email", "Email", "out"),
        # Shown under the MESH and RAG cards, not in the top row.
        ("demo", "Live demo", "out"),
    ],
    "heads": {
        "results": ("01", "Results I can reproduce", "MEASURED, NOT ESTIMATED"),
        "work": ("02", "Selected work", "ONE AT WORK, THREE OF MY OWN"),
        "toolkit": ("03", "Toolkit", "WHAT I BUILD WITH"),
        "research": ("04", "Research and writing", "PAPERS AND POSTS"),
    },
    "evals": {
        "command": "$ python -m evals --all",
        "rows": [
            ("Guardrails safety set", "35/35", "100% precision and recall, 0% false positives, in two runs"),
            ("Multi-agent end-to-end suite", "39/40", "97.5% over two runs; intent, tool calls and blocks all 100%"),
            ("Multi-agent offline tests", "137", "Backend and frontend, plus 23/23 live end-to-end"),
            ("RAG golden set", "45 Qs", "RAGAS, retrieval hit rate and MRR, refusal accuracy"),
            ("UI element detector, TestGrid", "−85%", "Processing time, with missing-element defects fixed"),
            ("ECA on YOLOv11s-OBB", "+3.8%", "mAP50 on DIOR-R, +4.3% recall, no extra parameters"),
        ],
        "note": "Project results re-run from the public repos. Detector result from my work at TestGrid.",
    },
    "cards": [
        {
            "key": "cotester",
            "eyebrow": "TESTGRID · COTESTER VISION",
            "title": "An in-house vision pipeline for CoTester",
            "summary": "Replaced a third-party LLM API with models we run ourselves, served on FastAPI. "
            "Icon naming in ONNX and two-pass OCR catch elements the first pass missed, "
            "and image-based element detection time is cut by about 85%.",
            "nodes": [("Screenshot", "web or mobile"), ("Detection", "VLM, YOLO"),
                      ("Text and icons", "two-pass OCR, ONNX"), ("Elements", "role, label, position")],
            "tags": ["Python", "VLM", "YOLO", "ONNX", "OCR", "FastAPI"],
            "cta": "CASE STUDY",
        },
        {
            "key": "mesh",
            "eyebrow": "MULTI-AGENT SYSTEM",
            "title": "MESH Support",
            "summary": "A customer support platform where a LangGraph supervisor routes each query to a "
            "Billing, Technical or Refunds agent. Fail-closed NeMo Guardrails gate every tool call, "
            "access is checked on the server, and refunds run only on the customer's confirmation.",
            "nodes": [("Customer", "query"), ("Input rail", "fail-closed, in parallel"),
                      ("Supervisor", "LangGraph router"), ("Specialist", "billing, tech, refunds")],
            "tags": ["Python", "LangGraph", "FastAPI", "MongoDB", "NeMo Guardrails", "Langfuse", "Pytest"],
            "cta": "REPO",
        },
        {
            "key": "rag",
            "eyebrow": "RETRIEVAL AND EVALUATION",
            "title": "RAG system with an evaluation pipeline",
            "summary": "Hybrid search over Pinecone and BM25, fused with Reciprocal Rank Fusion, that falls "
            "back to keywords when the vector store is down. A 45-question golden set scores "
            "RAGAS (with a separate judge model), retrieval hit rate, MRR and refusals, and 72 "
            "offline tests run in CI.",
            "nodes": [("Documents", "chunked, embedded"), ("Hybrid search", "Pinecone + BM25"),
                      ("Fusion", "RRF, k = 60"), ("Cited answer", "scored, traced")],
            "tags": ["Python", "FastAPI", "React", "LangChain", "Pinecone", "BM25", "RAGAS", "Docker"],
            "cta": "REPO",
        },
        {
            "key": "examforge",
            "eyebrow": "LLM TOOLING",
            "title": "ExamForge",
            "summary": "Turns a syllabus PDF into a question paper from a custom marks distribution and "
            "difficulty. Runs offline on Ollama or on OpenAI through one client, and exports "
            "the paper as a PDF.",
            "nodes": [("Syllabus", "PDF upload"), ("Topics", "found by the LLM"),
                      ("Questions", "marks, difficulty"), ("Paper", "PDF export")],
            "tags": ["Python", "Streamlit", "OpenAI API", "Ollama", "ReportLab"],
            "cta": "REPO",
        },
    ],
    "toolkit": [
        ("LLMs and agents", ["LangGraph", "LangChain", "Multi-agent", "Tool calling", "RAG", "NLP",
                             "Hybrid search", "Prompt engineering", "MCP"]),
        ("Models and APIs", ["OpenAI API", "Groq", "Ollama", "Hugging Face", "VLMs", "Embeddings"]),
        ("Evaluation and safety", ["RAGAS", "NeMo Guardrails", "Langfuse", "Golden sets", "Agent testing"]),
        ("Backend and deployment", ["Python", "FastAPI", "AWS EC2", "Nginx", "Pytest"]),
        ("ML and vision", ["PyTorch", "TensorFlow", "Scikit-learn", "YOLO", "OpenCV", "ONNX", "OCR"]),
        ("Data and tools", ["MongoDB", "Pinecone", "SQL", "Streamlit", "Git", "Postman", "Selenium Grid"]),
        # Drawn as one full-width row under the grid.
        ("Familiar", ["Go", "Docker", "GitHub Actions", "REST APIs", "JavaScript", "React", "Google Cloud Run",
                      "Vercel", "Render", "LangSmith", "Kaggle"]),
    ],
}

# --------------------------------------------------------------------------
# Palettes (the portfolio's indigo and amber tokens)
# --------------------------------------------------------------------------
PALETTES = {
    "dark": dict(surface="#12141f", chip="#181b2b", line="#262a40", fg="#ecedf5", muted="#8b8ea3",
                 strong="#a9acc0", accent="#8b9cff", alt="#ffc861", rule="#23263a"),
    "light": dict(surface="#ffffff", chip="#f3f4fa", line="#dfe2ee", fg="#16172a", muted="#6a6d85",
                  strong="#474a63", accent="#3f51d6", alt="#a06400", rule="#e0e2ee"),
}

# --------------------------------------------------------------------------
# Fonts: static instances of the variable fonts, measured without kerning so
# the layout maths matches what the browser draws.
# --------------------------------------------------------------------------
FONT_FILES = {
    "sans": "InterTight-Variable-latin.woff2",
    "mono": "JetBrainsMono-Variable-latin.woff2",
    "serif": "Newsreader-Italic-Variable-latin.woff2",
}
CSS_FAMILY = {"sans": "VPSans", "mono": "VPMono", "serif": "VPSerif"}
_instances: dict[tuple[str, int], TTFont] = {}


def font(fam: str, weight: int) -> TTFont:
    key = (fam, weight)
    if key not in _instances:
        var = TTFont(FONT_DIR / FONT_FILES[fam])
        _instances[key] = instancer.instantiateVariableFont(var, {"wght": weight})
    return _instances[key]


def measure(text: str, fam: str, weight: int, size: float, spacing: float = 0.0) -> float:
    f = font(fam, weight)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    upm = f["head"].unitsPerEm
    total = 0
    for ch in text:
        glyph = cmap.get(ord(ch))
        if glyph is None:
            raise ValueError(f"{fam} has no glyph for {ch!r} in {text!r}")
        total += hmtx[glyph][0]
    return total * size / upm + spacing * max(len(text) - 1, 0)


def font_face(fam: str, weight: int, chars: set[str]) -> str:
    f = font(fam, weight)
    buf = io.BytesIO()
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = []
    options.name_IDs = []
    options.notdef_outline = True
    sub = subset.Subsetter(options)
    sub.populate(text="".join(sorted(chars)))
    tmp = io.BytesIO()
    f.save(tmp)  # subset a copy, so the cached instance stays whole for later images
    tmp.seek(0)
    clone = TTFont(tmp)
    sub.subset(clone)
    clone.flavor = "woff2"
    clone.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:{CSS_FAMILY[fam]};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def wrap(text: str, fam: str, weight: int, size: float, width: float) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and measure(trial, fam, weight, size) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


# --------------------------------------------------------------------------
# A tiny SVG writer that remembers which glyphs each font instance needs
# --------------------------------------------------------------------------
class Svg:
    def __init__(self, width: float, height: float, label: str):
        self.w, self.h, self.label = width, height, label
        self.parts: list[str] = []
        self.defs: list[str] = []
        self.used: dict[tuple[str, int], set[str]] = defaultdict(set)

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x, y, s, fam="sans", weight=400, size=16, fill="#000", anchor="start",
             spacing=0.0, opacity=None) -> float:
        self.used[(fam, weight)].update(s)
        extra = f' letter-spacing="{spacing}"' if spacing else ""
        extra += f' text-anchor="{anchor}"' if anchor != "start" else ""
        extra += f' opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{CSS_FAMILY[fam]}" '
                 f'font-weight="{weight}" font-size="{size}" fill="{fill}"{extra}>{escape(s)}</text>')
        return measure(s, fam, weight, size, spacing)

    def save(self, name: str) -> None:
        css = "".join(font_face(fam, wt, chars) for (fam, wt), chars in sorted(self.used.items()))
        body = "".join(self.parts)
        defs = "".join(self.defs)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
               f'viewBox="0 0 {self.w:.0f} {self.h:.0f}" role="img" aria-label="{escape(self.label)}">'
               f"<title>{escape(self.label)}</title><defs><style>{css}</style>{defs}</defs>{body}</svg>")
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"  {name:28} {len(svg) / 1024:6.1f} KB")


def check(x, y, color, size=12):
    s = size
    return (f'<path d="M{x:.1f} {y + s * 0.55:.1f} L{x + s * 0.38:.1f} {y + s * 0.9:.1f} '
            f'L{x + s:.1f} {y + s * 0.12:.1f}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def arrow_out(x, y, color, s=10):
    return (f'<path d="M{x:.1f} {y + s:.1f} L{x + s:.1f} {y:.1f} M{x + s * 0.3:.1f} {y:.1f} '
            f'H{x + s:.1f} V{y + s * 0.7:.1f}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def arrow_down(x, y, color, s=10):
    return (f'<path d="M{x + s / 2:.1f} {y:.1f} V{y + s:.1f} M{x + s * 0.15:.1f} {y + s * 0.62:.1f} '
            f'L{x + s / 2:.1f} {y + s:.1f} L{x + s * 0.85:.1f} {y + s * 0.62:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')


def arrow_right(x1, x2, y, color):
    return (f'<path d="M{x1:.1f} {y:.1f} H{x2:.1f} M{x2 - 5:.1f} {y - 4:.1f} L{x2:.1f} {y:.1f} '
            f'L{x2 - 5:.1f} {y + 4:.1f}" fill="none" stroke="{color}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def brackets(x, y, size, color, sw=1.5):
    arm = size * 0.28
    d = (f"M{x} {y + arm} V{y} H{x + arm} M{x + size - arm} {y} H{x + size} V{y + arm} "
         f"M{x + size} {y + size - arm} V{y + size} H{x + size - arm} "
         f"M{x + arm} {y + size} H{x} V{y + size - arm}")
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" opacity="0.85"/>'


# --------------------------------------------------------------------------
# Hero: the portfolio's night horizon with detection boxes. Dark in both
# themes, like the hero on the site.
# --------------------------------------------------------------------------
def seeded(seed: int):
    state = seed

    def rand():
        nonlocal state
        state = (state * 16807) % 2147483647
        return state / 2147483647

    return rand


def build_hero():
    W, H = 1000, 420
    c = CONTENT["hero"]
    svg = Svg(W, H, f"{c['name']}. {c['eyebrow'].title()}. {c['line1']} "
                    f"{c['line2_pre']}{c['line2_em']}{c['line2_post']}")
    rand = seeded(7 * 9973)
    svg.defs.append(
        '<clipPath id="r"><rect width="1000" height="420" rx="18"/></clipPath>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#07081a"/><stop offset="38%" stop-color="#121a42"/>'
        '<stop offset="60%" stop-color="#2c3170"/><stop offset="74%" stop-color="#6b4f6e"/>'
        '<stop offset="84%" stop-color="#e5a24a"/></linearGradient>'
        '<radialGradient id="glow" cx="50%" cy="100%" r="62%"><stop offset="0%" stop-color="#ffc861" '
        'stop-opacity="0.3"/><stop offset="100%" stop-color="#ffc861" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#07081a" '
        'stop-opacity="0.55"/><stop offset="60%" stop-color="#07081a" stop-opacity="0"/></linearGradient>'
    )
    svg.add('<g clip-path="url(#r)">')
    svg.add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/><rect width="{W}" height="{H}" fill="url(#glow)"/>')
    for _ in range(120):
        x, y, r, o = rand() * W, rand() * 250, 0.4 + rand() * 0.9, 0.25 + rand() * 0.6
        svg.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#ecedf5" opacity="{o:.2f}"/>')
    mx, my = 845, 118
    svg.add(f'<circle cx="{mx}" cy="{my}" r="28" fill="#e9dfc9" opacity="0.92"/>'
            f'<circle cx="{mx - 11}" cy="{my - 7}" r="24" fill="#121a42" opacity="0.18"/>')
    ridges = [(330, 24, "#4b3f6b"), (356, 22, "#342d57"), (384, 19, "#211d3d"), (410, 14, "#0f0e22")]
    for base, amp, color in ridges:
        a, b, cc = rand() * 6.28, rand() * 6.28, rand() * 6.28
        d = f"M0 {H}"
        for x in range(0, W + 20, 20):
            wave = math.sin(x / 170 + a) * 0.6 + math.sin(x / 70 + b) * 0.28 + math.sin(x / 31 + cc) * 0.12
            d += f" L{x} {base + amp * wave:.1f}"
        svg.add(f'<path d="{d} L{W} {H} Z" fill="{color}"/>')
    svg.add(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')

    # Detection boxes, the site's motif: the model labelling what it sees.
    amber = "#ffc861"
    svg.add(brackets(mx - 46, my - 46, 92, amber))
    svg.text(mx - 46, my - 54, "MOON 0.97", "mono", 500, 11, amber, spacing=1.2, opacity=0.9)
    svg.add(brackets(640, 296, 96, amber))
    svg.text(640, 288, "RIDGE 0.91", "mono", 500, 11, amber, spacing=1.2, opacity=0.9)

    x = 56
    svg.text(x, 78, c["eyebrow"], "mono", 600, 12.5, amber, spacing=2.2)
    svg.text(x, 152, c["name"], "sans", 700, 66, "#ecedf5", spacing=-1.6)
    svg.text(x, 204, c["line1"], "sans", 400, 27, "#c9cbe0")
    w = svg.text(x, 240, c["line2_pre"], "sans", 400, 27, "#c9cbe0")
    w += svg.text(x + w, 241, c["line2_em"], "serif", 500, 31, "#8b9cff")
    svg.text(x + w, 240, c["line2_post"], "sans", 400, 27, "#c9cbe0")

    cx = x
    for i, item in enumerate(c["focus"]):
        tw = measure(item, "mono", 500, 11, 1.4)
        svg.add(f'<rect x="{cx:.1f}" y="268" width="{tw + 22:.1f}" height="26" rx="13" '
                f'fill="#0b0c14" fill-opacity="0.55" stroke="#3a3f6b"/>')
        svg.text(cx + 11, 285, item, "mono", 500, 11, "#a9b4ff", spacing=1.4)
        cx += tw + 30
    svg.add("</g>")
    svg.save("hero.svg")


# --------------------------------------------------------------------------
# Link buttons
# --------------------------------------------------------------------------
def build_links():
    widths = {}
    for key, label, kind in CONTENT["links"]:
        tw = measure(label.upper(), "mono", 600, 12.5, 1.4)
        W, H = 16 + 8 + 10 + tw + 12 + 11 + 16, 42
        widths[key] = round(W)
        for mode, p in PALETTES.items():
            svg = Svg(W, H, label)
            svg.add(f'<rect x="0.75" y="0.75" width="{W - 1.5:.1f}" height="{H - 1.5:.1f}" rx="10" '
                    f'fill="{p["surface"]}" stroke="{p["line"]}" stroke-width="1.5"/>')
            svg.add(f'<rect x="16" y="{H / 2 - 4:.1f}" width="8" height="8" rx="2" fill="{p["alt"]}"/>')
            svg.text(34, H / 2 + 4.5, label.upper(), "mono", 600, 12.5, p["fg"], spacing=1.4)
            ax = 34 + tw + 12
            svg.add((arrow_down if kind == "down" else arrow_out)(ax, H / 2 - 5.5, p["accent"], 11))
            svg.save(f"link-{key}-{mode}.svg")
    return widths


# --------------------------------------------------------------------------
# Section heads
# --------------------------------------------------------------------------
def build_heads():
    for key, (num, title, note) in CONTENT["heads"].items():
        for mode, p in PALETTES.items():
            W, H = 1000, 74
            svg = Svg(W, H, title)
            nw = svg.text(0, 44, f"[{num}]", "mono", 600, 15, p["alt"], spacing=1)
            svg.text(nw + 16, 46, title, "sans", 600, 30, p["fg"], spacing=-0.4)
            svg.text(W, 44, note, "mono", 500, 11, p["muted"], anchor="end", spacing=1.6)
            svg.add(f'<path d="M0 66 H{W}" stroke="{p["rule"]}" stroke-width="1.5" stroke-dasharray="2 5" '
                    f'stroke-linecap="round"/>')
            svg.save(f"head-{key}-{mode}.svg")


# --------------------------------------------------------------------------
# Results report
# --------------------------------------------------------------------------
def build_evals():
    e = CONTENT["evals"]
    rows = e["rows"]
    W, top, row_h = 1000, 70, 50
    H = top + row_h * len(rows) + 58
    label = "Results: " + "; ".join(f"{n} {r}, {d}" for n, r, d in rows)
    for mode, p in PALETTES.items():
        svg = Svg(W, H, label)
        svg.add(f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="16" fill="{p["surface"]}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>')
        svg.text(28, 40, e["command"], "mono", 500, 13, p["muted"])
        passed = f"{len(rows)} RESULTS"
        pw = measure(passed, "mono", 600, 11.5, 1.4)
        svg.add(f'<rect x="{W - 28 - pw - 22:.1f}" y="22" width="{pw + 22:.1f}" height="26" rx="13" '
                f'fill="{p["chip"]}" stroke="{p["line"]}"/>')
        svg.text(W - 28 - 11, 39.5, passed, "mono", 600, 11.5, p["accent"], anchor="end", spacing=1.4)
        for i, (name, result, detail) in enumerate(rows):
            y = top + i * row_h
            svg.add(f'<path d="M28 {y} H{W - 28}" stroke="{p["rule"]}" stroke-width="1"/>')
            mid = y + row_h / 2
            svg.add(check(30, mid - 7, p["accent"], 13))
            svg.text(58, mid + 5.5, name, "sans", 600, 16, p["fg"])
            svg.text(424, mid + 5.5, result, "mono", 700, 16, p["alt"], anchor="end")
            svg.text(452, mid + 5, detail, "sans", 400, 15, p["strong"])
        yb = top + row_h * len(rows)
        svg.add(f'<path d="M28 {yb} H{W - 28}" stroke="{p["rule"]}" stroke-width="1"/>')
        svg.text(28, yb + 34, e["note"], "sans", 400, 13.5, p["muted"])
        svg.save(f"results-{mode}.svg")


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------
def build_cards():
    W, pad = 1000, 32
    for idx, card in enumerate(CONTENT["cards"], 1):
        summary = wrap(card["summary"], "sans", 400, 16, W - pad * 2)
        sum_top = 120
        nodes_top = sum_top + 25 * (len(summary) - 1) + 32
        node_h = 58
        tags_y = nodes_top + node_h + 38
        H = tags_y + 28
        label = f"{card['title']}. {card['summary']}"
        for mode, p in PALETTES.items():
            svg = Svg(W, H, label)
            svg.add(f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="16" '
                    f'fill="{p["surface"]}" stroke="{p["line"]}" stroke-width="1.5"/>')
            num = f"{idx:02d}"
            nw = svg.text(pad, 44, num, "mono", 600, 12.5, p["accent"], spacing=1.4)
            svg.text(pad + nw + 14, 44, card["eyebrow"], "mono", 600, 12.5, p["alt"], spacing=1.8)
            svg.text(W - pad - 18, 44, card["cta"], "mono", 600, 11.5, p["muted"], anchor="end", spacing=1.4)
            svg.add(arrow_out(W - pad - 10, 35, p["accent"], 10))
            svg.text(pad, 82, card["title"], "sans", 700, 27, p["fg"], spacing=-0.4)
            for i, line in enumerate(summary):
                svg.text(pad, sum_top + i * 25, line, "sans", 400, 16, p["strong"])
            gap = 30
            n = len(card["nodes"])
            nw_ = (W - pad * 2 - gap * (n - 1)) / n
            for i, (title, sub) in enumerate(card["nodes"]):
                x = pad + i * (nw_ + gap)
                svg.add(f'<rect x="{x:.1f}" y="{nodes_top}" width="{nw_:.1f}" height="{node_h}" rx="10" '
                        f'fill="{p["chip"]}" stroke="{p["line"]}"/>')
                svg.text(x + 14, nodes_top + 25, title, "sans", 600, 15, p["fg"])
                svg.text(x + 14, nodes_top + 44, sub, "mono", 400, 11.5, p["muted"])
                if i < n - 1:
                    svg.add(arrow_right(x + nw_ + 6, x + nw_ + gap - 6, nodes_top + node_h / 2, p["accent"]))
            tags = "  ·  ".join(card["tags"])
            svg.text(pad, tags_y, tags, "mono", 500, 12, p["muted"], spacing=0.3)
            svg.save(f"work-{card['key']}-{mode}.svg")


# --------------------------------------------------------------------------
# Toolkit grid
# --------------------------------------------------------------------------
def build_toolkit():
    W, cols, pad, gap = 1000, 3, 28, 28
    col_w = (W - pad * 2 - gap * (cols - 1)) / cols
    chip_h, chip_gap = 28, 8

    def layout(items, width):
        rows, x, placed = 0, 0.0, []
        for item in items:
            w = measure(item, "sans", 500, 13.5) + 22
            if x and x + w > width:
                rows, x = rows + 1, 0.0
            placed.append((item, x, rows, w))
            x += w + chip_gap
        return placed, rows + 1

    # Groups fill a 3-column grid; a group left alone on the last row spans the full width.
    items_ = CONTENT["toolkit"]
    grid_rows = [items_[r:r + cols] for r in range(0, len(items_), cols)]
    full_w = W - pad * 2
    rows_laid = [[(name, *layout(items, full_w if len(row) == 1 else col_w)) for name, items in row]
                 for row in grid_rows]
    row_heights = [max(30 + n * (chip_h + chip_gap) for _, _, n in row) for row in rows_laid]
    H = pad + sum(row_heights) + 26 * (len(row_heights) - 1) + pad - 6
    label = "Toolkit. " + ". ".join(f"{n}: {', '.join(i)}" for n, i in CONTENT["toolkit"])
    for mode, p in PALETTES.items():
        svg = Svg(W, H, label)
        svg.add(f'<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="16" fill="{p["surface"]}" '
                f'stroke="{p["line"]}" stroke-width="1.5"/>')
        y0 = pad
        for r, rh in enumerate(row_heights):
            for c, (name, placed, _) in enumerate(rows_laid[r]):
                gx = pad + c * (col_w + gap)
                svg.text(gx, y0 + 12, name.upper(), "mono", 600, 11.5, p["alt"], spacing=1.6)
                for item, x, row, w in placed:
                    yy = y0 + 26 + row * (chip_h + chip_gap)
                    svg.add(f'<rect x="{gx + x:.1f}" y="{yy:.1f}" width="{w:.1f}" height="{chip_h}" rx="8" '
                            f'fill="{p["chip"]}" stroke="{p["line"]}"/>')
                    svg.text(gx + x + 11, yy + 18.5, item, "sans", 500, 13.5, p["fg"])
            y0 += rh + 26
        svg.save(f"toolkit-{mode}.svg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print("Building assets/")
    build_hero()
    widths = build_links()
    build_heads()
    build_evals()
    build_cards()
    build_toolkit()
    print("Link widths for README:", widths)
