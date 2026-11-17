#!/usr/bin/env python3
"""Keep profile.json in sync with what Ziad is actually working on.

1. Collect recent GitHub activity (repos pushed in the last DAYS days, their
   descriptions, README heads and commit subjects) with GH_PAT.
2. Ask Claude for conservative, evidence-backed proposals for profile.json.
3. Hand the proposals to Ziad's two homelab agents, Hermes and OpenClaw, who
   negotiate with each other over up to two rounds. Only what they both approve
   (possibly rewritten) is applied; items they still disagree on are dropped.
   They may also jointly add items the digest missed.
4. Apply the agreed changes and append a readable entry to profile-changes.md.

Environment:
  GH_PAT             token that can read the user's private repos (falls back to GITHUB_TOKEN)
  ANTHROPIC_API_KEY  API key (required unless --digest-only); on the homelab runner the OmniRoute key
  ANTHROPIC_BASE_URL optional Anthropic-compatible gateway (OmniRoute: http://192.168.2.170:20128)
  SYNC_MODELS        comma-separated gateway models to try in order (default auto/best-coding,auto/best-reasoning,auto/best-chat)
  SYNC_DAYS          look-back window in days (default 14)
  GH_USER            GitHub login to scan (default haresholmes)
  AGENT_HOST         SSH target that exposes ask-hermes / ask-openclaw (default root@192.168.2.170)
  AGENTS_DISABLED=1  skip the agents (nothing is applied; proposals are only logged)

Usage:
  python3 scripts/sync_profile.py                # full run
  python3 scripts/sync_profile.py --digest-only  # print the activity digest and exit
  python3 scripts/sync_profile.py --dry-run      # Claude proposals only, printed, nothing applied
"""
import datetime as dt
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "profile.json"
CHANGELOG = ROOT / "profile-changes.md"
GH_USER = os.environ.get("GH_USER", "haresholmes")
DAYS = int(os.environ.get("SYNC_DAYS", "14"))
MODEL = "claude-opus-5-5"

# Ziad's homelab agents live on the Proxmox host. The runner holds an SSH key whose
# forced command only permits `ask-hermes` / `ask-openclaw` (no shell).
AGENT_HOST = os.environ.get("AGENT_HOST", "root@192.168.2.170")
PRIVACY = ("Only professional/career facts suitable for a PUBLIC CV may appear in approved or added text: never "
           "personal, family, health, legal or financial details, phone numbers, addresses, credentials, internal "
           "hostnames or anything private. Reject or rewrite anything that breaks this.")


# ------------------------------------------------------------ GitHub ------

def gh(path, token, raw=False):
    url = path if path.startswith("http") else "https://api.github.com" + path
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json",
        "User-Agent": "portfolio-sync",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return data.decode("utf-8", "replace") if raw else json.loads(data)


def collect_digest(token):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DAYS)
    repos, page = [], 1
    while True:
        batch = gh(f"/user/repos?affiliation=owner,collaborator&sort=pushed&per_page=100&page={page}", token)
        if not batch:
            break
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    active = []
    for r in repos:
        pushed = dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
        if pushed < since or r.get("fork"):
            continue
        full = r["full_name"]
        commits = gh(f"/repos/{full}/commits?since={since.isoformat()}&per_page=100", token) or []
        mine = [c for c in commits if (c.get("author") or {}).get("login") == GH_USER
                or GH_USER.lower() in ((c["commit"].get("author") or {}).get("name", "").lower())
                or (c["commit"].get("author") or {}).get("email", "").startswith("ziad")]
        if not mine:
            continue
        readme = gh(f"/repos/{full}/readme", token, raw=True) or ""
        active.append({
            "repo": full,
            "private": r["private"],
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "topics": r.get("topics") or [],
            "pushed_at": r["pushed_at"],
            "commits_in_window": len(mine),
            "commit_subjects": [c["commit"]["message"].splitlines()[0][:140] for c in mine[:60]],
            "readme_head": readme[:2500],
        })
    return {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "days": DAYS, "repos": active}


