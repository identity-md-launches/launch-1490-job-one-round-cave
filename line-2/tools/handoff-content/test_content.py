"""Behavior checks: valid but different payloads, malformed expectations and CLI."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


content = load("content", Path(__file__).with_name("content.py"))
writer = load("writer", "line-2/tools/handoff/handoff.py")


class ContentTests(unittest.TestCase):
    def setUp(self):
        Path("test/scratch").mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir="test/scratch")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).relative_to(Path.cwd()) if Path(self.tmp.name).is_absolute() else Path(self.tmp.name)
        self.archive = self.root / "input.zip"
        self.expected = self.root / "expected.json"
        self.archive.write_bytes(writer.build({"a.txt": b"original", "nested/empty": b""}))
        self.expectation = content.capture(str(self.archive))
        self.save()

    def save(self):
        self.expected.write_text(json.dumps(self.expectation), encoding="utf-8")

    def check(self):
        return content.check(str(self.archive), str(self.expected))

    def test_real_demo(self):
        self.assertEqual(content.demo()["matched"], ["README.md", "handoff.py"])

    def test_roundtrip_nested_empty_and_unicode(self):
        self.assertTrue(self.check()["content_passed"])
        self.archive.write_bytes(writer.build({"é/🐸": b"hello"}))
        self.expectation = content.capture(str(self.archive))
        self.save()
        self.assertEqual(self.check()["matched"], ["é/🐸"])

    def test_valid_same_length_wrong_content(self):
        self.archive.write_bytes(writer.build({"a.txt": b"modified", "nested/empty": b""}))
        result = self.check()
        self.assertTrue(result["verified"])
        self.assertFalse(result["content_passed"])
        self.assertEqual(result["changed"][0]["path"], "a.txt")

    def test_expected_size_is_enforced(self):
        self.expectation["files"][0]["bytes"] += 1
        self.save()
        self.assertFalse(self.check()["content_passed"])

    def test_missing_and_extra(self):
        self.archive.write_bytes(writer.build({"a.txt": b"original", "extra": b"x"}))
        result = self.check()
        self.assertEqual(result["missing"], ["nested/empty"])
        self.assertEqual(result["unexpected"], ["extra"])
        self.assertFalse(result["content_passed"])

    def test_nonexact_allows_only_extras(self):
        self.archive.write_bytes(writer.build({"a.txt": b"original", "nested/empty": b"", "extra": b"x"}))
        self.assertFalse(self.check()["content_passed"])
        self.expectation["exact"] = False
        self.save()
        self.assertTrue(self.check()["content_passed"])

    def test_malformed_expectations(self):
        cases = []
        for path in ("/outside", "../outside", "a//b", "a/./b", "a\\b", "HANDOFF.json", "a\x00"):
            obj = copy.deepcopy(self.expectation)
            obj["files"][0]["path"] = path
            cases.append(obj)
        for key, value in (("bytes", True), ("bytes", -1), ("bytes", 2**100),
                           ("sha256", "z" * 64), ("sha256", "A" * 64)):
            obj = copy.deepcopy(self.expectation)
            obj["files"][0][key] = value
            cases.append(obj)
        obj = copy.deepcopy(self.expectation)
        obj["files"].append(obj["files"][0])
        cases.extend([obj, {**self.expectation, "exact": 1},
                      {**self.expectation, "files": []}, {**self.expectation, "extra": 1}])
        for obj in cases:
            with self.subTest(obj=obj), self.assertRaises(ValueError):
                content.parse_expectation(json.dumps(obj).encode())
        for raw in (b'{"exact":true,"exact":false}', b'{"x":NaN}', b'\xff', b'x' * (content.MAX_EXPECTATION + 1)):
            with self.assertRaises(ValueError):
                content.parse_expectation(raw)

    def test_corrupt_archive_and_digest(self):
        with self.assertRaises(ValueError):
            content.check(str(self.archive), str(self.expected), "f" * 64)
        self.archive.write_bytes(b"not an archive")
        with self.assertRaises(ValueError):
            self.check()

    def test_outside_and_symlink_refusal(self):
        for path in ("/etc/passwd", "../outside"):
            with self.assertRaises(ValueError):
                content.read_expectation(path)
        link = self.root / "link"
        link.symlink_to("expected.json")
        with self.assertRaises(ValueError):
            content.read_expectation(str(link))
        with self.assertRaises(ValueError):
            content.read_expectation(str(self.root))

    def test_cli_exit_codes_and_no_partial_receipt(self):
        args = ["check", str(self.archive), str(self.expected)]
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(content.main(args), 0)
            self.assertTrue(json.loads(stdout.getvalue())["content_passed"])
        self.archive.write_bytes(writer.build({"different": b"x"}))
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(content.main(args), 2)
            self.assertFalse(json.loads(stdout.getvalue())["content_passed"])
        self.expected.write_text("invalid")
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(content.main(args), 1)
            self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
