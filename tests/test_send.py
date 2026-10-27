"""tools/send.sh (each app's `just policy` runs it): copies an app's policy into this repo through `just take`, in a
throwaway worktree of origin/main, then `just land` there; a dry run only shows what would land.

The privacy repo here is a stand-in: a copy of send.sh, a stub take.sh that copies the file and commits it (the real
take.sh is tested in test_take.py), and a justfile whose `land` leaves a marker. The app is a scratch repo with its
own bare origin. Nothing touches the network or a real checkout."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
POLICY = "---\nname: Demo\nblurb: A demo\nupdated: 1 January 2026\n---\n# Demo privacy policy\n"
TAKE = """#!/usr/bin/env bash
set -eu
app=$1; file=$2
mkdir -p "src/$app"
cp "$file" "src/$app/policy.md"
git add "src/$app/policy.md"
git diff --cached --quiet && { echo "take: nothing changed"; exit 0; }
git -c user.name=t -c user.email=t@example.invalid commit -q -m "docs: policy from $app@${TAKE_SHA:0:7}"
"""
JUSTFILE = 'take app file:\n    bash tools/take.sh {{app}} {{file}}\n\nland:\n    { echo "$PWD"; ls; } > "$LANDED"\n'


def git(cwd, *args):
    return subprocess.run([*GIT, *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@unittest.skipUnless(shutil.which("just"), "just is not installed")
class Send(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # The privacy repo: an origin, and a checkout of it on main beside the app.
        seed = self.tmp / "seed"
        (seed / "tools").mkdir(parents=True)
        shutil.copy(ROOT / "tools" / "send.sh", seed / "tools" / "send.sh")
        (seed / "tools" / "take.sh").write_text(TAKE)
        (seed / "justfile").write_text(JUSTFILE)
        (seed / "src" / "demo").mkdir(parents=True)
        (seed / "src" / "demo" / "policy.md").write_text(POLICY)
        git(seed, "init", "-q", "-b", "main")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "start")
        self.priv_origin = self.tmp / "privacy.git"
        git(self.tmp, "clone", "-q", "--bare", str(seed), str(self.priv_origin))
        self.privacy = self.tmp / "work" / "privacy"
        git(self.tmp, "clone", "-q", str(self.priv_origin), str(self.privacy))
        # The app, with its own origin so that HEAD can be on origin/main.
        self.app = self.tmp / "work" / "app"
        (self.app / "docs").mkdir(parents=True)
        (self.app / "docs" / "privacy-policy.md").write_text(POLICY.replace("1 January", "2 January"))
        git(self.app, "init", "-q", "-b", "main")
        git(self.app, "add", "-A")
        git(self.app, "commit", "-q", "-m", "app")
        self.app_origin = self.tmp / "app.git"
        git(self.tmp, "clone", "-q", "--bare", str(self.app), str(self.app_origin))
        git(self.app, "remote", "add", "origin", str(self.app_origin))
        git(self.app, "fetch", "-q", "origin")
        self.landed = self.tmp / "landed"

    def send(self, *args, app="demo", file="docs/privacy-policy.md", cwd=None, **env):
        e = {k: v for k, v in os.environ.items() if not k.startswith(("PRIVACY", "SEND_"))}
        e.update(LANDED=str(self.landed), **{k: str(v) for k, v in env.items()})
        return subprocess.run(["bash", str(self.privacy / "tools" / "send.sh"), app, file, *args],
                              cwd=cwd or self.app, env=e, capture_output=True, text=True)

    def worktrees(self):
        return [l for l in git(self.privacy, "worktree", "list", "--porcelain").splitlines() if l.startswith("worktree ")]

    def push_from_elsewhere(self, name, text):
        other = self.tmp / f"other-{name}"
        git(self.tmp, "clone", "-q", str(self.priv_origin), str(other))
        (other / "NEWS").write_text(text)
        git(other, "add", "-A")
        git(other, "commit", "-q", "-m", name)
        git(other, "push", "-q", "origin", "main")
        return other

    def test_a_dry_run_shows_the_commit_and_leaves_the_privacy_checkout_alone(self):
        before = git(self.privacy, "rev-parse", "HEAD")
        r = self.send("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        sha = git(self.app, "rev-parse", "HEAD")[:7]
        self.assertIn(f"docs: policy from demo@{sha}", r.stdout)
        self.assertIn("nothing landed", r.stdout)
        self.assertFalse(self.landed.exists())
        self.assertEqual(git(self.privacy, "rev-parse", "HEAD"), before)
        self.assertEqual(git(self.privacy, "status", "--porcelain"), "")
        self.assertEqual(len(self.worktrees()), 1, "the scratch worktree is gone")
        self.assertEqual(git(self.privacy, "branch", "--list", "send-*"), "", "and its branch")

    def test_it_takes_and_lands_in_a_throwaway_worktree_when_head_is_on_origin_main(self):
        r = self.send()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        where = Path(self.landed.read_text().splitlines()[0])
        self.assertIn("send-privacy.", where.name, "land ran in the scratch worktree, not the checkout")
        self.assertEqual(len(self.worktrees()), 1, "and it is removed after a landing")
        self.assertEqual(git(self.privacy, "branch", "--list", "send-*"), "")
        self.assertEqual(git(self.privacy, "rev-parse", "HEAD"), git(self.priv_origin, "rev-parse", "main"), "the checkout's own main is untouched")

    def test_the_take_commit_is_on_a_branch_of_its_own_for_land_to_pick_up(self):
        (self.privacy / "justfile").write_text(JUSTFILE.replace('{ echo "$PWD"; ls; } > "$LANDED"', 'git log -1 --format=%s > "$LANDED"; git branch --show-current >> "$LANDED"'))
        git(self.privacy, "commit", "-q", "-am", "land shows the branch")
        git(self.privacy, "push", "-q", "origin", "main")
        r = self.send()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        subject, branch = self.landed.read_text().splitlines()
        self.assertTrue(subject.startswith("docs: policy from demo@"), subject)
        self.assertTrue(branch.startswith("send-demo-"), branch)

    def test_it_will_not_land_a_head_that_is_not_on_origin_main(self):
        (self.app / "docs" / "x.md").write_text("x")
        git(self.app, "add", "-A")
        git(self.app, "commit", "-q", "-m", "local only")
        r = self.send()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not on the app's origin/main", r.stderr)
        self.assertFalse(self.landed.exists())
        self.assertEqual(self.send("--dry-run").returncode, 0, "a dry run does not mind")

    def test_it_refuses_an_uncommitted_policy(self):
        policy = self.app / "docs" / "privacy-policy.md"
        policy.write_text(policy.read_text() + "more\n")
        r = self.send("--dry-run")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("uncommitted", r.stderr)
        git(self.app, "checkout", "--", "docs/privacy-policy.md")
        git(self.app, "rm", "-q", "--cached", "docs/privacy-policy.md")
        r = self.send("--dry-run")
        self.assertNotEqual(r.returncode, 0, "a policy that is not committed at all")
        self.assertIn("uncommitted", r.stderr)
        self.assertEqual(git(self.privacy, "worktree", "list").count("\n"), 0)

    def test_it_runs_from_a_subdirectory_and_a_worktree_of_the_app(self):
        git(self.app, "worktree", "add", "-q", "--detach", str(self.tmp / "wt"), "main")
        r = self.send("--dry-run", cwd=self.tmp / "wt")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        r = self.send("--dry-run", file="privacy-policy.md", cwd=self.app / "docs")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_a_clean_checkout_on_main_is_fast_forwarded_and_the_worktree_starts_from_the_newest(self):
        self.push_from_elsewhere("newer", "n")
        r = self.send("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(git(self.privacy, "log", "-1", "--format=%s"), "newer")

    def test_a_checkout_on_another_branch_is_left_alone_but_the_worktree_is_origin_main(self):
        git(self.privacy, "checkout", "-q", "-b", "mine")
        (self.privacy / "MINE").write_text("m")
        git(self.privacy, "add", "-A")
        git(self.privacy, "commit", "-q", "-m", "mine")
        self.push_from_elsewhere("newer", "n")
        r = self.send()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(git(self.privacy, "branch", "--show-current"), "mine")
        self.assertEqual(git(self.privacy, "log", "-1", "--format=%s"), "mine")
        files = self.landed.read_text().splitlines()
        self.assertIn("NEWS", files, "the worktree is GitHub's newest main")
        self.assertNotIn("MINE", files, "and not the checkout's own branch")

    def test_a_diverged_main_stops_it(self):
        (self.privacy / "LOCAL").write_text("l")
        git(self.privacy, "add", "-A")
        git(self.privacy, "commit", "-q", "-m", "local")
        self.push_from_elsewhere("newer", "n")
        r = self.send("--dry-run")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("diverged", r.stderr)

    def test_a_newer_send_sh_on_main_runs_from_the_top(self):
        other = self.push_from_elsewhere("newer-send", "n")
        sh = other / "tools" / "send.sh"
        sh.write_text(sh.read_text().replace("set -euo pipefail\n", 'set -euo pipefail\necho "send: newest script"\n', 1))
        git(other, "commit", "-q", "-am", "new send.sh")
        git(other, "push", "-q", "origin", "main")
        r = self.send("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(r.stdout.count("send: newest script"), 1, "once: the old copy re-runs itself, not twice")

    def test_nothing_changed_lands_nothing(self):
        (self.privacy / "src" / "demo" / "policy.md").write_text((self.app / "docs" / "privacy-policy.md").read_text())
        git(self.privacy, "add", "-A")
        git(self.privacy, "commit", "-q", "-m", "already there")
        git(self.privacy, "push", "-q", "origin", "main")
        r = self.send()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("nothing to land", r.stdout)
        self.assertFalse(self.landed.exists())
        self.assertEqual(len(self.worktrees()), 1)

    def test_a_privacy_repo_without_take_says_its_change_must_land_first(self):
        git(self.privacy, "rm", "-q", "tools/take.sh")
        git(self.privacy, "commit", "-q", "-m", "no take")
        git(self.privacy, "push", "-q", "origin", "main")
        r = self.send("--dry-run")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no tools/take.sh", r.stderr)
        self.assertEqual(len(self.worktrees()), 1)

    def test_a_take_that_stops_commits_and_lands_nothing(self):
        (self.privacy / "tools" / "take.sh").write_text('#!/usr/bin/env bash\necho "take: bump updated:" >&2\nexit 1\n')
        git(self.privacy, "commit", "-q", "-am", "strict take")
        git(self.privacy, "push", "-q", "origin", "main")
        r = self.send()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("bump updated:", r.stderr)
        self.assertFalse(self.landed.exists())
        self.assertEqual(len(self.worktrees()), 1)

    def test_a_land_that_fails_keeps_the_worktree_and_says_where(self):
        (self.privacy / "justfile").write_text(JUSTFILE.replace('{ echo "$PWD"; ls; } > "$LANDED"', "exit 3"))
        git(self.privacy, "commit", "-q", "-am", "land fails")
        git(self.privacy, "push", "-q", "origin", "main")
        r = self.send()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("just land stopped in", r.stderr)
        self.assertEqual(len(self.worktrees()), 2, "kept for the person to fix")

    def test_odd_arguments_are_refused(self):
        for args, kw in (((), {"app": "_shared"}), ((), {"app": "../x"}), ((), {"app": "Demo"}), (("--now",), {}), (("extra",), {}), ((), {"file": "docs/nope.md"})):
            r = self.send(*args, **kw)
            self.assertNotEqual(r.returncode, 0, (args, kw))
            self.assertIn("send:", r.stderr)
        self.assertEqual(self.worktrees(), [self.worktrees()[0]])


if __name__ == "__main__":
    unittest.main()
