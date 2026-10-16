#!/usr/bin/env python3
"""Build privacy.pdxfixit.com: src/<app>/policy.md -> public/<app>/index.html, plus public/index.html.

This repo owns how every policy page looks and how it is made. An app supplies only its policy text,
as src/<app>/policy.md; it does not ship a page.

    python3 build.py          # write public/ (the pages only; the logo, font, favicon and _headers are kept by hand)
    python3 build.py --check  # build in memory and fail if public/ differs: CI runs this before deploying

Stdlib only, no network. The output is byte-for-byte the same every run.

A policy.md starts with a front matter block, then a small Markdown subset:

    ---
    name: Arrow-Rama                              # the app's name, as the index lists it
    blurb: A puzzle game for Android and Wear OS  # the subheadline under the title, and the line under the name on the index
    updated: 16 October 2026                      # shown as "Last updated" in the header, after "Made by the Sandberg family"
    order: 10                                     # optional: lower first on the index (default: by name)
    ---
    # Title                  one per page, first: the headline in the page header (it is not repeated in the body)
    ## Heading
    A paragraph. **bold**, *italic*, [a link](https://example.com) or [mail](mailto:a@b.c)
    - a list item, one line each

Links may go to https:, mailto: or a path on this site; anything else is an error.
"""
import html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, PUBLIC = ROOT / "src", ROOT / "public"
HOME = "https://pdxfixit.com/"
CONTACT = "privacy@pdxfixit.com"

CSS = """\
/* The pdxfixit.com look: Newsreader on the brand brown, the badge worn high, a hem at the foot. */
@font-face{font-family:"Newsreader";font-style:normal;font-weight:300 600;font-display:swap;src:url(/newsreader.woff2) format("woff2")}
:root{
  --ground:#E4D6C8;--ink:#24170F;--muted:#6B4C37;--orange:#F6921D;--link:#8A3A12;--rule:rgba(36,23,15,.22);
  --wordmark-filter:none;
  --serif:"Newsreader",Georgia,serif;
  --gutter:clamp(16px,5.5vw,84px);
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root{--ground:#2A1E17;--ink:#F2E7DB;--muted:#BBA08A;--link:#FFB066;--rule:rgba(242,231,219,.25);
    --wordmark-filter:url(#to-white);color-scheme:dark}
}
*,*::before,*::after{box-sizing:border-box}
html{background:var(--ground)}
body{margin:0;min-height:100svh;display:grid;grid-template-rows:auto 1fr auto;grid-template-columns:minmax(0,1fr);
  background:var(--ground);color:var(--ink);font:400 18px/1.5 var(--serif);font-optical-sizing:auto;-webkit-font-smoothing:antialiased}
::selection{background:var(--orange);color:#24170F}
a{color:var(--link)}
:focus-visible{outline:2px solid currentColor;outline-offset:4px;border-radius:4px}
.top{padding:clamp(22px,5.5vh,56px) var(--gutter) 0}
.intro{max-width:46rem;margin-top:clamp(28px,6vh,64px)}
.badge{--s:clamp(58px,5.4vw,80px);width:max-content;margin:0;line-height:0}
.badge a{display:block;border-radius:4px}
.badge svg{display:block;height:calc(var(--s) * 246 / 305);width:calc(var(--s) * 720 / 305)}
.badge .wordmark{filter:var(--wordmark-filter)}
main{align-self:start;width:100%;max-width:46rem;padding:clamp(20px,4vh,40px) var(--gutter) clamp(28px,6vh,72px)}
h1{font:340 clamp(2rem,5.2vw,3.6rem)/1.06 var(--serif);letter-spacing:-.022em;margin:0 0 .6rem}
.sub{font-size:clamp(1.1rem,2.4vw,1.4rem);line-height:1.3;margin:0 0 .5rem}
.made{color:var(--muted);font-size:1rem;margin:0}
h2{font:400 1.5rem/1.25 var(--serif);margin:2.25rem 0 .5rem}
p{margin:.75rem 0}
main ul{padding-left:1.25rem}
main li{margin:.5rem 0}
ul.apps{list-style:none;margin:0;padding:0;border-top:1px solid var(--rule)}
ul.apps li{margin:0;border-bottom:1px solid var(--rule)}
ul.apps a{display:block;padding:1rem 0;text-decoration:none;color:var(--ink)}
ul.apps b{display:block;font:400 1.6rem/1.2 var(--serif);color:var(--link);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.2em}
ul.apps a:hover b{text-decoration-thickness:2px}
ul.apps span{color:var(--muted)}
.hem{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 24px;padding:14px var(--gutter) 20px;font-size:16px;color:var(--muted);border-top:1px solid var(--rule)}
.hem nav{display:flex;flex-wrap:wrap;gap:6px 20px}
.hem a{color:var(--muted)}
@media (max-width:640px){.badge{--s:54px}}
"""

