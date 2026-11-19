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

COMPACT = {0: ("17mm 19mm", "9.5pt", "1.45"), 1: ("16mm 18mm", "9.3pt", "1.4"), 2: ("15mm 17mm", "9.1pt", "1.36")}

CV_CSS = """\
  @page { size: A4; margin: %(margin)s; }
  :root { --ink: #111827; --muted: #5b6474; --line: #e5e7eb; --accent: #0f172a; --rule: #1d4ed8; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: var(--ink); font-size: %(font)s; line-height: %(lh)s; background: #fff;
  }
  .page { max-width: 180mm; margin: 0 auto; padding: 12mm 0; }
  @media print { .page { max-width: none; padding: 0; } }
  svg.px { shape-rendering: crispEdges; display: block; }
  header { margin-bottom: 4px; }
  .head-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
  .ident { display: flex; align-items: center; gap: 12px; }
  .ident svg.px { width: 11mm; height: auto; flex-shrink: 0; }
  h1 { font-size: 22pt; margin: 0; letter-spacing: -0.4px; line-height: 1.1; }
  .tagline { font-size: 10.2pt; font-weight: 600; color: var(--rule); margin: 3px 0 0; line-height: 1.35; }
  .contact { font-size: 8.8pt; color: var(--muted); margin-top: 6px; }
  .contact a { color: inherit; text-decoration: none; }
  .contact span + span::before { content: "  ·  "; color: #b8bec8; white-space: pre; }
  .strip { margin: 9px 0 2px; }
  .strip svg.px { width: 100%%; height: auto; }
  h2 {
    display: flex; align-items: center; gap: 7px;
    font-size: 9pt; text-transform: uppercase; letter-spacing: 1.8px; color: var(--accent);
    margin: 17px 0 7px; break-after: avoid;
  }
  h2 svg.px { width: 12px; height: 4px; }
  h2::after { content: ""; flex: 1; border-bottom: 1px solid var(--line); margin-left: 4px; }
  p { margin: 0; }
  .item { margin-bottom: 10px; break-inside: avoid; }
  .item-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; break-after: avoid; }
  .role { font-weight: 700; }
  .org { color: var(--muted); }
  .date { white-space: nowrap; color: var(--muted); font-size: 8.6pt; }
  ul { margin: 4px 0 0; padding-left: 14px; list-style: none; }
  li { position: relative; margin: 0 0 3px; break-inside: avoid; }
  ul li::before { content: ""; position: absolute; left: -11px; top: 0.62em; width: 4px; height: 4px; background: var(--rule); }
  .comp { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 14px; }
  .comp div { position: relative; padding-left: 11px; }
  .comp div::before { content: ""; position: absolute; left: 0; top: 0.55em; width: 5px; height: 5px; background: var(--rule); }
  .skills { display: grid; grid-template-columns: 34mm 1fr; gap: 4px 10px; }
  .skills b { color: var(--accent); }
  .small { font-size: 8.8pt; color: var(--muted); margin-top: 2px; }
  .qr-row { display: flex; gap: 6px; flex-shrink: 0; }
  .qr { width: 15mm; text-align: center; font-size: 6.8pt; color: var(--muted); line-height: 1.2; }
  .qr svg { width: 15mm; height: 15mm; display: block; }
  .qr a { color: inherit; text-decoration: none; }
  .live { break-inside: avoid; }
  .live .qr-row { gap: 14px; }
  .live .qr { width: 21mm; }
  .live .qr svg { width: 21mm; height: 21mm; }
"""

# Pixel-art accents (crisp SVG squares; scale-free in print).
SHIELD = ["..#######..", ".#########.", "###########", "####...####", "####...####", "#####.#####",
          "#####.#####", ".####.####.", ".#########.", "..#######..", "...#####...", "....###....", ".....#....."]


def pixel_shield():
    w, h = len(SHIELD[0]), len(SHIELD)
    cells = []
    for y, row in enumerate(SHIELD):
        for x, c in enumerate(row):
            if c == "#":
                fill = "#1d4ed8" if x < w // 2 + (y % 2) else "#3b82f6"
                cells.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{fill}"/>')
    cells = "".join(cells)
    return f'<svg class="px" viewBox="0 0 {w} {h}" aria-hidden="true">{cells}</svg>'


def pixel_marker():
    return ('<svg class="px" viewBox="0 0 9 3" aria-hidden="true">'
            '<rect x="0" y="0" width="3" height="3" fill="#bfdbfe"/><rect x="3" y="0" width="3" height="3" fill="#60a5fa"/>'
            '<rect x="6" y="0" width="3" height="3" fill="#1d4ed8"/></svg>')


