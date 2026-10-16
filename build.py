#!/usr/bin/env python3
"""Build privacy.pdxfixit.com: src/<app>/policy.md -> public/<app>/index.html, plus public/index.html.

This repo owns how every policy page looks and how it is made. An app supplies only its policy text,
as src/<app>/policy.md; it does not ship a page.

    python3 build.py          # write public/ (the pages and _headers; the logo, font and favicon are kept by hand)
    python3 build.py --check  # build in memory and fail if public/ differs: CI runs this before deploying

Stdlib only, no network. The output is byte-for-byte the same every run.

A policy.md starts with a front matter block, then a small Markdown subset:

    ---
    name: Arrow-Rama                              # the app's name, as the index lists it
    blurb: A puzzle game for Android and Wear OS  # the subheadline under the title, and the line under the name on the index
    updated: 16 October 2026                      # shown as "Last updated" in the header
    url: https://isopix.app/                      # optional: where to get the app (https only); the index links it
    ---
    # Title                  one per page, first: the headline in the page header (it is not repeated in the body)
    ## Heading
    A paragraph. **bold**, *italic*, [a link](https://example.com) or the protected contact address: {contact}
    - a list item, one line each

Links may go to https: or a path on this site; anything else is an error. An email address or a mailto: link in the
text is an error: write {contact}, which builds the address in the browser so a spam harvester cannot read it.

Shared text, written once: src/_shared/<name>.md holds blocks every app uses (the same Markdown subset, with front
matter `updated:` only, no '# Title', no @include). A policy pulls one in with a line of its own:

    @include rules

A page's "Last updated" is the newest of its own `updated:` and the `updated:` of every partial it includes, so
changing shared text and bumping the partial's date updates every page that includes it. An app's own sections stay
in its policy.md.
"""
import base64, datetime, hashlib, html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, PUBLIC = ROOT / "src", ROOT / "public"
HOME = "https://pdxfixit.com/"
# The contact address is never written out in plain text in this repo or on a page: a spam harvester that reads the
# HTML or the source finds nothing. It is stored here reversed and base64-encoded; a page carries the same string in
# data-c, and one small inline script (allowed by hash in the CSP) turns it into a mailto link in the browser. With
# scripts off, a reader sees "privacy at pdxfixit dot com". Write {contact} in a policy to place it.
CONTACT_ENC = "bW9jLnRpeGlmeGRwQHljYXZpcnA="
CONTACT = base64.b64decode(CONTACT_ENC).decode()[::-1]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}")
SCRIPT = ('for(const e of document.querySelectorAll("[data-c]")){const a=atob(e.dataset.c).split("").reverse().join(""),'
          'l=document.createElement("a");l.href="mailto:"+a;l.textContent=a;e.replaceChildren(l)}')
SCRIPT_HASH = base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()

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
ul.apps li{margin:0;border-bottom:1px solid var(--rule);display:flex;align-items:center;gap:12px;min-height:5.5rem}
ul.apps a.pol{display:block;flex:1;min-width:0;padding:1rem 0;text-decoration:none;color:var(--ink)}
ul.apps b{display:block;font:400 1.6rem/1.2 var(--serif);color:var(--link);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.2em}
ul.apps a:hover b{text-decoration-thickness:2px}
ul.apps a.go{flex:none;display:flex;align-items:center;justify-content:center;width:48px;height:48px;border:1px solid var(--rule);border-radius:12px;font-size:1.5rem;line-height:1;text-decoration:none}
ul.apps a.go:hover{border-color:var(--link)}
ul.apps span{color:var(--muted)}
.hem{display:flex;flex-wrap:wrap;justify-content:flex-start;gap:6px 24px;padding:14px var(--gutter) 20px;font-size:16px;color:var(--muted);border-top:1px solid var(--rule)}
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
    <a href="/" aria-label="PDXfixIT privacy policies">
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
"""

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
  <nav aria-label="Elsewhere">
{nav}
  </nav>
</footer>
<script>{script}</script>
</body>
</html>
"""


