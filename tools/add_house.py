#!/usr/bin/env python3
"""Add Renaissance Labs' own environments from the practice-environments repository.
Usage: python3 tools/add_house.py ../practice-environments
Writes data/records/renaissance.json and merges synthetic Hub-style metadata into data/hub.json."""
import json, os, sys
from datetime import date
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.abspath(sys.argv[1])
REPO = "RenaissanceLabsEU/practice"
envs = json.load(open(os.path.join(SRC, "environments.json")))
manifest = [json.loads(l) for l in open(os.path.join(SRC, "tasks.jsonl"))]
previous_hub = {h["id"]: h for h in json.load(open(f"{ROOT}/data/hub.json"))}
previous_path = os.path.join(ROOT, "data/records/renaissance.json")
previous_records = {r["id"]: r for r in json.load(open(previous_path))} if os.path.exists(previous_path) else {}
hub = [h for h in previous_hub.values() if not h["id"].startswith("RenaissanceLabsEU/")]
recs = []
for e in envs:
    rid = f"{REPO}#{e['name']}"
    mine = [m for m in manifest if m["env"] == e["name"]]
    first = sorted(m["id"] for m in mine if m["split"] == "train")[0]
    has_validators = os.path.exists(os.path.join(SRC, "envs", e["folder"], "validators.py"))
    hub.append({"kind": "datasets", "id": rid, "author": "RenaissanceLabs-EU", "downloads": 0, "likes": 0, "tags": ["license:mit", "harbor", "rl-environment"] + e.get("languages", ["en"]),
                "lastModified": date.today().isoformat(), "createdAt": date.today().isoformat(), "gated": False, "cardData": {"license": "mit"}})
    recs.append({"id": rid, "hub_id": rid, "kind": "datasets", "house": True, "name": e["title"], "summary": e["summary"], "isced": e["isced"], "isced2": None,
                 "task_type": e["task_type"], "good_for": e["good_for"], "tasks": len(mine), "families": e["families"],
                 "reward": {"type": "mixed" if has_validators else "programmatic", "signal": "graded",
                            "note": "A deterministic verifier compares each value in answer.json with the expected one" +
                                    (" and checks plans and counterexamples against the problem's own constraints" if has_validators else "") +
                                    "; the reward is the weighted share of checks passed, and a missing answer scores 0."},
                 "interface": ["terminal", "code-exec"], "horizon": "multi-step", "frameworks": ["harbor"], "needs": "Docker; no network at run time",
                 "languages": e.get("languages", ["en"]), "paper": None, "code": f"https://huggingface.co/datasets/{REPO}/tree/main/envs/{e['folder']}",
                 "hub_url": f"https://huggingface.co/datasets/{REPO}/tree/main/tasks/{e['name']}", "first_task": first, "env_name": e["name"],
                 "validated": "Every task: the reference solution scores 1.0 from the task files alone, an empty answer scores 0, and each check rejects a changed value.",
                 "run": None, "is_environment": True})
# Language tasks use bounded text/brief validators rather than numeric answer matching.
for record in recs:
    if record["env_name"].startswith("swedish-"):
        record["reward"]["note"] = "Each document is checked against an explicit editorial contract. Accepted alternatives earn equal credit; changed facts, extra claims and edits outside the contract score zero for that document. The task reward is the mean document score."
        record["validated"] = "All 324 Swedish task exports: standalone oracle 1.0, no-op 0. Adversarial and alternative-answer checks cover every published task; one hard task per family also passes in offline Docker."
# Preserve original publication dates and do not mark unchanged entries as updated.
for record in recs:
    old = previous_hub.get(record["id"])
    if old:
        new_meta = next(h for h in hub if h["id"] == record["id"])
        new_meta["createdAt"] = old.get("createdAt") or new_meta["createdAt"]
        if previous_records.get(record["id"]) == record:
            new_meta["lastModified"] = old.get("lastModified") or new_meta["lastModified"]
json.dump(recs, open(f"{ROOT}/data/records/renaissance.json", "w"), ensure_ascii=False, indent=1)
json.dump(hub, open(f"{ROOT}/data/hub.json", "w"), ensure_ascii=False)
print(len(recs), "Renaissance Labs environments")
