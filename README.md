# Arrow-Rama privacy policy

The privacy policy for Arrow-Rama, an Android and Wear OS puzzle game. It is served at
https://privacy.pdxfixit.com/ by a Cloudflare Worker (static assets). The old GitHub Pages address,
https://pdxfixit.github.io/arrowrama-privacy/, keeps working until it is retired on purpose.

`index.html` is built from the game's policy text by its own tool. Change the text there and publish the rebuilt page;
do not edit `index.html` here by hand.

## Hosting

- `wrangler.jsonc` defines the Worker `privacy-pdxfixit-com` and attaches the custom domain `privacy.pdxfixit.com`.
- `.assetsignore` lists the files that are not part of the site. Anything new at the repo root that is not site
  content must be added there, or it will be published.
- `_headers` sets the security headers.
- Deploy with `npx wrangler deploy` from the repo root, using an account that holds the `pdxfixit.com` zone.