FILTER = """\
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<filter id="to-white" color-interpolation-filters="sRGB"><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0"/></filter>
</defs></svg>
"""

BADGE = """\
  <div class="badge">
    <a href="__HOME__" aria-label="PDXfixIT home">
      <svg viewBox="44 59 720 246" role="img" aria-label="PDXfixIT">
        <defs>
          <image id="art" x="44" y="59" width="720" height="201" href="/logo-art.webp"/>
          <clipPath id="ring-part"><rect x="44" y="59" width="234" height="246"/></clipPath>
          <clipPath id="word-part"><rect x="278" y="59" width="486" height="201"/></clipPath>
        </defs>
        <rect x="132" y="250" width="26" height="26" fill="#9C9C9C"/>
        <rect x="133" y="250" width="24" height="23" fill="#FFF"/>
        <rect x="137.5" y="274" width="14" height="31" fill="#8F8F8F"/>
        <rect x="139" y="274" width="11" height="31" fill="#FFF"/>
        <use href="#art" clip-path="url(#ring-part)"/>
        <use class="wordmark" href="#art" clip-path="url(#word-part)"/>
      </svg>
    </a>
  </div>
""".replace("__HOME__", HOME)

PAGE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="/favicon.ico">
<style>
{css}</style>
</head>
<body>
{filter}
<header class="top">
{badge}  <div class="intro">
{intro}
  </div>
</header>

<main>
{main}
</main>

<footer class="hem">
  <span>The Sandberg family</span>
  <nav aria-label="Elsewhere">
{nav}
  </nav>
