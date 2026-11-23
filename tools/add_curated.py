#!/usr/bin/env python3
"""Add environments that are not tagged rl-environment on the Hub, from a hand-kept list.
Writes data/records/curated.json and merges Hub metadata for them into data/hub.json."""
import json, os, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T, S = "0612", "0613"
# name, hub repo, subfolder (or ""), paper, field, task type, tasks, summary, evidence, good for
ROWS = [
 ("Endless Terminals 1K (rootless Apptainer)", "laion/endless-terminals-rootless-apptainer", "", "https://arxiv.org/abs/2601.16443", T, "terminal tasks", 1000,
  "Complete generated Linux terminal tasks built from task categories, complexity levels and scenario contexts.",
  "All 1,000 tasks pass the oracle 3/3 and reject a no-op 3/3 under rootless Apptainer.", ["Rootless HPC clusters", "Warm-up tasks for weak agents"]),
 ("RTS-1K (rootless Apptainer)", "laion/rts-1k-rootless-apptainer", "", "https://arxiv.org/abs/2608.05466", T, "terminal tasks", 984,
  "Solve terminal tasks rewritten recursively from about 600 TerminalWorld seeds.",
  "984 of a frozen 1,000-task cohort pass oracle and negative-control checks 3/3 offline.", ["Rootless HPC clusters", "Offline terminal RL"]),
 ("TaskTrove Curriculum Medium", "open-thoughts/TaskTrove", "DCAgent__exp_rpt_curriculum-medium-v2", None, S, "python programming", 489,
  "Write Python solutions to 489 canonical programming tasks checked by unit tests.", "", ["Curriculum stage between easy and real repositories"]),
 ("TaskTrove Curriculum Easy", "open-thoughts/TaskTrove", "DCAgent__exp_rpt_curriculum-easy", None, S, "python programming", 500,
  "Write Python solutions to about 500 easier programming tasks with fewer unit tests.", "", ["First curriculum stage for small models"]),
 ("TaskTrove R2E-Gym", "open-thoughts/TaskTrove", "laion__r2egym-patched-full-oracle-v3", "https://arxiv.org/abs/2504.07164", S, "issue fixing", 2566,
  "Fix synthetic software-engineering tasks derived from GitHub repositories, checked by the repository tests.",
  "Representative oracle checks pass for eight retained repository families.", ["Software-engineering RL at scale"]),
 ("SWE-Gym 1K (rootless Apptainer)", "laion/swegym-1k-rootless-apptainer", "", "https://arxiv.org/abs/2412.21139", S, "issue fixing", 1029,
  "Fix human-annotated issues in 11 Python repositories so the hidden tests pass.",
  "Oracle passes 1,029 of 1,029 and the no-op is rejected 1,029 of 1,029, offline.", ["Rootless HPC clusters", "Software-engineering RL"]),
 ("TaskTrove BugsInPy v4 (17 verified)", "laion/tasktrove-bugsinpy-v4-oracle17-apptainer-v1", "", None, S, "bug fixing", 17,
  "Repair real Python bugs from BugsInPy; only the 17 tasks with a reconstructed gold solution are verified.",
  "17 tasks pass repeated oracle, unchanged-starter and empty-solution controls.", ["Small verified smoke set"]),
 ("TMax 15K (Harbor)", "laion/TMax-15K-Harbor", "", "https://arxiv.org/abs/2606.23321", T, "terminal tasks", 15000,
  "Solve about 15,000 terminal tasks packaged as Harbor task directories.", "", ["Large-scale terminal RL"]),
 ("CLI-Gym", "LiberCoders/CLI-Gym", "", "https://arxiv.org/abs/2606.22883", T, "terminal tasks", 1600,
  "Repair broken command-line environments in tasks generated from real GitHub issues.", "", ["Environment repair skills"]),
 ("LiteCoder-Terminal RL preview", "Lite-Coder/LiteCoder-Terminal-RL-preview", "", "https://arxiv.org/abs/2605.29559", T, "terminal tasks", 600,
  "Solve about 600 terminal tasks released as an RL preview set.", "", ["Small-model terminal RL"]),
 ("TaskTrove SWE-rebench V2", "open-thoughts/TaskTrove", "DCAgent__swe_rebench_v2_patched_oracle-v2", "https://arxiv.org/abs/2602.23866", S, "issue fixing", 18315,
  "Fix software-engineering tasks derived from GitHub changes in 18 programming languages.", "", ["Multi-language software-engineering RL"]),
 ("TaskTrove SWE-smith", "open-thoughts/TaskTrove", "laion__swesmith-oracle-filtered-v2", "https://arxiv.org/abs/2504.21798", S, "issue fixing", None,
  "Fix synthetically injected bugs in Python repositories, filtered to tasks whose oracle passes.", "", ["Software-engineering RL"]),
 ("Nemotron Terminal easy clean-1K (rootless Apptainer)", "laion/nemotron-terminal-easy-clean1k-rootless-apptainer", "", None, T, "terminal tasks", 1000,
  "Solve 1,000 easy terminal tasks, 250 in each of four domains, from NVIDIA's synthetic terminal corpus.",
  "Every task passes its replay oracle 3/3 and rejects the no-op control 3/3 offline.", ["Training pool, not a clean benchmark", "Rootless HPC clusters"]),
 ("Nemotron terminal corpus, unified (100k sandboxes)", "DCAgent/nemotron-terminal-corpus-unified-100000-sandboxes", "", "https://arxiv.org/abs/2602.21193", T, "terminal tasks", 100000,
  "Solve terminal tasks from the unified Nemotron corpus, each with sandbox metadata.", "", ["Very large terminal RL pool"]),
 ("TaskTrove Nemotron-SWE Pivot", "open-thoughts/TaskTrove", "laion__nemotron-gym-agentic-swe-pivot-v4", None, S, "issue fixing", None,
  "Fix SWE-Gym and R2E-Gym tasks refactored into the NeMo Gym input format.", "", ["NeMo Gym pipelines"]),
 ("InferredBugs (sandboxes and verifier)", "DCAgent/inferredbugs-sandboxes-verifier", "", "https://arxiv.org/abs/2504.21798", S, "bug fixing", 10000,
  "Repair inferred bugs in a corpus of about 10,000 tasks packaged with sandboxes and verifier data.", "", ["Bug-repair RL"]),
 ("TaskTrove OpenSWE", "open-thoughts/TaskTrove", "laion__openswe-tasks-patched-v7-oracle-success", "https://arxiv.org/abs/2603.13023", S, "issue fixing", 40000,
  "Fix real GitHub issues across Python repositories, in tasks created with agent assistance.", "", ["Large-scale software-engineering RL"]),
 ("CalibForge", "AweAI-Team/CalibForge", "", "https://arxiv.org/abs/2608.06352", T, "terminal tasks", 5400,
  "Solve terminal tasks authored by an agent and calibrated so that weak solvers fail and strong solvers pass.",
  "The source list reports about 8 points gained on Terminal-Bench 2 after SFT for stronger models.", ["Difficulty-calibrated training", "SFT before RL"]),
 ("TerminalWorld", "EuniAI/TerminalWorld", "", "https://arxiv.org/abs/2605.22535", T, "terminal tasks", 1400,
  "Reproduce tasks reconstructed from recordings of real terminal sessions.", "", ["Held-out evaluation", "Realistic terminal work"]),
 ("SETA-Env", "camel-ai/SETA-Env", "", "https://arxiv.org/abs/2607.10891", T, "terminal tasks", 4567,
  "Solve terminal tasks sourced from nl2bash, Stack Overflow and Kaggle notebooks, plus harder evolved variants.",
  "The authors report higher Terminal-Bench scores for two models after RL with pass rate as reward.", ["Terminal RL with a difficulty ladder"]),
 ("Terminal-Lego-15k", "Lego-X/Terminal-Lego-15k", "", "https://huggingface.co/papers/2606.03461", T, "terminal tasks", 15000,
  "Solve about 15,000 validated Harbor terminal tasks sourced from Stack Overflow.", "Tasks are validated.", ["Large-scale terminal RL"]),
]
def meta(repo):
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://huggingface.co/api/datasets/{repo}", headers={"User-Agent": "catalogue-builder"}), timeout=40)
        return json.load(r)
    except Exception as ex:
        print("no hub metadata:", repo, ex); return None