def pixel_strip(n=90):
    """A single row of squares that dithers out from solid blue to nothing."""
    cells = []
    for i in range(n):
        density = 1 - i / n
        if (i * 37 % 100) / 100 < density * 1.15:
            shade = "#1d4ed8" if density > 0.66 else "#60a5fa" if density > 0.33 else "#bfdbfe"
            cells.append(f'<rect x="{i * 2}" y="0" width="1.2" height="1.2" fill="{shade}"/>')
    return f'<svg class="px" viewBox="0 0 {n * 2} 1.2" aria-hidden="true">' + "".join(cells) + "</svg>"


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


def qr_block(links):
    """Small scannable QR codes so a printed CV still reaches the live links."""
    import segno  # pip install segno (in /home/runner/venvs/portfolio on the runner)
    cells = []
    for link in links:
        svg = segno.make(link["url"], error="m").svg_inline(scale=1, border=2, dark="#111827", omitsize=True)
        url, label = link["url"], link["label"]
        cells.append(f'<div class="qr"><a href="{url}">{svg}<div>{label}</div></a></div>')
    return '<div class="qr-row">' + "".join(cells) + "</div>"


def render_cv(p, compact=0):
    """The CV uses short cv_* variants of profile text where present, so it stays airy
    while the website keeps the fuller wording."""
    margin, font, lh = COMPACT[max(0, min(compact, 2))]
    css = CV_CSS % {"margin": margin, "font": font, "lh": lh}
    cv_max = int(p.get("cv_max_bullets", 7))
    h2 = lambda title: f"<h2>{pixel_marker()}{title}</h2>"
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
    qr = qr_block(p["cv_qr"]) if p.get("cv_qr") else ""
    out.append(f'<header>\n<div class="head-row"><div class="ident">{pixel_shield()}<div>\n  <h1>{p["name"]}</h1>\n'
               f'  <div class="tagline">{"<br>".join(p["title"].split(" · "))}</div>\n</div></div>{qr}</div>\n<div class="contact">{"".join(contact)}</div>\n'
               f'<div class="strip">{pixel_strip()}</div>\n</header>')

    out.append(h2("Profile") + f"\n<p>{p.get('cv_summary', p['summary'])}</p>")
    if p.get("cv_competencies"):
        out.append(h2("Core Competencies") + "\n<div class=\"comp\">" + "".join(f"<div>{c}</div>" for c in p["cv_competencies"]) + "</div>")

    out.append(h2("Experience"))
    for e in p["experience"]:
        bullets = list(e.get("cv_bullets", e.get("bullets", [])))[: int(e.get("cv_max_bullets", cv_max))]
        for g in e.get("engagements", []):
            bullets.append(f"<b>{g['client']}</b>: {g.get('cv_text', g['text'])}")
        bullets += e.get("cv_closing_bullets", e.get("closing_bullets", []))
        org = f"{e['org']} · {e['location']}" if e.get("location") else e["org"]
        out.append(cv_item(e["role"], org, period(e["start"], e["end"]), bullets))

    if p.get("leadership"):
        out.append(h2("Leadership"))
        for l in p["leadership"]:
            out.append(cv_item(l["role"], l["org"], period(l["start"], l["end"]), [l.get("cv_text", l["text"])]))

    out.append(h2("Selected Projects"))
    for pr in p["projects"]:
        if not pr.get("cv"):
            continue
        title = pr.get("cv_title", pr["title"])
        out.append(cv_item(title, pr.get("cv_subtitle"), pr["period"], [pr.get("cv_desc", pr["desc"])]))
    cw = p.get("cv_client_websites")
    if cw:
        out.append(cv_item(cw["title"], None, cw["period"], [cw["desc"]]))

    out.append(h2("Education"))
    for ed in p["education"]:
        out.append(cv_item(ed["degree"], ed["school"], period(ed["start"], ed["end"]), [], small=ed.get("cv_note", ed.get("note"))))

    out.append(h2("Skills") + "\n<div class=\"skills\">")
    for sk in p["skills"]:
        if sk.get("cv"):
            out.append(f'  <b>{sk.get("cv_title", sk["title"])}</b><div>{sk["cv"]}</div>')
    out.append('  <b>Languages spoken</b><div>' + " · ".join(f"{l['name']} ({l['level'].lower()})" for l in p["languages"]) + "</div>")
    out.append("</div>")
    if p.get("cv_live_links"):
        out.append('<div class="live">' + h2("Live work · scan to open") + qr_block(p["cv_live_links"]) + "</div>")
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