def digest_text(d, full=True, readme_chars=2500):
    lines = [f"Activity window: last {d['days']} days (generated {d['generated_at']})", ""]
    for r in d["repos"]:
        lines.append(f"### {r['repo']} ({'private' if r['private'] else 'public'}; {r['language']}; last push {r['pushed_at']})")
        if r["description"]:
            lines.append(f"Description: {r['description']}")
        if r["topics"]:
            lines.append("Topics: " + ", ".join(r["topics"]))
        lines.append(f"Commits by Ziad in window: {r['commits_in_window']}")
        lines += [f"- {s}" for s in r["commit_subjects"][: (60 if full else 25)]]
        if r["readme_head"] and (full or readme_chars):
            lines.append("README (head):")
            lines.append(r["readme_head"][:readme_chars])
        lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------ Claude ------

OPS = ["add_role_bullet", "add_engagement", "add_engagement_detail", "set_engagement_end", "add_project", "add_skill_terms"]

SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": OPS},
                    "org": {"type": "string", "description": "Experience org to attach to (exact match on profile.experience[].org); empty when not applicable"},
                    "client": {"type": "string", "description": "Engagement client name under Computator Technology; empty when not applicable"},
                    "text": {"type": "string", "description": "CV-quality sentence(s) for the bullet/engagement/project description"},
                    "site_text": {"type": "string", "description": "Shorter version for the website; empty to reuse text"},
                    "title": {"type": "string", "description": "Project title for add_project; empty otherwise"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "start": {"type": "string", "description": "e.g. 'Nov 2026'; empty when unknown"},
                    "end": {"type": "string", "description": "e.g. 'Present' or 'Dec 2026'; empty when unknown"},
                    "skill_title": {"type": "string", "description": "profile.skills[].title to extend for add_skill_terms; empty otherwise"},
                    "terms": {"type": "array", "items": {"type": "string"}},
                    "evidence_repos": {"type": "array", "items": {"type": "string"}, "description": "full_name of repos in the digest that prove this"},
                    "reason": {"type": "string"}
                },
                "required": ["op", "org", "client", "text", "site_text", "title", "tags", "start", "end",
                             "skill_title", "terms", "evidence_repos", "reason"],
                "additionalProperties": False
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["changes", "summary"],
    "additionalProperties": False
}

SYSTEM = """You maintain the CV and portfolio website of Ziad Hares, a CTO, founder and cybersecurity engineer in Dubai.
You receive the current profile.json (single source of truth for both documents) and a digest of Ziad's GitHub activity over the last few weeks.

Propose only changes that the digest clearly proves. Rules:
- Never invent employers, titles, certifications, dates, metrics or clients. If the digest does not show it, do not add it.
- Skip anything already covered by an existing bullet, engagement, project or skill. Prefer no change over a near-duplicate.
- A new repo that is clearly a client or product project becomes an engagement under "Computator Technology" (op add_engagement) unless it belongs to Begad (then add_role_bullet on the Begad org) or is personal/lab work (then add_project).
- Significant new capability inside an existing engagement or role becomes add_engagement_detail (appends one sentence to that engagement) or add_role_bullet.
- When a repo for an engagement marked with an end date is clearly active again, use set_engagement_end with end "Present".
- Mention a technology in add_skill_terms only when it is used substantively in the digest and not yet in that skill.
- Write bullets in the existing style: concrete, past or present tense, technologies named, no hype, no first person, under 45 words. Use HTML entities for & (write &amp;).
- Do not include secrets, credentials, internal IPs, customer names found in commit messages, or anything embarrassing.
- Every change must cite evidence_repos from the digest.
- If nothing qualifies, return an empty changes list and say why in summary."""


def _strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def _normalise_proposals(data):
    """Coerce whatever model answered into the SCHEMA shape; drop malformed items."""
    out = []
    for c in (data or {}).get("changes", []) or []:
        if not isinstance(c, dict) or c.get("op") not in OPS:
            continue
        item = {k: "" for k in ("org", "client", "text", "site_text", "title", "start", "end", "skill_title", "reason")}
        item.update({k: str(c.get(k) or "") for k in item})
        item["op"] = c["op"]
        item["tags"] = [str(t) for t in (c.get("tags") or [])][:4]
        item["terms"] = [str(t) for t in (c.get("terms") or [])]
        item["evidence_repos"] = [str(t) for t in (c.get("evidence_repos") or [])]
        out.append(item)
    return {"changes": out, "summary": str((data or {}).get("summary") or "")}


