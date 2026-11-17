#!/usr/bin/env python3
"""Render cv.html and the profile-driven sections of index.html from profile.json.

profile.json is the single source of truth. Strings in it are trusted HTML
fragments (entities such as &amp; are already encoded where needed).

Usage:  python3 scripts/build.py              # writes cv.html and index.html in place
        python3 scripts/build.py --check      # exit 1 if either file would change
        python3 scripts/build.py --compact=1  # tighter CV type/margins (0, 1 or 2); render_cv.sh picks this

The CV shows the first `cv_max_bullets` bullets of each role (profile default 7, per-role override);
the website shows all of them, so sync-added bullets grow the site without overflowing the CV.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "profile.json"
CV = ROOT / "cv.html"
INDEX = ROOT / "index.html"

COMPACT = {0: ("11mm 12mm", "9.2pt", "1.3"), 1: ("10mm 11mm", "8.9pt", "1.27"), 2: ("9mm 10mm", "8.6pt", "1.24")}

CV_CSS = """\
  @page { size: A4; margin: %(margin)s; }
  :root {
    --ink: #111827; --muted: #4b5563; --line: #d1d5db; --accent: #0f172a; --rule: #1d4ed8;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: var(--ink); font-size: %(font)s; line-height: %(lh)s; background: #fff;
  }
  .page { max-width: 186mm; margin: 0 auto; padding: 10mm 0; }
  @media print { .page { max-width: none; padding: 0; } }
  header { border-bottom: 2px solid var(--accent); padding-bottom: 5px; margin-bottom: 7px; }
  h1 { font-size: 20pt; margin: 0; letter-spacing: -0.3px; }
  .tagline { font-size: 10.5pt; font-weight: 600; color: var(--rule); margin: 1px 0 3px; }
  .contact { font-size: 8.6pt; color: var(--muted); }
  .contact a { color: inherit; text-decoration: none; }
  .contact span + span::before { content: " · "; color: #9ca3af; }
  h2 {
    font-size: 9.6pt; text-transform: uppercase; letter-spacing: 1.1px; color: var(--accent);
    border-bottom: 1px solid var(--line); margin: 9px 0 4px; padding-bottom: 2px;
  }
  p { margin: 0 0 4px; }
  .item { margin-bottom: 5px; }
  .item-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; break-after: avoid; }
  li { break-inside: avoid; }
  h2 { break-after: avoid; }
  .role { font-weight: 700; }
  .org { color: var(--muted); }
  .date { white-space: nowrap; color: var(--muted); font-size: 8.6pt; }
  ul { margin: 2px 0 0; padding-left: 13px; }
  li { margin: 0 0 1.2px; }
  .skills { display: grid; grid-template-columns: 1fr; gap: 1.5px; }
  .skills div b { color: var(--accent); }
  .small { font-size: 8.6pt; color: var(--muted); }
