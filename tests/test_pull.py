"""pull.py: copies a pulled policy exactly, refuses what is not a policy, writes nothing on a failure."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = "---\nname: Demo\nblurb: A demo\nupdated: 1 January 2026\n---\n# Demo privacy policy\n\n@include rules\n"


class PullTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.host = Path(self.tmp.name) / "host"
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "pulled.txt").write_text("# note\n\ndemo acme/demo docs/policy.md\n")
        (self.repo / "pull.py").write_text((ROOT / "pull.py").read_text())
        self.serve("main", POLICY)

    def serve(self, ref, text):
        f = self.host / "acme" / "demo" / ref / "docs" / "policy.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)

    def run_pull(self, *args, ref=None):
        env = dict(os.environ, PULL_HOST=self.host.as_uri())
        env.pop("PULL_REF", None)
        if ref:
            env["PULL_REF"] = ref
        return subprocess.run([sys.executable, "-I", str(self.repo / "pull.py"), *args], env=env, capture_output=True, text=True)

    def dest(self):
        return self.repo / "src" / "demo" / "policy.md"

    def test_copies_the_file_exactly(self):
        r = self.run_pull()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.dest().read_text(), POLICY)

    def test_a_commit_is_read_at_that_commit(self):
        sha = "a" * 40
        self.serve(sha, POLICY.replace("A demo", "At a commit"))
        self.assertEqual(self.run_pull(ref=sha).returncode, 0)
        self.assertIn("At a commit", self.dest().read_text())

    def test_check_reports_a_difference_and_writes_nothing(self):
        self.assertEqual(self.run_pull().returncode, 0)
        self.serve("main", POLICY + "More.\n")
        r = self.run_pull("--check")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.dest().read_text(), POLICY)
        self.assertEqual(self.run_pull().returncode, 0)
        self.assertEqual(self.run_pull("--check").returncode, 0)

    def test_what_is_not_a_policy_is_refused_and_nothing_is_written(self):
        self.serve("main", "<html>404</html>")
        r = self.run_pull()
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(self.dest().exists())

    def test_a_missing_file_and_a_bad_ref_are_refused(self):
        (self.host / "acme" / "demo" / "main" / "docs" / "policy.md").unlink()
        self.assertNotEqual(self.run_pull().returncode, 0)
        self.assertNotEqual(self.run_pull(ref="main; rm -rf /").returncode, 0)


if __name__ == "__main__":
    unittest.main()