hubp = f"{ROOT}/data/hub.json"
hub = json.load(open(hubp)); have = {(h["kind"], h["id"]) for h in hub}
recs, cache = [], {}
for name, repo, sub, paper, field, ttype, tasks, summary, ev, good in ROWS:
    if ("datasets", repo) in have and not sub and repo not in cache:
        print("already indexed, skipped:", repo); continue
    if repo not in cache:
        cache[repo] = meta(repo)
        m = cache[repo]
        if m:
            hub.append({"kind": "datasets", "id": repo, "author": m.get("author"), "downloads": m.get("downloads"), "likes": m.get("likes"),
                        "tags": m.get("tags", []), "lastModified": m.get("lastModified"), "createdAt": m.get("createdAt"), "gated": m.get("gated"),
                        "cardData": {"license": (m.get("cardData") or {}).get("license")}})
    if not cache[repo]: continue
    rid = repo + ("#" + sub if sub else "")
    recs.append({"id": rid, "hub_id": repo, "hub_path": sub, "kind": "datasets", "name": name, "summary": summary, "isced": field, "isced2": None,
                 "task_type": ttype, "good_for": good, "reward": {"type": "tests", "signal": "binary", "note": "Verifier tests run in the sandbox after the agent finishes; a task counts as solved when they pass."},
                 "tasks": tasks, "interface": ["terminal", "code-exec"], "horizon": "multi-step", "frameworks": ["harbor"] if "harbor" in name.lower() or "TaskTrove" in repo or "apptainer" in repo else [],
                 "run": None, "needs": "Apptainer (rootless)" if "apptainer" in repo else "", "languages": ["en"], "paper": paper, "code": None,
                 "validated": ev, "is_environment": True, "curated": True})
json.dump(recs, open(f"{ROOT}/data/records/curated.json", "w"), ensure_ascii=False, indent=1)
json.dump(hub, open(hubp, "w"), ensure_ascii=False)
print(len(recs), "curated records")
