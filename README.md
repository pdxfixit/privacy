# Arrow-Rama privacy policy

Privacy policies for PDXfixIT apps, served at https://privacy.pdxfixit.com/ by a Cloudflare Worker (static assets
only). One folder per app under `public/`; `public/index.html` is the index that links to each.

- Arrow-Rama (Android and Wear OS puzzle game): https://privacy.pdxfixit.com/arrowrama/

`public/arrowrama/index.html` is built from the game's policy text by its own tool. Change the text there and publish
the rebuilt page; do not edit it here by hand. Every push to `main` deploys.

To add an app: put its page at `public/<app>/index.html` and add a link to `public/index.html`.

## Hosting (same shape as pdxfixit/website)

- `public/`: the site. `_headers` sets the security headers; `.assetsignore` keeps non-site files out.
- `site/wrangler.toml`: the Worker `privacy-pdxfixit-com` and its Custom Domain `privacy.pdxfixit.com`.
- `site/verify.sh`: after a deploy, every live page must match its `public/**/index.html` byte for byte.
- `.github/workflows/deploy.yml`: deploys through [flarepress](https://github.com/pdxfixit/flarepress) with this repo's
  secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.

GitHub Pages is off; the old address (pdxfixit.github.io/arrowrama-privacy/) no longer serves.