def propose(profile, digest):
    """Ask the model for proposals. Through the real Anthropic API this uses structured outputs on
    claude-opus-5-5; through an Anthropic-compatible gateway (ANTHROPIC_BASE_URL set, e.g. Ziad's
    OmniRoute on the homelab) the responding model varies, so it falls back to JSON-in-text with a
    fallback list of gateway models and strips <think> blocks."""
    import anthropic  # imported here so --digest-only works without the SDK
    gateway = bool(os.environ.get("ANTHROPIC_BASE_URL"))
    # Gateway models can be slow; cap each attempt so the fallback list still fits in the job timeout.
    client = anthropic.Anthropic(timeout=float(os.environ.get("SYNC_MODEL_TIMEOUT", "420")), max_retries=1)
    user = ("Current profile.json:\n```json\n" + json.dumps(profile, ensure_ascii=False, indent=1)
            + "\n```\n\nGitHub activity digest:\n" + digest_text(digest, full=not gateway, readme_chars=1200 if gateway else 2500)
            + "\n\nReturn ONLY one fenced ```json block with an object of this exact shape and nothing else:\n"
            + json.dumps({"changes": [{k: ("[]" if SCHEMA["properties"]["changes"]["items"]["properties"][k]["type"] == "array" else "")
                                        for k in SCHEMA["properties"]["changes"]["items"]["required"]}], "summary": ""}, indent=1)
            + "\nAllowed op values: " + ", ".join(OPS) + ". Use [] for empty arrays and \"\" for empty strings.")
    models = ([m for m in os.environ.get("SYNC_MODELS", "auto/best-coding,auto/best-reasoning,auto/best-chat").split(",") if m.strip()]
              if gateway else [MODEL])
    last_err = None
    for model in models:
        kwargs = dict(model=model, max_tokens=12000, system=SYSTEM, messages=[{"role": "user", "content": user}])
        if not gateway:
            kwargs["output_config"] = {"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}}
        try:
            with client.messages.stream(**kwargs) as stream:
                resp = stream.get_final_message()
        except anthropic.RateLimitError as e:
            print(f"{model}: rate limited ({e.message[:120]}); trying next model")
            last_err = e
            continue
        except anthropic.APIStatusError as e:
            print(f"{model}: API error {e.status_code}: {e.message[:200]}; trying next model")
            last_err = e
            continue
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            print(f"{model}: {e.__class__.__name__}; trying next model")
            last_err = e
            continue
        if resp.stop_reason == "refusal":
            raise SystemExit(f"Model declined the request: {resp.stop_details}")
        text = _strip_think("".join(b.text for b in resp.content if b.type == "text"))
        data = parse_decisions(text) if gateway else json.loads(text)
        if data is None or "changes" not in data:
            print(f"{model} (answered as {resp.model}): no parsable JSON; trying next model")
            last_err = ValueError("unparsable")
            continue
        print(f"proposals from {model} (answered as {resp.model})")
        return _normalise_proposals(data), resp.usage
    raise SystemExit(f"No model produced usable proposals: {last_err}")


# ------------------------------------------------------- agents -----------

def ask_agent(agent, prompt, timeout=620):
    """Ask Hermes or OpenClaw over the restricted SSH gate. Returns text, or None if unavailable."""
    if os.environ.get("AGENTS_DISABLED") == "1":
        return None
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", AGENT_HOST,
           f"ask-{agent} " + shlex.quote(prompt)]
    for attempt in range(3):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"{agent}: unavailable ({e.__class__.__name__})")
            return None
        if r.returncode == 75:  # the peer lock is held; wait and retry
            import time
            print(f"{agent}: busy, retrying in 90s")
            time.sleep(90)
            continue
        if r.returncode != 0:
            print(f"{agent}: exit {r.returncode}: {r.stderr.strip()[:300]}")
            return None
        return r.stdout.strip()
    return None


