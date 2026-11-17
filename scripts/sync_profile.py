#!/usr/bin/env python3
"""Keep profile.json in sync with what Ziad is actually working on.

1. Collect recent GitHub activity (repos pushed in the last DAYS days, their
   descriptions, README heads and commit subjects) with GH_PAT.
2. Ask Claude for conservative, evidence-backed additions to profile.json.
3. Validate every proposed change against the digest (a change must cite a
   repo that appears in the digest) and apply it.
4. Append a human-readable entry to profile-changes.md.

Environment:
  GH_PAT             token that can read the user's private repos (falls back to GITHUB_TOKEN)
  ANTHROPIC_API_KEY  Claude API key (required unless --digest-only)
  SYNC_DAYS          look-back window in days (default 14)
  GH_USER            GitHub login to scan (default haresholmes)

Usage:
  python3 scripts/sync_profile.py              # full run, writes profile.json if anything changed
  python3 scripts/sync_profile.py --digest-only  # print the activity digest and exit
  python3 scripts/sync_profile.py --dry-run    # call Claude but only print the proposed changes
"""
import base64
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "profile.json"
CHANGELOG = ROOT / "profile-changes.md"
GH_USER = os.environ.get("GH_USER", "haresholmes")
DAYS = int(os.environ.get("SYNC_DAYS", "14"))
MODEL = "claude-opus-5-5"


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
    repos = []
    page = 1
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


def digest_text(d):
    lines = [f"Activity window: last {d['days']} days (generated {d['generated_at']})", ""]
    for r in d["repos"]:
        lines.append(f"### {r['repo']} ({'private' if r['private'] else 'public'}; {r['language']}; last push {r['pushed_at']})")
        if r["description"]:
            lines.append(f"Description: {r['description']}")
        if r["topics"]:
            lines.append("Topics: " + ", ".join(r["topics"]))
        lines.append(f"Commits by Ziad in window: {r['commits_in_window']}")
        lines += [f"- {s}" for s in r["commit_subjects"]]
        if r["readme_head"]:
            lines.append("README (head):")
            lines.append(r["readme_head"])
        lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------ Claude ------

SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": [
                        "add_role_bullet", "add_engagement", "add_engagement_detail",
                        "set_engagement_end", "add_project", "add_skill_terms"]},
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
- A new repo that is clearly a client or product project becomes an engagement under "Computator Technology" (op add_engagement) unless it belongs to Begad (then add_role_bullet on the Begad org) or is personal/lab work (then add_project with cv=false).
- Significant new capability inside an existing engagement or role becomes add_engagement_detail (appends one sentence to that engagement) or add_role_bullet.
- When a repo for an engagement marked with an end date is clearly active again, use set_engagement_end with end "Present".
- Mention a technology in add_skill_terms only when it is used substantively in the digest and not yet in that skill.
- Write bullets in the existing style: concrete, past or present tense, technologies named, no hype, no first person, under 45 words. Use HTML entities for & (write &amp;).
- Do not include secrets, credentials, internal IPs, customer names found in commit messages, or anything embarrassing.
- Every change must cite evidence_repos from the digest.
- If nothing qualifies, return an empty changes list and say why in summary."""


def propose(profile, digest):
    import anthropic  # imported here so --digest-only works without the SDK
    client = anthropic.Anthropic()
    user = ("Current profile.json:\n```json\n" + json.dumps(profile, ensure_ascii=False, indent=1)
            + "\n```\n\nGitHub activity digest:\n" + digest_text(digest)
            + "\n\nReturn the JSON object of proposed changes.")
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": user}],
    ) as stream:
        resp = stream.get_final_message()
    if resp.stop_reason == "refusal":
        raise SystemExit(f"Claude declined the request: {resp.stop_details}")
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text), resp.usage


# ------------------------------------------------------------- apply ------

def norm(s):
    return " ".join(s.lower().split())


def apply_changes(profile, changes, digest):
    known = {r["repo"] for r in digest["repos"]}
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
                e = next((x for x in profile["experience"] if x["org"] == c["org"]), None)
                if not e:
                    raise ValueError(f"unknown org {c['org']!r}")
                if any(norm(c["text"]) == norm(b) for b in e.get("bullets", [])):
                    raise ValueError("duplicate bullet")
                e.setdefault("bullets", []).append(c["text"])
                if "site_bullets" in e:
                    e["site_bullets"].append(c["site_text"] or c["text"])
            elif op == "add_engagement":
                if comp is None:
                    raise ValueError("no Computator Technology entry")
                if any(norm(g["client"]) == norm(c["client"]) for g in comp.get("engagements", [])):
                    raise ValueError("engagement exists")
                comp.setdefault("engagements", []).append({
                    "client": c["client"], "start": c["start"] or "2026", "end": c["end"] or "Present",
                    "text": c["text"], "site_text": c["site_text"] or c["text"]})
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
                if not c["end"]:
                    raise ValueError("no end given")
                g["end"] = c["end"]
            elif op == "add_project":
                if any(norm(p["title"]) == norm(c["title"]) for p in profile["projects"]):
                    raise ValueError("project exists")
                profile["projects"].insert(len([p for p in profile["projects"] if p.get("featured")]), {
                    "title": c["title"], "desc": c["site_text"] or c["text"], "tags": c["tags"][:4] or ["Project"],
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
        except ValueError as err:
            skipped.append((c, str(err)))
    return applied, skipped


def log_changes(applied, skipped, summary, usage):
    today = dt.date.today().isoformat()
    lines = [f"## {today}", "", summary.strip(), ""]
    for c, ev in applied:
        what = c.get("client") or c.get("title") or c.get("org") or c.get("skill_title")
        lines.append(f"- **{c['op']}** {what}: {c['text'] or ', '.join(c['terms'])}  \n  evidence: {', '.join(ev)}")
    for c, why in skipped:
        lines.append(f"- skipped {c['op']} ({why})")
    if usage:
        lines.append(f"\n_tokens: in {usage.input_tokens}, out {usage.output_tokens}_")
    existing = CHANGELOG.read_text() if CHANGELOG.exists() else "# Profile sync log\n\nAutomatic additions to profile.json proposed from GitHub activity and applied by scripts/sync_profile.py.\n\n"
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
        raise SystemExit("ANTHROPIC_API_KEY is not set. Add it as a repository secret: gh secret set ANTHROPIC_API_KEY")
    profile = json.loads(PROFILE.read_text())
    result, usage = propose(profile, digest)
    changes = result.get("changes", [])
    print(f"Claude proposed {len(changes)} change(s): {result.get('summary','')}")
    if "--dry-run" in sys.argv:
        print(json.dumps(changes, indent=1, ensure_ascii=False))
        return
    applied, skipped = apply_changes(profile, changes, digest)
    for c, why in skipped:
        print(f"skipped {c['op']}: {why}")
    if not applied:
        print("Nothing applied.")
        return
    PROFILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    log_changes(applied, skipped, result.get("summary", ""), usage)
    print(f"Applied {len(applied)} change(s) to profile.json")


if __name__ == "__main__":
    main()
