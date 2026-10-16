# PDXfixIT privacy policies

The privacy policy for each app the Sandberg family makes, served at https://privacy.pdxfixit.com/ by a Cloudflare
Worker (static assets only, no script).

| App | Policy |
|---|---|
| Arrow-Rama (Android and Wear OS puzzle game) | https://privacy.pdxfixit.com/arrowrama/ |

The index at https://privacy.pdxfixit.com/ lists every app. GitHub Pages is not used. This repo was renamed from
`arrowrama-privacy`; GitHub redirects the old name for git, but update any remote or link that still uses it.

## This repo owns the pages

An app supplies its policy **text**. This repo owns how every page looks and how it is made, so the pages stay
consistent with each other and with pdxfixit.com, and no app repo needs a page generator.

```
src/<app>/policy.md      the policy text for one app (the only thing an app changes)
build.py                 src/ -> public/<app>/index.html and public/index.html
public/                  what is deployed: built pages, plus files kept by hand (below)
site/wrangler.toml       the Worker and its custom domain
site/verify.sh           after a deploy, checks the live site matches public/
.github/workflows/       deploy.yml
```

### Change a policy

1. Edit `src/<app>/policy.md`, and set `updated:` in its front matter to the new date.
2. Run `python3 build.py` and commit `src/` and `public/` together.
3. Push to `main`. The deploy does the rest.

Never edit `public/<app>/index.html` or `public/index.html` by hand. The deploy runs `python3 build.py --check` first
and fails if `public/` is not exactly what `src/` builds.

### Add an app

Add `src/<app>/policy.md` (the folder name is the URL path: lowercase letters, digits, hyphens) and run
`python3 build.py`. The index lists it, ordered by `order:` if set, else by name.

### The policy.md format

A front matter block, then a small Markdown subset. `build.py` documents it at the top and rejects anything else.

```
---
name: Arrow-Rama                              # the app's name, as the index lists it
blurb: A puzzle game for Android and Wear OS  # the subheadline, and the line under the name on the index
updated: 16 October 2026                      # "Last updated" in the page header
order: 10                                     # optional: lower first on the index
---
# Arrow-Rama privacy policy        the headline; one per page, first
## A heading
A paragraph with **bold**, *italic* and a [link](https://example.com).
- a list item, one line each
```

Links may go to `https:`, `mailto:` or a path on this site. A heading is one line, and a list is only `- ` lines.

### Preview locally

```
python3 build.py
python3 -m http.server -d public 8000     # http://localhost:8000/ (the _headers file is not applied locally)
```

`build.py` is stdlib-only, needs no network, and writes identical bytes every run.

## The look

The pages follow pdxfixit.com: the Newsreader serif, the brand brown (espresso in dark mode), orange accents, the
PDXfixIT badge at the top left, links back to pdxfixit.com. The CSS lives in `build.py`, so every page changes together.
The badge, the footer and the headline block are in the same file.

Three files in `public/` are kept by hand and shared by every page:

- `logo-art.webp`: the logo artwork behind the badge, copied from pdxfixit.com's source.
- `favicon.ico`: the favicon, from the same place.
- `newsreader.woff2`: a Newsreader variable font (weights 300 to 600) subset to printable ASCII plus
  `’ “ ” – — · ← → é ©`. A character outside that set falls back to Georgia. To add characters, fetch a new subset
  from Google Fonts with those characters in the `text=` parameter and replace the file.

## Hosting and deploy

- `site/wrangler.toml` defines the Worker `privacy-pdxfixit-com`, serves `public/`, and attaches the custom domain
  `privacy.pdxfixit.com`. `pdxfixit.com` must be a zone in the same Cloudflare account.
- `public/_headers` sets the response headers: no-cache, `nosniff`, a referrer policy and a strict CSP (no scripts, no
  other origins; this site's own images and font and inline styles only). It is not served as a file.
- `.github/workflows/deploy.yml` runs on every push to `main`, in this order:
  1. `python3 build.py --check`: `public/` is a clean build of `src/`.
  2. `wrangler deploy` through [flarepress](https://github.com/pdxfixit/flarepress), as pdxfixit/website does.
  3. `site/verify.sh`: every `public/**/index.html` is served byte for byte, with the CSP from `_headers`, five
     fetches in a row within 90 seconds. Cloudflare's edge can lag an upload, so one fetch proves nothing.
- Repo secrets: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. The token is this repo's own, scoped as
  pdxfixit/website's is: Workers Scripts: Edit, plus Workers Routes: Edit, DNS: Edit and Zone: Read on `pdxfixit.com`.
  No agent holds a token.
- To deploy by hand, from a checkout of flarepress: `just push /path/to/this/repo/site` (it uses
  `CLOUDFLARE_API_TOKEN` when set, else `wrangler login`). The workflow is the normal path.
- No `justfile` and no `site.conf`, as in pdxfixit/website: `build.py --check` and `site/verify.sh` do that work here.

### On the owner's Mac: the flarepress registry

flarepress's `just sites` (a read-only health check of every site) only sees site folders under
`~/.config/flarepress/sites/` (`$FLAREPRESS_SITES`). A name there may be a link to an app repo's `site/` folder. To
include this site:

```
ln -s /path/to/this/repo/site ~/.config/flarepress/sites/privacy.pdxfixit.com
just sites privacy.pdxfixit.com           # from a flarepress checkout
```

A folder without a `site.conf` is checked only for `/` answering 200; this site has no `site.conf`, so it is not
asked for `/version.json`.