def parse_decisions(text):
    """Pull the last ```json block out of an agent reply."""
    if not text:
        return None
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    for raw in reversed(blocks):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    m = re.search(r"\{.*\}", text, re.S)  # last resort: a bare object
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def describe(c):
    what = c.get("client") or c.get("title") or c.get("org") or c.get("skill_title") or ""
    body = c.get("text") or ", ".join(c.get("terms", []))
    when = f" [{c.get('start') or '?'} – {c.get('end') or '?'}]" if c.get("start") or c.get("end") else ""
    return f"{c['op']} · {what}{when}: {body}  (evidence: {', '.join(c.get('evidence_repos', []))})"


DECISION_FORMAT = """End your reply with exactly one fenced ```json block of this shape (ids refer to the numbered proposals):
{"decisions":[{"id":1,"verdict":"approve|reject|rewrite","text":"<rewritten CV text when verdict is rewrite, else empty>","note":"<one line of reasoning>"}],
 "additions":[{"op":"add_engagement|add_project|add_role_bullet","client":"<client for add_engagement, else empty>","title":"<project title for add_project, else empty>","org":"<org for add_role_bullet, else empty>","text":"<CV text>","start":"<e.g. Nov 2026 or empty>","end":"<Present or empty>","tags":["<tag>"],"note":"<why you are sure this is true>"}],
 "stance":"<one sentence summary of your position>"}
Keep additions to at most 3 and include one only when you are certain it is real, professional and not already in the profile."""


def brief_text(profile, proposals, digest):
    known = sorted({g["client"] for e in profile["experience"] for g in e.get("engagements", [])}
                   | {e["org"] for e in profile["experience"]} | {p["title"] for p in profile["projects"]})
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DAYS)).date().isoformat()
    numbered = "\n".join(f"{i}. {describe(c)}" for i, c in enumerate(proposals, 1)) or "(no proposals from the GitHub digest)"
    return (f"Context: Ziad's public CV and portfolio website (haresholmes.eu.org) are updated automatically. "
            f"The profile already covers: {', '.join(known)}.\n"
            f"Proposed additions generated from his GitHub activity since {since}:\n{numbered}\n\n"
            f"Short view of that GitHub activity:\n{digest_text(digest, full=False, readme_chars=0)[:6000]}\n\n{PRIVACY}")