"""


def load_profile():
    return json.loads(PROFILE.read_text())


def period(start, end):
    return f"{start} – {end}"


# ---------------------------------------------------------------- CV --------

def cv_item(role, org, when, bullets, small=None):
    head = f'<div class="item-head"><div><span class="role">{role}</span>'
    if org:
        head += f' <span class="org">· {org}</span>'
    head += f'</div><div class="date">{when}</div></div>'
    body = ""
    if bullets:
        body += "\n  <ul>\n" + "\n".join(f"    <li>{b}</li>" for b in bullets) + "\n  </ul>"
    if small:
        body += f'\n  <div class="small">{small}</div>'
    return f'<div class="item">\n  {head}{body}\n</div>'


def render_cv(p, compact=0):
    margin, font, lh = COMPACT[max(0, min(compact, 2))]
    css = CV_CSS % {"margin": margin, "font": font, "lh": lh}
    cv_max = int(p.get("cv_max_bullets", 7))
    out = []
    out.append("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
               f"<title>{p['name']} — CV</title>\n<meta name=\"robots\" content=\"noindex\">\n"
               "<!-- GENERATED FILE: edit profile.json and run scripts/build.py -->\n"
               f"<style>\n{css}</style>\n</head>\n<body>\n<div class=\"page\">")
    contact = [f"<span>{p['location']}</span>"]
    for ph in p["phones"]:
        contact.append(f'<span><a href="tel:{ph.replace(" ", "")}">{ph}</a></span>')
    contact.append(f'<span><a href="mailto:{p["email"]}">{p["email"]}</a></span>')
    contact.append(f'<span><a href="https://{p["site"]}">{p["site"]}</a></span>')
    contact.append(f'<span><a href="https://www.{p["linkedin"]}">{p["linkedin"]}</a></span>')
    contact.append(f'<span><a href="https://{p["github"]}">{p["github"]}</a></span>')
    out.append("<header>\n  <h1>%s</h1>\n  <div class=\"tagline\">%s</div>\n  <div class=\"contact\">\n    %s\n  </div>\n</header>"
               % (p["name"], p["title"], "\n    ".join(contact)))

    out.append(f"<h2>Summary</h2>\n<p>{p['summary']}</p>")

    out.append("<h2>Experience</h2>")
    for e in p["experience"]:
        bullets = list(e.get("bullets", []))[: int(e.get("cv_max_bullets", cv_max))]
        for g in e.get("engagements", []):
            bullets.append(f"<b>{g['client']}</b> ({g['start']} – {g['end']}): {g['text']}")
        bullets += e.get("closing_bullets", [])
        org = f"{e['org']} · {e['location']}" if e.get("location") else e["org"]
        out.append(cv_item(e["role"], org, period(e["start"], e["end"]), bullets))

    if p.get("leadership"):
        out.append("<h2>Leadership</h2>")
        for l in p["leadership"]:
            out.append(cv_item(l["role"], l["org"], period(l["start"], l["end"]), [l["text"]]))

    out.append("<h2>Selected Projects</h2>")
    for pr in p["projects"]:
        if not pr.get("cv"):
            continue
        title = pr.get("cv_title", pr["title"])
        out.append(cv_item(title, pr.get("cv_subtitle"), pr["period"], [pr.get("cv_desc", pr["desc"])]))
    cw = p.get("cv_client_websites")
    if cw:
        out.append(cv_item(cw["title"], None, cw["period"], [cw["desc"]]))

    out.append("<h2>Education</h2>")
    for ed in p["education"]:
        out.append(cv_item(ed["degree"], ed["school"], period(ed["start"], ed["end"]), [], small=ed.get("note")))

    out.append("<h2>Technical Skills</h2>\n<div class=\"skills\">")
    for s in p["skills"]:
        if s.get("cv"):
            out.append(f'  <div><b>{s.get("cv_title", s["title"])}:</b> {s["cv"]}</div>')
    out.append('  <div><b>Spoken languages:</b> ' + " · ".join(f"{l['name']} ({l['level'].lower()})" for l in p["languages"]) + "</div>")
    out.append("</div>")
    out.append("</div>\n</body>\n</html>\n")
    return "\n\n".join(out)


# ------------------------------------------------------------- index --------

def site_experience(p):
    items = []
    for e in p["experience"]:
        bullets = list(e.get("site_bullets", e.get("bullets", [])))
        for g in e.get("engagements", []):
            bullets.append(f"<strong>{g['client']}</strong> ({g['start']} – {g['end']}): {g.get('site_text', g['text'])}")
        bullets += e.get("site_closing_bullets", e.get("closing_bullets", []))
        lis = "\n".join(f"                        <li>{b}</li>" for b in bullets)
        items.append(f"""            <div class="experience-item">
                <div class="experience-dot"></div>
                <div class="experience-content">
                    <div class="experience-role">{e['role']}</div>
                    <div class="experience-company">{e['org']}{' · ' + e['location'] if e.get('location') else ''}</div>
                    <div class="experience-date">{period(e['start'], e['end'])}</div>
                    <ul class="experience-bullets">
{lis}
                    </ul>
                </div>
            </div>""")
    for l in p.get("leadership", []):
        items.append(f"""            <div class="experience-item">
                <div class="experience-dot"></div>
                <div class="experience-content">
                    <div class="experience-role">{l['role']}</div>
                    <div class="experience-company">{l['org']}</div>
                    <div class="experience-date">{period(l['start'], l['end'])}</div>
                    <div class="experience-desc">{l['text']}</div>
                </div>
            </div>""")
    return "\n".join(items)


def site_skills(p):
    cards = []
    for s in p["skills"]:
        cards.append(f"""                <div class="skill-card">
                    <div class="skill-icon">{s['icon']}</div>
                    <div class="skill-title">{s['title']}</div>
                    <div class="skill-desc">{s['site']}</div>
                </div>""")
    return "\n".join(cards)


def site_projects(p):
    cards = []
    for pr in p["projects"]:
        cls = "project-card project-card-featured" if pr.get("featured") else "project-card"
        badge = f'\n                    <div class="project-badge">{pr["badge"]}</div>' if pr.get("badge") else ""
        tags = "\n".join(f'                        <span class="project-tag">{t}</span>' for t in pr["tags"])
        cards.append(f"""                <div class="{cls}">
                    <div class="project-accent-line"></div>{badge}
                    <div class="project-title">{pr['title']}</div>
                    <div class="project-desc">{pr['desc']}</div>
                    <div class="project-tags">
{tags}
                    </div>
                </div>""")
    return "\n".join(cards)


def site_about(p):
    return "\n".join(f"            <p>{para}</p>" for para in p["about"])


def site_hero(p):
    return (f"                <h2>{p['headline']}</h2>\n"
            f"                <p class=\"hero-subtitle\">{p['hero_subtitle']}</p>")


def replace_region(html, name, body):
    start = f"<!-- profile:{name}:start -->"
    end = f"<!-- profile:{name}:end -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(html):
        raise SystemExit(f"index.html is missing the {name} markers")
    return pattern.sub(lambda m: f"{start}\n{body}\n{indent_for(name)}{end}", html, count=1)


def indent_for(name):
    return {"hero": "                ", "about": "            ", "experience": "            ",
            "skills": "            ", "projects": "            "}.get(name, "")


def render_index(p, html):
    html = replace_region(html, "hero", site_hero(p))
    html = replace_region(html, "about", site_about(p))
    html = replace_region(html, "experience", site_experience(p))
    html = replace_region(html, "skills", site_skills(p))
    html = replace_region(html, "projects", site_projects(p))
    return html


def main():
    check = "--check" in sys.argv
    compact = 0
    for a in sys.argv[1:]:
        if a.startswith("--compact="):
            compact = int(a.split("=", 1)[1])
    p = load_profile()
    new_cv = render_cv(p, compact)
    new_index = render_index(p, INDEX.read_text())
    changed = []
    for path, content in ((CV, new_cv), (INDEX, new_index)):
        if not path.exists() or path.read_text() != content:
            changed.append(path.name)
            if not check:
                path.write_text(content)
    if check:
        print("would change: " + (", ".join(changed) or "nothing"))
        sys.exit(1 if changed else 0)
    print("updated: " + (", ".join(changed) or "nothing (already current)"))


if __name__ == "__main__":
    main()
