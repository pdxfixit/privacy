# Rules for agents working in this repo

This repo makes https://privacy.pdxfixit.com/. The README explains everything; these are the rules that are easy to
break and that CI or a reader will catch.

- **Never edit `public/<app>/index.html`, `public/index.html` or `public/_headers` by hand.** They are generated. Edit `src/`, run
  `python3 build.py`, commit `src/` and `public/` together. The deploy runs `python3 build.py --check` and refuses a
  `public/` that `src/` would not build.
- **The index lists apps alphabetically by `name:` (case ignored), always.** The build sorts them; there is no
  `order:` key and no way to set one. Do not reorder `public/index.html` by hand (it fails the check) and do not add an
  ordering feature. Adding an app is one `src/<app>/policy.md`; it lands in its alphabetical place by itself.
- **Policy text is `src/<app>/policy.md`.** Text every app shares is written once in `src/_shared/<name>.md` and
  pulled in with `@include <name>`. Change shared wording there, not as a copy in each app. Never copy shared text
  into a policy.md.
- **Bump `updated:`** in the file you changed (a policy.md or a `_shared` file). A page shows the newest date among
  itself and its includes.
- **Apps supply policy text only.** This repo owns the look and the generation. Do not add a page generator, a
  stylesheet or HTML to an app repo, and do not copy generated HTML in here.
- **What the policies say is the owner's decision.** Do not change the wording of a policy, or what an app is said to
  collect, without the owner's approval. Layout and build changes are fine to make.
- **Never write the contact email address in plain text** (a policy, a README, a comment, a commit message you can
  avoid): write `{contact}` in a policy. The site hides it from spam harvesters and `build.py` refuses a plain address
  or a `mailto:` link. Do not add a plain `mailto:` link or another address by another route.
- **Do not add another origin, script or third-party request** (fonts, analytics, a CDN, an embed). The pages load
  nothing but their own files; the CSP in the generated `_headers` allows exactly that. The policies tell people so.
- **Keep `SECURITY_EXPIRES` in `build.py` in the future** (`security.txt`); `build.py` warns in its last 60 days.
- **Land with `just land`**, from your own branch (a worktree): flarepress's shared tool pulls `main` from GitHub first,
  cherry-picks your commits, runs `just test` (`build.py --check`), and pushes. A push deploys. Check the run (the
  `deploy` workflow) before saying a change is live.