def negotiate(profile, proposals, digest):
    """Hermes and OpenClaw talk it over, relayed by this script. Returns (final_decisions, additions, transcript)."""
    brief = brief_text(profile, proposals, digest)
    transcript = []

    h1 = ask_agent("hermes",
        "You are Hermes. The portfolio sync pipeline is relaying a negotiation between you and OpenClaw about what goes on "
        "Ziad's public CV. Give your opening position: for each numbered proposal say approve, reject or rewrite (with the "
        "better wording), using what you know about Ziad's real work to check titles, dates and claims. Then propose up to 3 "
        "additions the pipeline missed, if any. Be concrete and brief.\n\n" + brief + "\n\n" + DECISION_FORMAT)
    transcript.append(("Hermes, opening", h1))
    if h1 is None:
        return None, None, transcript

    o1 = ask_agent("openclaw",
        "You are OpenClaw. The portfolio sync pipeline is relaying a negotiation between you and Hermes about what goes on "
        "Ziad's public CV. Below are the proposals and Hermes's opening position. Agree where Hermes is right, push back where "
        "wording is overstated, unclear, unprofessional or unsupported, and give your own verdict for every proposal and for "
        "each addition Hermes suggested (list an addition in your own additions only if you agree it is real).\n\n"
        + brief + "\n\nHermes's opening position:\n" + h1 + "\n\n" + DECISION_FORMAT)
    transcript.append(("OpenClaw, response", o1))
    if o1 is None:
        return None, None, transcript

    dh, do = parse_decisions(h1), parse_decisions(o1)
    if dh and do and agreed(dh, do, proposals):
        final, additions = merge(dh, do, proposals)
        return final, additions, transcript

    h2 = ask_agent("hermes",
        "You are Hermes. Second and final round of your negotiation with OpenClaw about Ziad's public CV. Read OpenClaw's "
        "objections, concede where OpenClaw is right, hold your ground only with a reason, and give your FINAL verdict for "
        "every proposal and addition. Aim to converge; anything you two still disagree on will be dropped.\n\n"
        + brief + "\n\nYour opening position:\n" + h1 + "\n\nOpenClaw's response:\n" + o1 + "\n\n" + DECISION_FORMAT)
    transcript.append(("Hermes, final", h2))
    o2 = ask_agent("openclaw",
        "You are OpenClaw. Final round of your negotiation with Hermes about Ziad's public CV. Read Hermes's final position and "
        "give your FINAL verdict for every proposal and addition. Aim to converge; anything you two still disagree on will be "
        "dropped.\n\n" + brief + "\n\nHermes's opening position:\n" + h1 + "\n\nYour earlier response:\n" + o1
        + "\n\nHermes's final position:\n" + (h2 or "(no reply)") + "\n\n" + DECISION_FORMAT)
    transcript.append(("OpenClaw, final", o2))
    dh2, do2 = parse_decisions(h2) or dh, parse_decisions(o2) or do
    if not (dh2 and do2):
        return None, None, transcript
    final, additions = merge(dh2, do2, proposals)
    return final, additions, transcript


def _by_id(d):
    out = {}
    for x in d.get("decisions", []) or []:
        try:
            out[int(x.get("id"))] = x
        except (TypeError, ValueError):
            pass
    return out


def norm(s):
    return " ".join((s or "").lower().split())


def _add_key(a):
    return norm(a.get("client") or a.get("title") or (a.get("org", "") + ":" + a.get("text", "")[:40]))


def agreed(dh, do, proposals):
    h, o = _by_id(dh), _by_id(do)
    for i in range(1, len(proposals) + 1):
        vh, vo = (h.get(i) or {}).get("verdict"), (o.get(i) or {}).get("verdict")
        if vh != vo and {vh, vo} != {"approve", "rewrite"}:
            return False
    hk = {_add_key(a) for a in dh.get("additions", []) or []}
    ok = {_add_key(a) for a in do.get("additions", []) or []}
    return hk == ok


def merge(dh, do, proposals):
    """Items both approve (or approve/rewrite) pass; rewrite text comes from Hermes when present, else OpenClaw.
    Additions pass only when both agents list the same client/title."""
    h, o = _by_id(dh), _by_id(do)
    final = []
    for i, c in enumerate(proposals, 1):
        vh, vo = (h.get(i) or {}).get("verdict"), (o.get(i) or {}).get("verdict")
        if vh in ("approve", "rewrite") and vo in ("approve", "rewrite"):
            text = (h.get(i) or {}).get("text") if vh == "rewrite" else None
            text = text or ((o.get(i) or {}).get("text") if vo == "rewrite" else None)
            c = dict(c)
            if text:
                c["text"] = text
                c["site_text"] = ""
            c["verdict"] = "approved" + (" (rewritten)" if text else "")
            c["notes"] = [(h.get(i) or {}).get("note", ""), (o.get(i) or {}).get("note", "")]
            final.append(c)
        else:
            c = dict(c)
            c["verdict"] = f"dropped (Hermes: {vh or 'no verdict'}, OpenClaw: {vo or 'no verdict'})"
            c["notes"] = [(h.get(i) or {}).get("note", ""), (o.get(i) or {}).get("note", "")]
            final.append(c)
    ok = {_add_key(a): a for a in do.get("additions", []) or []}
    additions = []
    for a in dh.get("additions", []) or []:
        k = _add_key(a)
        if k in ok and a.get("text"):
            additions.append({**a, "evidence_repos": ["hermes+openclaw consensus"], "site_text": "",
                              "tags": a.get("tags") or ["Project"], "terms": [], "skill_title": "",
                              "reason": a.get("note", ""), "op": a.get("op") or "add_project",
                              "client": a.get("client", ""), "title": a.get("title", ""), "org": a.get("org", ""),
                              "start": a.get("start", ""), "end": a.get("end", "")})
    return final, additions


