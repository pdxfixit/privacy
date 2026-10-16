# Rules for agents working in this repo

This repo makes https://privacy.pdxfixit.com/. The README explains everything; these are the rules that are easy to
break and that CI or a reader will catch.

- **Never edit `public/<app>/index.html` or `public/index.html` by hand.** They are generated. Edit `src/`, run
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
- **Push to `main`.** A push deploys. Check the run (the `deploy` workflow) before saying a change is live.
