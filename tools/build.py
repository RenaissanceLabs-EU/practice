#!/usr/bin/env python3
"""Build the Open Environments Index: a static site from data/hub.json (Hub metadata),
data/records/*.json (per-environment records) and data/isced_f.json (the taxonomy)."""
import csv, glob, html, json, math, os, re, shutil
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://practice.renaissancelabs.eu"
e = lambda s: html.escape(str(s if s is not None else ""), quote=True)

REWARD = {"tests": "Hidden tests", "exact-match": "Exact match", "programmatic": "Programmatic check",
          "state-check": "State check", "llm-judge": "LLM judge", "rubric": "Rubric",
          "learned-model": "Learned scorer", "mixed": "Mixed", "unknown": "Not stated"}
REWARD_HELP = {"tests": "Tests run inside the sandbox decide the score.",
               "exact-match": "The answer is compared with a stored reference.",
               "programmatic": "A deterministic checker script scores the output.",
               "state-check": "The final state of the app, database or simulator is inspected.",
               "llm-judge": "A language model grades the result.",
               "rubric": "The result is scored against a rubric with several criteria.",
               "learned-model": "A trained scoring model gives the reward.",
               "mixed": "Several reward sources are combined.",
               "unknown": "The card does not say how the reward is computed."}
SIGNAL = {"binary": "Pass or fail", "graded": "Graded, 0 to 1", "dense": "Dense, per step", "unknown": "Not stated"}
IFACE = {"terminal": "Terminal", "code-exec": "Code execution", "tool-calls": "Tool calls", "gui-desktop": "Desktop GUI",
         "browser": "Browser", "text": "Text only", "multi-agent": "Multi-agent", "simulator": "Simulator", "robotics": "Robotics"}
HORIZON = {"single-turn": "Single turn", "multi-step": "Multi-step", "long-horizon": "Long horizon", "unknown": "Not stated"}
FW = {"harbor": ("Harbor", "https://github.com/harbor-framework/harbor"),
      "verifiers": ("Verifiers", "https://github.com/PrimeIntellect-ai/verifiers"),
      "openenv": ("OpenEnv", "https://github.com/meta-pytorch/OpenEnv"),
      "nemo-gym": ("NeMo Gym", "https://github.com/NVIDIA-NeMo/Gym"),
      "agentenv": ("AgentEnv", None), "hud": ("HUD", None), "other": ("Other", None)}