# ------------------------------------------------------------- apply ------

def apply_changes(profile, changes, digest):
    known = {r["repo"] for r in digest["repos"]} | {"hermes+openclaw consensus"}
    applied, skipped = [], []
    comp = next((e for e in profile["experience"] if e["org"] == "Computator Technology"), None)
    for c in changes:
        ev = [r for r in c.get("evidence_repos", []) if r in known]
        if not ev:
            skipped.append((c, "no evidence repo from the digest"))
            continue
        op = c["op"]
        try:
            if op == "add_role_bullet":
                e = next((x for x in profile["experience"] if norm(x["org"]) == norm(c["org"])
                          or norm(c["org"]) in norm(x["org"])), None)
                if not e:
                    g = next((g for g in (comp or {}).get("engagements", []) if norm(g["client"]) == norm(c["org"])), None)
                    pr = next((p for p in profile["projects"] if norm(p["title"]) == norm(c["org"])
                               or norm(c["org"]) in norm(p["title"])), None)
                    if g:
                        c = dict(c, op="add_engagement_detail", client=g["client"])
                        op = "add_engagement_detail"
                    elif pr:
                        if norm(c["text"]) in norm(pr["desc"]):
                            raise ValueError("detail already present")
                        pr["desc"] = pr["desc"].rstrip(".") + ". " + c["text"].rstrip(".") + "."
                        if pr.get("cv_desc"):
                            pr["cv_desc"] = pr["cv_desc"].rstrip(".") + ". " + c["text"].rstrip(".") + "."
                        applied.append((c, ev))
                        continue
                    else:
                        raise ValueError(f"unknown org {c['org']!r}")
            if op == "add_role_bullet":
                if any(norm(c["text"]) == norm(b) for b in e.get("bullets", [])):
                    raise ValueError("duplicate bullet")
                e.setdefault("bullets", []).append(c["text"])
                if "site_bullets" in e:
                    e["site_bullets"].append(c.get("site_text") or c["text"])
            elif op == "add_engagement":
                if comp is None:
                    raise ValueError("no Computator Technology entry")
                if any(norm(g["client"]) == norm(c["client"]) for g in comp.get("engagements", [])):
                    raise ValueError("engagement exists")
                if not c.get("client"):
                    raise ValueError("engagement without client")
                comp.setdefault("engagements", []).append({
                    "client": c["client"], "start": c.get("start") or "2026", "end": c.get("end") or "Present",
                    "text": c["text"], "site_text": c.get("site_text") or c["text"]})
            elif op == "add_engagement_detail":
                g = next((g for g in comp.get("engagements", []) if norm(g["client"]) == norm(c["client"])), None)
                if not g:
                    raise ValueError(f"unknown engagement {c['client']!r}")
                if norm(c["text"]) in norm(g["text"]):
                    raise ValueError("detail already present")
                g["text"] = g["text"].rstrip(".") + "; " + c["text"][0].lower() + c["text"][1:].rstrip(".") + "."
                g["site_text"] = g.get("site_text", g["text"])
            elif op == "set_engagement_end":
                g = next((g for g in comp.get("engagements", []) if norm(g["client"]) == norm(c["client"])), None)
                if not g:
                    raise ValueError(f"unknown engagement {c['client']!r}")
                if not c.get("end"):
                    raise ValueError("no end given")
                g["end"] = c["end"]
            elif op == "add_project":
                if not c.get("title"):
                    raise ValueError("project without title")
                if any(norm(p["title"]) == norm(c["title"]) for p in profile["projects"]):
                    raise ValueError("project exists")
                profile["projects"].insert(len([p for p in profile["projects"] if p.get("featured")]), {
                    "title": c["title"], "desc": c.get("site_text") or c["text"], "tags": (c.get("tags") or ["Project"])[:4],
                    "cv": False})
            elif op == "add_skill_terms":
                s = next((s for s in profile["skills"] if norm(s["title"]) == norm(c["skill_title"])), None)
                if not s:
                    raise ValueError(f"unknown skill {c['skill_title']!r}")
                new = [t for t in c["terms"] if t.lower() not in s["site"].lower()]
                if not new:
                    raise ValueError("terms already listed")
                s["site"] = s["site"] + ", " + ", ".join(new)
                if s.get("cv"):
                    s["cv"] = s["cv"] + ", " + ", ".join(new)
            else:
                raise ValueError(f"unknown op {op}")
            applied.append((c, ev))
        except (ValueError, KeyError, TypeError) as err:
            skipped.append((c, str(err)))
    return applied, skipped