HEADERS = """\
# Response headers for Cloudflare Workers Static Assets (this file is not served).
# Generated by build.py: do not edit by hand (the script hash must match the pages' one inline script).
# no-cache: browsers check for a new copy on every load, so a deploy shows up at once.
# The CSP allows this site's own images and font, inline styles, and the one inline script (by hash) that builds the
# contact link in the browser; nothing else, and no other origins. HSTS is not here: it is set once for the whole
# zone in Cloudflare (SSL/TLS, Edge Certificates), so every subdomain gets the same policy.
/*
  Cache-Control: no-cache
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Resource-Policy: same-origin
  Content-Security-Policy: default-src 'none'; script-src 'sha256-{hash}'; style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
"""


# RFC 9116. Contact is a link, not an email address, so no address is published here. Expires must be renewed at least
# yearly: move SECURITY_EXPIRES forward (build.py warns in the last 60 days).
SECURITY_EXPIRES = "2027-10-16T00:00:00.000Z"
SECURITY_TXT = f"""\
Contact: https://github.com/pdxfixit/privacy/security/advisories/new
Expires: {SECURITY_EXPIRES}
Preferred-Languages: en
Canonical: https://privacy.pdxfixit.com/.well-known/security.txt
"""


def fail(msg):
    sys.exit(f"❌ build: {msg}")


def esc(t):
    return html.escape(t, quote=False)


def attr(t):
    return html.escape(t, quote=True)


def inline(text, where):
    """Escape, then bold, italic and links. Link targets are checked; {contact} is the protected address."""
    if EMAIL.search(text) or "mailto:" in text:
        fail(f"{where}: no email address or mailto: link in the text; write {{contact}} instead: {text[:60]!r}")
    t = esc(text)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        if not (url.startswith("https://") or re.fullmatch(r"/[A-Za-z0-9_./-]*", url)):
            fail(f"{where}: link to {url!r}: only https: and paths on this site are allowed")
        return f'<a href="{attr(url)}">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    if "[" in t and "](" in t:
        fail(f"{where}: unparsed link in {text[:60]!r}")
    return t.replace("{contact}", contact_html())


def contact_html():
    spoken = CONTACT.replace("@", " at ").replace(".", " dot ")
    return f'<span class="contact" data-c="{CONTACT_ENC}">{spoken}</span>'


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def parse_date(text, where):
    m = re.fullmatch(r"(\d{1,2}) (%s) (\d{4})" % "|".join(MONTHS), text)
    if not m:
        fail(f"{where}: updated: {text!r} is not a date like '16 October 2026'")
    return int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1))


def show_date(d):
    return f"{d[2]} {MONTHS[d[1] - 1]} {d[0]}"


def front_matter(path, allowed, required):
    where = str(path.relative_to(ROOT))
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        fail(f"{where}: no front matter block")
    meta = {}
    for line in m.group(1).splitlines():
        line = re.sub(r"\s+#.*$", "", line)
        k, sep, v = line.partition(":")
        if not sep:
            fail(f"{where}: bad front matter line {line!r}")
        meta[k.strip()] = v.strip()
    for k in required:
        if not meta.get(k):
            fail(f"{where}: front matter needs {k}")
    unknown = set(meta) - set(allowed)
    if unknown:
        fail(f"{where}: unknown front matter {sorted(unknown)}")
    return meta, [b for b in re.split(r"\n\s*\n", m.group(2).strip("\n")) if b.strip()], where


def load_shared(name, where):
    """A shared partial, src/_shared/<name>.md: front matter `updated`, then blocks. Returns (date, blocks)."""
    path = SRC / "_shared" / f"{name}.md"
    if not path.is_file():
        fail(f"{where}: @include {name}: there is no src/_shared/{name}.md")
    meta, blocks, pwhere = front_matter(path, {"updated"}, ("updated",))
    for b in blocks:
        first = b.strip("\n").splitlines()[0]
        if first.startswith("# ") or first.startswith("@include"):
            fail(f"{pwhere}: a shared partial has no '# Title' and no @include: {first[:50]!r}")
    return parse_date(meta["updated"], pwhere), blocks


