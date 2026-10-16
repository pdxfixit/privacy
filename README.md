# PDXfixIT privacy policies

The privacy policy for each PDXfixIT app, served at https://privacy.pdxfixit.com/ by a Cloudflare Worker (static
assets only).

- Arrow-Rama (Android and Wear OS puzzle game): https://privacy.pdxfixit.com/arrowrama/

## This repo owns the pages

An app supplies its policy **text**. This repo owns how every page looks and how it is made, so the pages stay
consistent with each other and with pdxfixit.com, and no app repo needs a page generator.

- `src/<app>/policy.md`: the policy text for one app. A front matter block (`name`, `blurb`, `updated`, optional
  `order`), then a small Markdown subset. `build.py` documents it at the top.
- `build.py`: `python3 build.py` writes `public/<app>/index.html` and the index, `public/index.html`.
  `python3 build.py --check` fails if `public/` is not exactly what `src/` builds. Stdlib only, no network.
- Change the text: edit `src/<app>/policy.md` (and `updated`), run `python3 build.py`, commit both. Do not edit
  `public/<app>/index.html` or `public/index.html` by hand: the deploy refuses a `public/` that `build.py` would not make.
- Add an app: add `src/<app>/policy.md`, run `python3 build.py`. The index lists it.

## Hosting (same shape as pdxfixit/website)

- `public/`: the site. `_headers` sets the security headers; `.assetsignore` keeps non-site files out. The logo,
  font and favicon here are kept by hand and shared by every page.
- `site/wrangler.toml`: the Worker `privacy-pdxfixit-com` and its Custom Domain `privacy.pdxfixit.com`.
- `site/verify.sh`: after a deploy, every live page and its CSP header must match `public/` and `_headers`.
- `.github/workflows/deploy.yml`: every push to `main` runs `build.py --check`, deploys through
  [flarepress](https://github.com/pdxfixit/flarepress) with this repo's secrets `CLOUDFLARE_API_TOKEN` and
  `CLOUDFLARE_ACCOUNT_ID`, then runs `site/verify.sh`.

GitHub Pages is off; the old address (pdxfixit.github.io/arrowrama-privacy/) no longer serves.