def log_changes(applied, skipped, dropped, summary, usage, transcript):
    today = dt.date.today().isoformat()
    lines = [f"## {today}", "", summary.strip(), ""]
    for c, ev in applied:
        what = c.get("client") or c.get("title") or c.get("org") or c.get("skill_title")
        lines.append(f"- **{c['op']}** {what} — {c.get('verdict', 'applied')}: {c['text'] or ', '.join(c.get('terms', []))}  \n  evidence: {', '.join(ev)}")
        for who, note in zip(("Hermes", "OpenClaw"), c.get("notes", [])):
            if note:
                lines.append(f"  - {who}: {note}")
    for c in dropped:
        lines.append(f"- ~~{c['op']} {c.get('client') or c.get('title') or c.get('org') or c.get('skill_title')}~~ {c['verdict']}")
    for c, why in skipped:
        lines.append(f"- skipped {c['op']} ({why})")
    if transcript:
        lines += ["", "<details><summary>Negotiation transcript</summary>", ""]
        for who, text in transcript:
            lines += [f"**{who}**", "", (text or "(no reply)").strip(), ""]
        lines.append("</details>")
    if usage:
        lines.append(f"\n_tokens: in {usage.input_tokens}, out {usage.output_tokens}_")
    existing = CHANGELOG.read_text() if CHANGELOG.exists() else "# Profile sync log\n\n"
    CHANGELOG.write_text(existing.rstrip() + "\n\n" + "\n".join(lines) + "\n")


def main():
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_PAT (or GITHUB_TOKEN) is required")
    digest = collect_digest(token)
    if "--digest-only" in sys.argv:
        print(digest_text(digest))
        return
    if not digest["repos"]:
        print("No activity in window; nothing to do.")
        return
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        raise SystemExit("ANTHROPIC_API_KEY is not set (on the homelab runner it is read from /home/runner/.config/omniroute/key)")
    profile = json.loads(PROFILE.read_text())
    result, usage = propose(profile, digest)
    proposals = result.get("changes", [])
    print(f"Claude proposed {len(proposals)} change(s): {result.get('summary', '')}")
    if "--dry-run" in sys.argv:
        print(json.dumps(proposals, indent=1, ensure_ascii=False))
        return

    final, additions, transcript = negotiate(profile, proposals, digest)
    if final is None:
        print("Hermes/OpenClaw did not reach a usable decision; nothing applied.")
        log_changes([], [], [], "Agents unavailable or undecided; no changes applied. " + result.get("summary", ""), usage, transcript)
        return
    approved = [c for c in final if c["verdict"].startswith("approved")]
    dropped = [c for c in final if not c["verdict"].startswith("approved")]
    for c in approved:  # both agents approved it, which is the evidence Ziad asked for
        if not c.get("evidence_repos"):
            c["evidence_repos"] = ["hermes+openclaw consensus"]
    applied, skipped = apply_changes(profile, approved + additions, digest)
    for c, why in skipped:
        print(f"skipped {c['op']}: {why}")
    if applied:
        PROFILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    log_changes(applied, skipped, dropped, result.get("summary", ""), usage, transcript)
    print(f"Applied {len(applied)} agreed change(s); dropped {len(dropped)}; skipped {len(skipped)}")


if __name__ == "__main__":
    main()