LANG = {"hi": "Hindi", "sa": "Sanskrit", "und": "Not stated", "en": "English", "sv": "Swedish", "de": "German", "fr": "French", "es": "Spanish", "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "ru": "Russian", "pt": "Portuguese", "it": "Italian", "fi": "Finnish", "da": "Danish", "no": "Norwegian", "nl": "Dutch", "multi": "Multilingual", "multilingual": "Multilingual"}

# ---------- load ----------
tax = json.load(open(f"{ROOT}/data/isced_f.json"))
DET, NAR, BRO = {}, {}, {}
for b in tax["broad"]:
    BRO[b["code"]] = b
    for n in b["narrow"]:
        NAR[n["code"]] = n
        for d in n["detailed"]:
            DET[d["code"]] = d
hub = {(h["kind"], h["id"]): h for h in json.load(open(f"{ROOT}/data/hub.json"))}
records = []
for p in sorted(glob.glob(f"{ROOT}/data/records/*.json")):
    records += json.load(open(p))
overrides = {}
if os.path.exists(f"{ROOT}/data/overrides.json"):
    overrides = {o["id"]: o for o in json.load(open(f"{ROOT}/data/overrides.json"))}

def slug(kind, rid):
    s = re.sub(r"[^a-z0-9]+", "-", rid.replace("/", "--").lower().replace("--", "§")).strip("-").replace("§", "--")
    return ("space--" if kind == "spaces" else "") + s

def tagval(tags, prefix):
    for t in tags:
        if t.startswith(prefix): return t[len(prefix):]
    return ""

envs, dropped = [], []
seen = set()
for r in records:
    r = {**r, **overrides.get(r["id"], {})}
    key = (r["kind"], r["id"])
    r["hub_id"] = r.get("hub_id") or r["id"]
    h = hub.get((r["kind"], r["hub_id"]))
    if not h or key in seen: continue
    seen.add(key)
    if not r.get("is_environment", True) or r.get("_remove"):
        dropped.append(r["id"]); continue
    if r.get("isced") not in DET: r["isced"] = "0021"
    if r.get("isced2") not in DET or r.get("isced2") == r["isced"]: r["isced2"] = None
    rw = r.get("reward") or {}
    if rw.get("type") not in REWARD: rw["type"] = "unknown"
    if rw.get("signal") not in SIGNAL: rw["signal"] = "unknown"
    rw["note"] = (rw.get("note") or "").strip()
    r["reward"] = rw
    tags = h.get("tags", [])
    fws = [f for f in (r.get("frameworks") or []) if f in FW]
    for f in ("harbor", "verifiers", "openenv", "nemo-gym"):
        if f in tags and f not in fws: fws.append(f)
    if r["kind"] == "spaces" and "openenv" not in fws: fws.insert(0, "openenv")
    r["frameworks"] = [f for f in fws if f != "other"] or []
    r["interface"] = [i for i in (r.get("interface") or []) if i in IFACE]
    if r.get("horizon") not in HORIZON: r["horizon"] = "unknown"
    r["tasks"] = r["tasks"] if isinstance(r.get("tasks"), int) and r["tasks"] > 0 else None
    r["good_for"] = [g.strip().rstrip(".") for g in (r.get("good_for") or []) if g and g.strip()][:3]
    r["run"] = (r.get("run") or "").strip() or None
    r["owner"], r["repo"] = r["id"].split("/", 1)
    r["name"] = (r.get("name") or r["repo"]).strip()
    r["summary"] = (r.get("summary") or "").strip()
    r["slug"] = slug(r["kind"], r["id"])
    r["url"] = f"/env/{r['slug']}/"
    r["house"] = bool(r.get("house"))
    r["languages"] = list(dict.fromkeys(str(x).strip().lower() for x in (r.get("languages") or []) if str(x).strip())) or ["und"]
    r["hub"] = r.get("hub_url") or f"https://huggingface.co/{'datasets' if r['kind']=='datasets' else 'spaces'}/{r['hub_id']}" + (f"/tree/main/{r['hub_path']}" if r.get("hub_path") else "")
    r["downloads"] = h.get("downloads") or 0
    r["likes"] = h.get("likes") or 0
    r["updated"] = (h.get("lastModified") or "")[:10]
    r["created"] = (h.get("createdAt") or "")[:10]
    r["gated"] = bool(h.get("gated"))
    r["licence"] = tagval(tags, "license:") or ((h.get("cardData") or {}).get("license") if isinstance((h.get("cardData") or {}).get("license"), str) else "") or ""
    r["size"] = tagval(tags, "size_categories:")
    envs.append(r)
envs.sort(key=lambda r: (-r["downloads"], r["id"].lower()))
house = sorted([r for r in envs if r["house"]], key=lambda r: r["isced"])

by_det = {c: [] for c in DET}
for r in envs: by_det[r["isced"]].append(r)
MAXN = max(len(v) for v in by_det.values())
def weight(n): return 0 if not n else round(14 + 62 * math.log1p(n) / math.log1p(MAXN))
covered = sum(1 for v in by_det.values() if v)
publishers = len({r["owner"] for r in envs})
TODAY = date.today().isoformat()
import hashlib
VER = hashlib.md5(open(f"{ROOT}/styles.css","rb").read() + open(f"{ROOT}/app.js","rb").read()).hexdigest()[:8]

# ---------- pieces ----------
def num(n):
    if n is None: return ""
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 10_000: return f"{n/1000:.0f}k"
    return f"{n:,}"

THEME_BOOT = "<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>"
MOON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M13.5 9.6A5.8 5.8 0 0 1 6.4 2.5a5.8 5.8 0 1 0 7.1 7.1z"/></svg>'

def page(path, title, desc, body, current=""):
    nav = [("/", "Index", "home"), ("/fields/", "Fields", "fields"), ("/about/", "About", "about")]
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{h}"{cur if k == current else ""}>{t}</a>' for h, t, k in nav)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:site_name" content="Open Environments Index by Renaissance Labs">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{SITE}/assets/social-preview.png">
<meta property="og:image:secure_url" content="{SITE}/assets/social-preview.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Open Environments Index by Renaissance Labs. A place for models to practice human work, illustrated by a map of fields.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE}/assets/social-preview.png">
<meta name="twitter:image:alt" content="Open Environments Index by Renaissance Labs. A place for models to practice human work.">
<link rel="icon" href="/assets/favicon.png">
<link rel="preload" href="/assets/fonts/fraunces-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
{THEME_BOOT}
<link rel="stylesheet" href="/styles.css?v={VER}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="bar">
  <a class="brand" href="https://renaissancelabs.eu/"><img src="/assets/mark.png" alt="" width="28" height="28"><span>Renaissance Labs</span></a>
  <nav aria-label="Main">{links}<a class="ext" href="https://labs.renaissancelabs.eu/">Atlas</a><a class="ext" href="https://learn.renaissancelabs.eu/">Learn</a><button class="theme" id="theme" aria-label="Switch between light and dark">{MOON}</button></nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot wrap">
  <p class="brand"><img src="/assets/mark.png" alt="" width="22" height="22"> Renaissance Labs · Open Environments Index · Made in Europe</p>
  <p class="foot-links"><a href="/environments.csv">Download data (CSV)</a><a href="/data/environments.json">JSON</a><a href="/llms.txt">llms.txt</a><a href="https://discord.gg/6JUezWZbAm">Suggest a correction</a><a href="https://huggingface.co/RenaissanceLabsEU">Hugging Face</a></p>
</footer>
<script src="/app.js?v={VER}" defer></script>
</body>
</html>
"""
    out = f"{ROOT}{path}index.html" if path.endswith("/") else f"{ROOT}{path}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(doc)

def card(r, attrs=True):
    d = DET[r["isced"]]
    pills = []
    if r["tasks"]: pills.append(f'<span class="pill">{num(r["tasks"])} tasks</span>')
    if r["reward"]["type"] != "unknown": pills.append(f'<span class="pill rw">{REWARD[r["reward"]["type"]]}</span>')
    pills += [f'<span class="pill fw">{f}</span>' for f in r["frameworks"][:3]]
    pills += [f'<span class="pill lang" lang="en">{e(LANG.get(code, code))}</span>' for code in r["languages"]]
    data = ""
    if attrs:
        s = " ".join([r["name"], r["id"], r["summary"], r.get("task_type") or "", d["name"], BRO[r["isced"][:2]]["name"], " ".join(r["good_for"]), " ".join(LANG.get(code, code) for code in r["languages"])]).lower()
        data = (f' data-f="{r["isced"]}" data-f2="{r["isced2"] or ""}" data-fw="{" ".join(r["frameworks"])}" data-lang="{e(" ".join(r["languages"]))}" data-rw="{r["reward"]["type"]}"'
                f' data-if="{" ".join(r["interface"])}" data-hz="{r["horizon"]}" data-run="{1 if r["run"] else 0}" data-ev="{1 if r.get("validated") else 0}"'
                f' data-house="{1 if r["house"] else 0}" data-dl="{r["downloads"]}" data-likes="{r["likes"]}" data-upd="{r["updated"]}" data-tasks="{r["tasks"] or 0}" data-name="{e(r["name"].lower())}" data-s="{e(s)}"')
    kind = "Space · " if r["kind"] == "spaces" else ""
    if r["house"]: pills.insert(0, '<span class="pill house">Renaissance Labs</span>')
    return (f'<a class="card b{r["isced"][:2]}" href="{r["url"]}"{data}>'
            f'<div class="top"><span class="fld"><i>{r["isced"]}</i>{e(d["name"])}</span><span>{e(r.get("task_type") or "")}</span></div>'
            f'<h3>{e(r["name"])}</h3><p class="by">{kind}{e("Renaissance Labs · " + r["env_name"] if r["house"] else r["id"])}</p>'
            f'<p class="sum">{e(r["summary"])}</p>'
            f'<div class="facts">{"".join(pills)}</div>'
            + (f'<div class="meta"><span>{len(r.get("families") or [])} task families · oracle-verified</span><span>{r["updated"]}</span></div></a>' if r["house"] else
             f'<div class="meta"><span><b>{num(r["downloads"])}</b> downloads · <b>{num(r["likes"])}</b> likes</span><span>{r["updated"]}</span></div></a>'))

def codeblock(text):
    lines = []
    for ln in text.split("\n"):
        lines.append(f'<span class="cm">{e(ln)}</span>' if ln.lstrip().startswith("#") else e(ln))
    return f'<div class="codebox"><button class="copy" type="button">Copy</button><pre>{chr(10).join(lines)}</pre></div>'

def house_section():
    if not house: return ""
    fields = len({r["isced"] for r in house})
    opened = len({r["isced"] for r in house if all(x["house"] for x in by_det[r["isced"]])})
    return f"""<section class="house-sec" id="ours">
    <div class="house-head"><div><p class="eyebrow">Built by Renaissance Labs</p><h2>Environments for the empty fields</h2>
    <p>{len(house)} environments and {sum(r["tasks"] or 0 for r in house):,} tasks across {fields} fields, {opened} of which had no open environment before. Each task ships as a Harbor directory with a deterministic verifier and a reference solution, runs offline in a small container, and gives a graded reward.</p></div>
    <a class="btn ghost" href="https://huggingface.co/datasets/RenaissanceLabsEU/practice">The Practice dataset</a></div>
    <div class="grid">{"".join(card(r, False) for r in house)}</div></section>"""

# ---------- home ----------
def build_home():
    rows = []
    for b in tax["broad"]:
        dets = [d for n in b["narrow"] for d in n["detailed"]]
        n_b = sum(len(by_det[d["code"]]) for d in dets)
        tiles = []
        for d in dets:
            n = len(by_det[d["code"]])
            if n:
                tiles.append(f'<button type="button" class="tile" style="--w:{weight(n)}" data-code="{d["code"]}" data-name="{e(d["name"])}" aria-pressed="false" title="{n} environment{"s" if n != 1 else ""} in {e(d["name"])}">'
                             f'<span class="tc">{d["code"]}<b>{n}</b></span><span class="tn">{e(d["name"])}</span></button>')
            else:
                tiles.append(f'<div class="tile empty" title="No open environment yet"><span class="tc">{d["code"]}</span><span class="tn">{e(d["name"])}</span></div>')
        rows.append(f'<div class="row b{b["code"]}"><a class="row-label" href="/fields/{b["code"]}/"><span class="code">{b["code"]}</span><span class="nm">{e(b["short"])}</span>'
                    f'<span class="ct">{n_b} environment{"s" if n_b != 1 else ""}</span></a><div class="tiles">{"".join(tiles)}</div></div>')
    empties = "".join(f'<li class="b{c[:2]}"><i>{c}</i>{e(d["name"])}</li>' for c, d in DET.items() if not by_det[c])
    def opts(pairs): return "".join(f'<option value="{v}">{e(t)}</option>' for v, t in pairs)
    def used(key, labels, multi=False):
        cnt = {}
        for r in envs:
            for v in (r[key] if multi else [r[key]]): cnt[v] = cnt.get(v, 0) + 1
        return [(k, f"{labels[k] if not isinstance(labels[k], tuple) else labels[k][0]} ({cnt[k]})") for k in labels if cnt.get(k)]
    rwcnt = {}
    for r in envs: rwcnt[r["reward"]["type"]] = rwcnt.get(r["reward"]["type"], 0) + 1
    body = f"""<section class="intro">
  <p class="eyebrow">Open Environments Index</p>
  <h1>Every field of human work, as a place for models to <em>practice</em>.</h1>
  <p class="lede">A catalogue of the open reinforcement-learning environments for language-model agents, arranged by the same fields UNESCO uses to classify what people study. For each one: what the agent does, how it is rewarded, and how to run it.</p>
  <div class="stats">
    <div class="stat"><b>{len(envs)}</b><span>environments</span></div>
    <div class="stat"><b>{covered}<small> / {len(DET)}</small></b><span>fields covered</span></div>
    <div class="stat"><b>{publishers}</b><span>publishers</span></div>
    <div class="stat"><b>{sum(1 for r in envs if r["run"])}</b><span>with a run command</span></div>
  </div>
</section>
<div class="wrap">
  <div class="chart-head">
    <div><h2>The chart of fields</h2>
    <p>The {len(tax["broad"])} broad and {len(DET)} detailed fields of ISCED-F 2013, the international classification of fields of education and training. A darker tile holds more environments. A dashed tile has none yet. Select a tile to see what is in it.</p></div>
    <div class="scale" aria-hidden="true"><i class="e"></i>none <i style="opacity:.25"></i><i style="opacity:.5"></i><i style="opacity:.75"></i><i></i> more</div>
  </div>
  <div class="chart" id="chart">{"".join(rows)}</div>
  <div class="gap">
    <div><h3>{len(DET) - covered} fields have no open environment</h3><p>Most of what exists teaches models to write software and operate computers. Health care, teaching, agriculture, the trades and most of the humanities are still almost empty.</p></div>
    <ul>{empties}</ul>
  </div>

  {house_section()}
  <div class="dir-head" id="directory"><h2>All environments</h2><span class="n" id="count">{len(envs)} environments</span></div>
  <div class="filters"><div class="filters-in">
    <label class="search"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg><input id="q" type="search" placeholder="Search by name, publisher, task or field" aria-label="Search environments" autocomplete="off"></label>
    <select class="sel" data-k="b" aria-label="Broad field"><option value="">All fields</option>{opts((b["code"], f'{b["code"]} {b["short"]}') for b in tax["broad"] if any(by_det[d["code"]] for n in b["narrow"] for d in n["detailed"]))}</select>
    <select class="sel" data-k="fw" aria-label="Framework"><option value="">Any framework</option>{opts(used("frameworks", FW, True))}</select>
    <select class="sel" data-k="rw" aria-label="Reward"><option value="">Any reward</option>{opts(used("reward_type", REWARD))}</select>
    <select class="sel" data-k="if" aria-label="Interface"><option value="">Any interface</option>{opts(used("interface", IFACE, True))}</select>
    <select class="sel" data-k="lang" aria-label="Task language"><option value="">Any language</option>{opts((code, LANG.get(code, code)) for code in sorted({code for r in envs for code in r["languages"]}))}</select>
    <select class="sel" data-k="hz" aria-label="Horizon"><option value="">Any horizon</option>{opts(used("horizon", HORIZON))}</select>
    <label class="chk"><input type="checkbox" data-k="run">Run command</label>
    <label class="chk"><input type="checkbox" data-k="ev">Evidence reported</label>
    <label class="chk"><input type="checkbox" data-k="house">By Renaissance Labs</label>
    <select class="sel" id="sort" aria-label="Sort"><option value="dl">Most downloaded</option><option value="likes">Most liked</option><option value="upd">Recently updated</option><option value="tasks">Most tasks</option><option value="name">A to Z</option></select>
    <button class="clear" id="clear" type="button" hidden>Clear</button>
  </div></div>
  <p class="active-field" id="active-field" hidden></p>
  <div class="grid" id="grid">{"".join(card(r) for r in envs)}</div>
  <p class="none" id="none" hidden>No environment matches. Try fewer filters.</p>
  <button class="btn ghost more" id="more" type="button" hidden>Show more</button>
</div>"""
    page("/", "Open Environments Index · RL environments for language-model agents, by field",
         f"A catalogue of {len(envs)} open RL environments for language-model agents, arranged by the ISCED-F fields of education. For each: the task, the reward and how to run it.", body, "home")

# ---------- environment pages ----------
def run_section(r):
    steps = []
    if r["house"]:
        t = f'tasks/{r["env_name"]}/{r["first_task"]}'
        steps = [("Get the tasks", "this environment is one subset of the Practice dataset", f'hf download RenaissanceLabsEU/practice --repo-type dataset --include "tasks/{r["env_name"]}/*" --local-dir Practice\ncd Practice', "Leave out <code>--include</code> to fetch every environment and the generators."),
                 ("Check one task by hand", "build it, run the reference solution, run the verifier",
                  f"docker build -t practice-task {t}/environment\ndocker run --rm --network none -v $PWD/{t}/tests:/tests:ro -v $PWD/{t}/solution:/solution:ro practice-task \\\n  bash -c 'bash /solution/solve.sh; bash /tests/test.sh; cat /logs/verifier/reward.txt'",
                  "Prints 1.0. Leave out <code>bash /solution/solve.sh;</code> to see the reward for doing nothing, which is 0."),
                 ("Run it with an agent", "each task folder is a Harbor task", f"harbor run --path tasks/{r['env_name']} --agent oracle\n# then your own agent and model, for example:\n# harbor run --path tasks/{r['env_name']} --agent terminus-2 --model <your-model>",
                  "The agent works in <code>/app</code> and writes <code>/app/answer.json</code>. The verifier writes the reward to <code>/logs/verifier/reward.txt</code>. Tasks tagged <code>eval</code> use seeds the <code>train</code> tasks never see."),
                 ("Make more tasks", "the generators are seeded and unlimited; needs the full download", f"python3 tools/export.py {r['env_name'].replace('-', '_')}", "")]
        out = [f'<div class="step"><p class="step-h"><b>{i}. {t_}</b><span>{sub}</span></p>{codeblock(code)}{f"<p class=note>{note}</p>" if note else ""}</div>' for i, (t_, sub, code, note) in enumerate(steps, 1)]
        return "".join(out) + '<p class="note">Needs Docker. The Harbor commands follow the framework\'s usual pattern and were not run by us; the Docker check above was.</p>'
    name = r["hub_id"].split("/")[-1]
    if r["run"]:
        steps.append(("From the card", "copied from the publisher's own instructions", r["run"], ""))
    if r["kind"] == "datasets":
        gate = "This repository is gated: request access on the Hub and log in with <code>hf auth login</code> first." if r["gated"] else ""
        steps.append(("Get the files", "the whole repository, to a local folder", f"hf download {r['hub_id']} --repo-type dataset" + (f" --include \"{r['hub_path']}/*\"" if r.get("hub_path") else "") + f" --local-dir {name}", gate))
        if "harbor" in r["frameworks"] and not r.get("curated"):
            steps.append(("Check it with Harbor", "common pattern, not from this card",
                          f"# the oracle agent runs the reference solution, so no model is called\nharbor run --repo https://huggingface.co/datasets/{r['hub_id']} --agent oracle",
                          "If every task passes, the environment works on your machine. Then swap in your own agent and model. Some repositories keep the tasks in a subfolder; the card says where."))
        if "openenv" in r["frameworks"] and "harbor" in r["frameworks"]:
            steps.append(("Serve it for training with OpenEnv", "common pattern, not from this card",
                          f"pip install \"openenv[harbor]\"\nopenenv harbor serve --dataset {r['id']} --llm-url http://127.0.0.1:8000/v1 --model <your-model>", ""))
    else:
        steps.append(("Run the Space locally", "every Space is a Docker image or app you can clone", f"git clone https://huggingface.co/spaces/{r['id']}\ncd {name}", "The Space also runs live on the Hub; open it to see the API it serves."))
    out = []
    for i, (t, sub, code, note) in enumerate(steps, 1):
        out.append(f'<div class="step"><p class="step-h"><b>{i}. {t}</b><span>{sub}</span></p>{codeblock(code)}{f"<p class=note>{note}</p>" if note else ""}</div>')
    docs = [f'<a href="{FW[f][1]}">{FW[f][0]}</a>' for f in r["frameworks"] if FW[f][1]]
    tail = f'<p class="note">Framework documentation: {", ".join(docs)}.{" Needs: " + e(r["needs"]) + "." if r.get("needs") else ""}</p>' if docs or r.get("needs") else ""
    if not docs and r.get("needs"): tail = f'<p class="note">Needs: {e(r["needs"])}.</p>'
    return "".join(out) + tail

def build_env(r):
    d, b = DET[r["isced"]], BRO[r["isced"][:2]]
    rw = r["reward"]
    side = [("Field", f'<a href="/fields/{b["code"]}/#f{d["code"]}">{d["code"]} {e(d["name"])}</a>' +
             (f'<br><a href="/fields/{r["isced2"][:2]}/#f{r["isced2"]}">{r["isced2"]} {e(DET[r["isced2"]]["name"])}</a>' if r["isced2"] else ""))]
    if r.get("task_type"): side.append(("Task", e(r["task_type"].capitalize())))
    if r["tasks"]: side.append(("Tasks", f'{r["tasks"]:,}'))
    if r["interface"]: side.append(("Interface", "".join(f'<span class="pill">{IFACE[i]}</span>' for i in r["interface"])))
    side.append(("Horizon", HORIZON[r["horizon"]]))
    if r["frameworks"]: side.append(("Frameworks", "".join(f'<span class="pill fw">{f}</span>' for f in r["frameworks"])))
    if r.get("languages"): side.append(("Task language", e(", ".join(LANG.get(code, code) for code in r["languages"]))))
    side.append(("Licence", e(r["licence"]) if r["licence"] else "Not stated"))
    if r["house"]: side.append(("Task families", "".join(f'<span class="pill fw">{f}</span>' for f in r.get("families") or [])))
    else: side.append(("On the Hub", f'{num(r["downloads"])} downloads · {num(r["likes"])} likes' + (" · gated" if r["gated"] else "")))
    side.append(("Updated", r["updated"] + (f' (created {r["created"]})' if r["created"] else "")))
    links = [f'<a href="{e(r["hub"])}">{"Task folder" if r["house"] else "Hub repository"}</a>']
    if r.get("paper"): links.append(f'<a href="{e(r["paper"])}">Paper</a>')
    if r.get("code"): links.append(f'<a href="{e(r["code"])}">Code</a>')
    side.append(("Links", " · ".join(links)))
    sidehtml = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in side)
    rel = [x for x in by_det[r["isced"]] if x is not r][:6]
    if len(rel) < 3:
        rel += [x for x in envs if x["isced"][:2] == r["isced"][:2] and x is not r and x not in rel][:6 - len(rel)]
    good = f'<section class="sec"><h2>Good for</h2><ul class="goodfor">{"".join(f"<li>{e(g)}</li>" for g in r["good_for"])}</ul></section>' if r["good_for"] else ""
    ev = f'<section class="sec"><h2>Evidence</h2><p class="evidence">{e(r["validated"])}</p><p class="note">{"Checked by our own test suite. No model has been trained on these tasks yet, so there is no evidence of training lift." if r["house"] else "As reported by the publisher. We have not reproduced it."}</p></section>' if r.get("validated") else ""
    body = f"""<div class="wrap b{b["code"]}">
  <p class="crumbs"><a href="/">Index</a> / <a href="/fields/{b["code"]}/">{e(b["short"])}</a> / <a href="/fields/{b["code"]}/#f{d["code"]}">{e(d["name"])}</a></p>
  <header class="env-head">
    <a class="fldchip" href="/fields/{b["code"]}/#f{d["code"]}"><i>{d["code"]}</i><span>{e(d["name"])}</span></a>
    <h1>{e(r["name"])}</h1>
    <p class="id">{"Space · " if r["kind"] == "spaces" else ""}{e("RenaissanceLabsEU/practice · " + r["env_name"] if r["house"] else r["id"])}</p>
    <p class="lede">{e(r["summary"])}</p>
    <p class="actions"><a class="btn" href="{e(r["hub"])}">{"Open on Hugging Face"}</a><a class="btn ghost" href="#run">How to run it</a></p>
  </header>
  <div class="env">
    <div>
      {good}
      <section class="sec"><h2>Reward</h2>
        <dl class="reward"><div><dt>How it is scored</dt><dd>{REWARD[rw["type"]]}</dd></div><div><dt>Signal</dt><dd>{SIGNAL[rw["signal"]]}</dd></div></dl>
        <p>{e(rw["note"]) if rw["note"] else REWARD_HELP[rw["type"]]}</p>
      </section>
      <section class="sec" id="run"><h2>How to run it</h2>{run_section(r)}</section>
      {ev}
    </div>
    <aside><dl class="side">{sidehtml}</dl>
    <p class="prov">{"This entry comes from a hand-kept list of terminal and software-engineering environments, not from the Hub tag." if r.get("curated") else "Built and verified by Renaissance Labs." if r["house"] else "This record was drawn from the publisher's card on " + TODAY + "."} The card is the authority; <a href="/about/#method">how records are made</a>.</p></aside>
  </div>
  {f'<section class="related"><h2>More in this field</h2><div class="grid">{"".join(card(x, False) for x in rel)}</div></section>' if rel else ""}
</div>"""
    page(r["url"], f'{r["name"]} · {d["name"]} · Open Environments Index', r["summary"] or f'RL environment {r["id"]}', body)

# ---------- field pages ----------
def build_fields():
    navs = []
    for b in tax["broad"]:
        dets = [d for n in b["narrow"] for d in n["detailed"]]
        n_b = sum(len(by_det[d["code"]]) for d in dets)
        cov = sum(1 for d in dets if by_det[d["code"]])
        bars = "".join(f'<i style="--w:{weight(len(by_det[d["code"]]))}"></i>' for d in dets)
        navs.append(f'<a class="b{b["code"]}" href="/fields/{b["code"]}/"><span class="code">{b["code"]}</span><span class="nm">{e(b["name"])}</span>'
                    f'<span class="ct">{n_b} environment{"s" if n_b != 1 else ""} · {cov} of {len(dets)} fields covered</span><span class="bar2">{bars}</span></a>')
        secs = []
        for n in b["narrow"]:
            ds = []
            for d in n["detailed"]:
                items = by_det[d["code"]]
                also = [x for x in envs if x["isced2"] == d["code"]]
                inner = f'<div class="grid">{"".join(card(x, False) for x in items)}</div>' if items else '<p class="nothing">No open environment in this field yet.</p>'
                if also:
                    inner += '<p class="note">Also touches this field: ' + ", ".join(f'<a href="{x["url"]}">{e(x["name"])}</a>' for x in also[:12]) + ".</p>"
                ds.append(f'<section class="detail" id="f{d["code"]}"><h3><i>{d["code"]}</i>{e(d["name"])}<span>{len(items) or "none"}</span></h3>{inner}</section>')
            secs.append(f'<section class="narrow"><h2><i>{n["code"]}</i>{e(n["name"])}</h2>{"".join(ds)}</section>')
        body = f"""<div class="wrap b{b["code"]}">
  <p class="crumbs"><a href="/">Index</a> / <a href="/fields/">Fields</a></p>
  <header class="page-head"><p class="eyebrow">ISCED-F {b["code"]}</p><h1>{e(b["name"])}</h1>
  <p class="lede">{n_b} open environment{"s" if n_b != 1 else ""} across {cov} of the {len(dets)} detailed fields in this group.</p></header>
  {"".join(secs)}
</div>"""
        page(f'/fields/{b["code"]}/', f'{b["name"]} · RL environments · Open Environments Index', f'{n_b} open RL environments for language-model agents in {b["name"].lower()} (ISCED-F {b["code"]}).', body, "fields")
    body = f"""<div class="wrap">
  <header class="page-head"><p class="eyebrow">ISCED-F 2013</p><h1>Fields</h1>
  <p class="lede">Every environment is filed under one detailed field of ISCED-F 2013, by the subject a person would have studied to do the work. The bars show each detailed field in the group; a pale bar is an empty field.</p></header>
  <div class="fieldnav">{"".join(navs)}</div>
</div>"""
    page("/fields/", "Fields · Open Environments Index", "RL environments for language-model agents, browsed by the ISCED-F 2013 fields of education and training.", body, "fields")

# ---------- about ----------
def build_about():
    rw = {}
    for r in envs: rw[r["reward"]["type"]] = rw.get(r["reward"]["type"], 0) + 1
    rows = "".join(f"<tr><td>{REWARD[k]}</td><td>{REWARD_HELP[k]}</td><td>{rw.get(k, 0)}</td></tr>" for k in REWARD)
    n_spaces = sum(1 for r in envs if r["kind"] == "spaces")
    n_cur = sum(1 for r in envs if r.get("curated"))
    body = f"""<div class="wrap">
  <header class="page-head"><p class="eyebrow">About</p><h1>What this is, and how it is made</h1>
  <p class="lede">An index of open RL environments for language-model agents, so that anyone training a model can find a place to practice a skill, see how it is rewarded, and run it.</p></header>
  <div class="prose">
  <h2>What counts as an environment</h2>
  <p>A set of tasks an agent can attempt, with a way to score each attempt. On the Hugging Face Hub an environment is a dataset repository tagged <code>rl-environment</code>, as described in the Hub's <a href="https://huggingface.co/blog/rl-environments">RL environments post</a>. The Hub hosts the tasks; a framework such as Harbor, Verifiers, OpenEnv or NeMo Gym supplies the runtime and runs the verifier.</p>
  <p>The index holds {len(envs)} entries as of {TODAY}: {len(envs) - n_spaces - n_cur} dataset repositories with that tag, {n_cur} further tasksets from a hand-kept list of terminal and software-engineering environments that do not carry the tag, and {n_spaces} live Spaces with the same tag and at least three likes. Several thousand more Spaces carry the tag, most of them entries to one hackathon in spring 2026; they are left out until they attract use. Repositories that carry the tag but hold only trajectories, checkpoints, slides or demos are left out too ({len(dropped)} so far).</p>
  <h2>Why ISCED-F</h2>
  <p>Environments need one system of domains that already exists, covers all of human work and study, and is not ours. <a href="{tax["url"]}">ISCED-F 2013</a> is UNESCO's classification of fields of education and training: 11 broad fields, 29 narrow and 80 detailed. Ministries, Eurostat and the OECD already use it to count who studies what. Filing environments in it makes the gaps visible: a field with graduates and no environment is a field models have nowhere to practice.</p>
  <p>Each environment gets one detailed field, chosen by the subject of the task and not by the tool. A terminal task about genomics is biology. Where a second field fits, it is recorded and shown on the field page. Some conventions: general shell and operations work is 0612, software development is 0613, using applications as an end user is 0611, data analysis is 0542, text exercises with no subject are 0021, and games are 1015.</p>
  <h2 id="method">How records are made</h2>
  <p>Downloads, likes, licence, dates and tags come from the Hub API. The summary, field, reward, interface, task count and run command are read from each publisher's card by a language model working to a fixed schema, with instructions to leave a value empty when the card does not state it. Run commands marked "From the card" are copied verbatim. Commands marked "common pattern" are the usual way to run that framework and were not taken from the card.</p>
  <p>These records have been spot-checked, not audited line by line, and none of the environments has been run by us. The card is the authority. If a record is wrong, <a href="https://discord.gg/6JUezWZbAm">tell us</a> and it will be corrected.</p>
  <h2>Reward types</h2>
  <table class="t"><thead><tr><th>Type</th><th>Meaning</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Licence</h2>
  <p>The index data is CC BY 4.0; please credit "Open Environments Index by Renaissance Labs". Each environment keeps its own licence, shown on its page.</p>
  </div>
</div>"""
    page("/about/", "About · Open Environments Index", "What the Open Environments Index covers, why it uses ISCED-F 2013, and how each record is made.", body, "about")

# ---------- data files ----------
def build_data():
    keys = ["id", "kind", "name", "summary", "isced", "isced2", "task_type", "tasks", "reward_type", "reward_signal", "reward_note",
            "interface", "horizon", "frameworks", "run", "needs", "good_for", "validated", "languages", "licence", "downloads", "likes",
            "updated", "created", "gated", "paper", "code", "hub", "page"]
    rows = []
    for r in envs:
        rows.append({**{k: r.get(k) for k in keys}, "reward_type": r["reward"]["type"], "reward_signal": r["reward"]["signal"],
                     "reward_note": r["reward"]["note"], "page": SITE + r["url"], "field": DET[r["isced"]]["name"]})
    json.dump({"generated": TODAY, "taxonomy": tax["source"], "count": len(rows), "environments": rows},
              open(f"{ROOT}/data/environments.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{ROOT}/environments.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys + ["field"]); w.writeheader()
        for row in rows:
            w.writerow({k: ("; ".join(map(str, v)) if isinstance(v, list) else v) for k, v in row.items()})
    lines = ["# Open Environments Index", "", f"> {len(envs)} open RL environments for language-model agents, filed under the ISCED-F 2013 fields of education. By Renaissance Labs. Generated {TODAY}.", ""]
    for b in tax["broad"]:
        items = [r for r in envs if r["isced"][:2] == b["code"]]
        if not items: continue
        lines += [f"## {b['code']} {b['name']}", ""]
        for r in sorted(items, key=lambda r: (r["isced"], -r["downloads"])):
            lines.append(f"- [{r['name']}]({SITE}{r['url']}) ({r['isced']} {DET[r['isced']]['name']}; reward: {REWARD[r['reward']['type']].lower()}): {r['summary']}")
        lines.append("")
    open(f"{ROOT}/llms.txt", "w").write("\n".join(lines))
    urls = ["/", "/fields/", "/about/"] + [f"/fields/{b['code']}/" for b in tax["broad"]] + [r["url"] for r in envs]
    open(f"{ROOT}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                           "".join(f"<url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    open(f"{ROOT}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

for r in envs: r["reward_type"] = r["reward"]["type"]
shutil.rmtree(f"{ROOT}/env", ignore_errors=True)
shutil.rmtree(f"{ROOT}/fields", ignore_errors=True)
build_home()
for r in envs: build_env(r)
build_fields(); build_about(); build_data()
open(f"{ROOT}/.nojekyll", "w").close()
print(f"{len(envs)} environments, {covered}/{len(DET)} fields, {publishers} publishers, {len(dropped)} dropped")
