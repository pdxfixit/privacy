"""tools/take.sh: takes an app's policy, builds, tests and commits it; refuses what is not safe; undoes a failure."""
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = "---\nname: Demo\nblurb: A demo\nupdated: 1 January 2026\n---\n# Demo privacy policy\n\n@include rules\n\n## What Demo keeps\n\n- Nothing.\n"
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]


class TakeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.repo = tmp / "privacy"
        # A copy of this repo's files with a stub justfile, so `just test` here is the build check alone (not these tests again).
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__"))
        (self.repo / "justfile").write_text("test:\n    python3 build.py --check\n")
        (self.repo / "src" / "demo").mkdir()
        (self.repo / "src" / "demo" / "policy.md").write_text(POLICY)
        self.git("init", "-q", "-b", "main")
        subprocess.run(["python3", "build.py"], cwd=self.repo, check=True, capture_output=True)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "start")
        self.file = tmp / "app" / "privacy-policy.md"
        self.file.parent.mkdir()
        self.file.write_text(POLICY)

    def git(self, *args):
        return subprocess.run([*GIT, *args], cwd=self.repo, capture_output=True, text=True, check=True).stdout.strip()

    def take(self, app="demo", file=None, **env):
        e = {k: v for k, v in os.environ.items() if not k.startswith("TAKE_")}
        e.update(env)
        return subprocess.run(["bash", str(self.repo / "tools" / "take.sh"), app, str(file or self.file)], cwd=self.repo, env=e, capture_output=True, text=True)

    def head(self):
        return self.git("rev-parse", "HEAD")

    def test_nothing_changed_says_so_and_commits_nothing(self):
        before = self.head()
        r = self.take()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing changed", r.stdout)
        self.assertEqual(self.head(), before)

    def test_a_changed_policy_is_copied_built_and_committed_with_the_sha_message(self):
        self.file.write_text(POLICY.replace("Nothing.", "Little.").replace("1 January 2026", "2 January 2026"))
        r = self.take(TAKE_SHA="0123456789abcdef")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.repo / "src/demo/policy.md").read_bytes(), self.file.read_bytes())
        self.assertIn("Little.", (self.repo / "public/demo/index.html").read_text())
        self.assertEqual(self.git("log", "-1", "--format=%s"), "docs: Demo: policy from demo@0123456")
        self.assertEqual(sorted(self.git("show", "--name-only", "--format=").split("\n")), ["public/demo/index.html", "src/demo/policy.md"])
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_take_message_wins(self):
        self.file.write_text(POLICY.replace("Nothing.", "Little.").replace("1 January 2026", "2 January 2026"))
        r = self.take(TAKE_SHA="0123456", TAKE_MESSAGE="docs: my words")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.git("log", "-1", "--format=%s"), "docs: my words")

    def test_refuses_a_changed_text_with_the_same_updated(self):
        self.file.write_text(POLICY.replace("Nothing.", "Little."))
        before = self.head()
        r = self.take()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("bump updated:", r.stderr)
        self.assertEqual(self.head(), before)
        self.assertIn("Nothing.", (self.repo / "src/demo/policy.md").read_text())

    def test_refuses_an_app_folder_that_does_not_exist(self):
        r = self.take(app="nope")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no src/nope", r.stderr)
        self.assertFalse((self.repo / "src" / "nope").exists())

    def test_refuses_shared_and_odd_app_names(self):
        for app in ("_shared", "../x", "Demo"):
            self.assertNotEqual(self.take(app=app).returncode, 0, app)

    def test_refuses_a_file_that_is_not_a_policy(self):
        for text in ("# Just a page\n", "---\nname: X\nblurb: Y\n---\nbody\n", "---\nname: X\nupdated: 3 May 2026\n---\nbody\n", "---\nname: X\nblurb: Y\nupdated: 3 May 2026\n"):
            self.file.write_text(text)
            r = self.take()
            self.assertNotEqual(r.returncode, 0, text)
            self.assertIn("take:", r.stderr)
        self.assertEqual((self.repo / "src/demo/policy.md").read_text(), POLICY)

    def test_refuses_uncommitted_changes_here(self):
        rules = self.repo / "src" / "_shared" / "rules.md"
        rules.write_text(rules.read_text() + "\n")
        r = self.take()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("uncommitted", r.stderr)

    def test_a_policy_the_build_refuses_is_put_back(self):
        # A plain address is an error in build.py; the failed take leaves src/ and public/ as committed.
        self.file.write_text(POLICY.replace("Nothing.", "Write to someone@example.com.").replace("1 January 2026", "2 January 2026"))
        before = self.head()
        r = self.take()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.head(), before)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual((self.repo / "src/demo/policy.md").read_text(), POLICY)


if __name__ == "__main__":
    unittest.main()