def parse(path):
    meta, blocks, where = front_matter(path, {"name", "blurb", "updated", "url"}, ("name", "blurb", "updated"))
    if "url" in meta and not re.fullmatch(r"https://[a-z0-9.-]+(/[^\s\"<>]*)?", meta["url"]):
        fail(f"{where}: url is one https: address")
    date = parse_date(meta["updated"], where)
    expanded = []
    for b in blocks:
        lines = b.strip("\n").splitlines()
        inc = re.fullmatch(r"@include ([a-z0-9-]+)", b.strip())
        if inc:
            pdate, pblocks = load_shared(inc.group(1), where)
            date = max(date, pdate)
            expanded += pblocks
        elif any(l.startswith("@include") for l in lines):
            fail(f"{where}: an '@include name' is a line of its own, with blank lines around it")
        else:
            expanded.append(b)
    # the page is as new as the newest of its own text and the shared text it includes
    meta["updated"] = show_date(date)
    out, title = [], None
    for b in expanded:
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
                       intro=head, main=main, script=SCRIPT, nav="\n".join(f"    {n}" for n in nav))


def get_link(meta):
    """The index's button to the product itself, in the right margin of its row: Google Play for the Android apps,
    the site for the web apps. An app with no `url:` (not released yet) gets none, and its row is just as tall."""
    url = meta.get("url")
    if not url:
        return ""
    play = url.startswith("https://play.google.com/")
    label = f'Get {meta["name"]} on Google Play' if play else f'Open {meta["name"]}'
    return f'<a class="go" href="{esc(url)}" aria-label="{esc(label)}" title="{esc(label)}">{"&#x25B6;&#xFE0F;" if play else "&#x1F310;"}</a>'


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
    mail = contact_html()
    for slug, meta, title, body in apps:
        nav = ['<a href="/">All policies</a>', f'<a href="{HOME}">pdxfixit.com</a>', mail]
        head = intro(title, meta["blurb"], f'Last updated {meta["updated"]}')
        pages[f"{slug}/index.html"] = render(title, f'{meta["name"]}: {meta["blurb"]}. {title}.', head, body, nav)
    # The index is alphabetical by name, always: there is no way to set an order, so it cannot be put out of order.
    apps.sort(key=lambda a: (a[1]["name"].casefold(), a[0]))
    items = "\n".join(f'    <li><a class="pol" href="/{s}/"><b>{esc(m["name"])}</b><span>{esc(m["blurb"])}</span></a>{get_link(m)}</li>'
                      for s, m, _, _ in apps)
    index = f'<ul class="apps">\n{items}\n</ul>'
    head = intro("Privacy policies", "What each app keeps, what it sends, and how to delete it.", MADE_BY)
    pages["index.html"] = render("PDXfixIT privacy policies", "The privacy policy for each app the Sandberg family makes.",
                                 head, index, [f'<a href="{HOME}">pdxfixit.com</a>', mail])
    for rel, text in pages.items():
        if EMAIL.search(text):
            fail(f"public/{rel} would contain a plain email address: use {{contact}}")
    pages["_headers"] = HEADERS.format(hash=SCRIPT_HASH)
    pages[".well-known/security.txt"] = SECURITY_TXT
    return pages


def main():
    left = (datetime.datetime.strptime(SECURITY_EXPIRES[:10], "%Y-%m-%d").date() - datetime.date.today()).days
    if left < 60:
        print(f"⚠️ security.txt Expires is {'past' if left < 0 else 'in ' + str(left) + ' days'}: move SECURITY_EXPIRES forward")
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