</footer>
</body>
</html>
"""


def fail(msg):
    sys.exit(f"❌ build: {msg}")


def esc(t):
    return html.escape(t, quote=False)


def attr(t):
    return html.escape(t, quote=True)


def inline(text, where):
    """Escape, then bold, italic and links. Link targets are checked."""
    t = esc(text)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        if not (url.startswith(("https://", "mailto:")) or re.fullmatch(r"/[A-Za-z0-9_./-]*", url)):
            fail(f"{where}: link to {url!r}: only https:, mailto: and paths on this site are allowed")
        return f'<a href="{attr(url)}">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    if "[" in t and "](" in t:
        fail(f"{where}: unparsed link in {text[:60]!r}")
    return t


def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        fail(f"{path.relative_to(ROOT)}: no front matter block")
    meta = {}
    for line in m.group(1).splitlines():
        line = re.sub(r"\s+#.*$", "", line)
        k, sep, v = line.partition(":")
        if not sep:
            fail(f"{path.relative_to(ROOT)}: bad front matter line {line!r}")
        meta[k.strip()] = v.strip()
    for k in ("name", "blurb", "updated"):
        if not meta.get(k):
            fail(f"{path.relative_to(ROOT)}: front matter needs {k}")
    unknown = set(meta) - {"name", "blurb", "updated", "order"}
    if unknown:
        fail(f"{path.relative_to(ROOT)}: unknown front matter {sorted(unknown)}")
    where = str(path.relative_to(ROOT))
    blocks = [b for b in re.split(r"\n\s*\n", m.group(2).strip("\n")) if b.strip()]
    out, title = [], None
    for b in blocks:
        lines = b.strip("\n").splitlines()
        if lines[0].startswith("# "):
            if title or len(lines) != 1:
                fail(f"{where}: one '# Title' line, first, on its own")
            title = lines[0][2:].strip()
            # the title and the date are in the page's header, not its body
        elif lines[0].startswith("## "):
            if len(lines) != 1:
                fail(f"{where}: a '## ' heading is one line: {lines[0][:50]!r}")
            out.append(f"<h2>{inline(lines[0][3:].strip(), where)}</h2>")
        elif lines[0].startswith("- "):
            if not all(l.startswith("- ") for l in lines):
                fail(f"{where}: a list is only '- ' lines, one per item: {lines[0][:50]!r}")
            out.append("<ul>")
            out += [f"<li>{inline(l[2:].strip(), where)}</li>" for l in lines]
            out.append("</ul>")
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines), where)}</p>")
    if not title:
        fail(f"{where}: no '# Title'")
    return meta, title, "\n".join(out)


MADE_BY = "Made by the Sandberg family"


def intro(headline, sub, made):
    return "\n".join(f"    {l}" for l in (f"<h1>{esc(headline)}</h1>", f'<p class="sub">{esc(sub)}</p>', f'<p class="made">{esc(made)}</p>'))


def render(title, description, head, main, nav):
    return PAGE.format(title=esc(title), description=attr(description), css=CSS, filter=FILTER, badge=BADGE,
                       intro=head, main=main, nav="\n".join(f"    {n}" for n in nav))


def build():
    apps = []
    for path in sorted(SRC.glob("*/policy.md")):
        slug = path.parent.name
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            fail(f"src/{slug}: an app folder is lowercase letters, digits and hyphens")
        meta, title, body = parse(path)
        apps.append((slug, meta, title, body))
    if not apps:
        fail("no src/<app>/policy.md")
    pages = {}
    mail = f'<a href="mailto:{CONTACT}">{CONTACT}</a>'
    for slug, meta, title, body in apps:
        nav = ['<a href="/">All policies</a>', f'<a href="{HOME}">pdxfixit.com</a>', mail]
        head = intro(title, meta["blurb"], f'{MADE_BY} \u00b7 Last updated {meta["updated"]}')
        pages[f"{slug}/index.html"] = render(title, f'{meta["name"]}: {meta["blurb"]}. {title}.', head, body, nav)
    apps.sort(key=lambda a: (int(a[1].get("order", 1000)), a[1]["name"].lower()))
    items = "\n".join(f'    <li><a href="/{s}/"><b>{esc(m["name"])}</b><span>{esc(m["blurb"])}</span></a></li>'
                      for s, m, _, _ in apps)
    index = f'<ul class="apps">\n{items}\n</ul>'
    head = intro("Privacy policies", "What each app keeps, what it sends, and how to delete it.", MADE_BY)
    pages["index.html"] = render("PDXfixIT privacy policies", "The privacy policy for each app the Sandberg family makes.",
                                 head, index, [f'<a href="{HOME}">pdxfixit.com</a>', mail])
    return pages


def main():
    check = "--check" in sys.argv[1:]
    if [a for a in sys.argv[1:] if a != "--check"]:
        sys.exit(__doc__)
    pages = build()
    if check:
        bad = False
        for rel, want in pages.items():
            p = PUBLIC / rel
            if not p.exists() or p.read_text(encoding="utf-8") != want:
                print(f"❌ public/{rel} is not what build.py makes: run python3 build.py and commit")
                bad = True
        # a page in public/ that no source makes is a hand edit or a leftover
        for p in PUBLIC.glob("*/index.html"):
            if str(p.relative_to(PUBLIC)) not in pages:
                print(f"❌ public/{p.relative_to(PUBLIC)} has no src/{p.parent.name}/policy.md")
                bad = True
        if bad:
            sys.exit(1)
        print(f"✅ public/ is a clean build ({len(pages)} pages)")
        return
    for rel, text in pages.items():
        p = PUBLIC / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"✅ public/{rel} {len(text.encode()):,} bytes")


if __name__ == "__main__":
    main()
