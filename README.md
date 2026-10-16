# Arrow-Rama privacy policy

The privacy policy for Arrow-Rama, an Android and Wear OS puzzle game, served at
https://privacy.pdxfixit.com/ by a Cloudflare Worker (static assets only).

`public/index.html` is built from the game's policy text by its own tool. Change the text there and publish the
rebuilt page; do not edit `public/index.html` here by hand. Every push to `main` deploys it.

## Hosting (same shape as pdxfixit/website)

- `public/`: the site. `_headers` sets the security headers; `.assetsignore` keeps non-site files out.
- `site/wrangler.toml`: the Worker `privacy-pdxfixit-com` and its Custom Domain `privacy.pdxfixit.com`.
- `site/verify.sh`: after a deploy, the live page must match `public/index.html` byte for byte.
- `.github/workflows/deploy.yml`: deploys through [flarepress](https://github.com/pdxfixit/flarepress) with this repo's
  secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.

The old GitHub Pages address (pdxfixit.github.io/arrowrama-privacy/) stopped serving when the page moved here.
