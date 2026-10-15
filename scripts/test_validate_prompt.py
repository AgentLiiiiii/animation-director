"""Regression tests for structural errors, not animation quality."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_prompt import validate

SCRIPT = Path(__file__).with_name("validate_prompt.py")
BASE = """画面内容
猫看见鸟。
时间线（4秒）
[00:00–00:01.25]
猫抬头。
[00:01.25–00:04]
镜头推近，猫停住。
全局约束
无背景音乐。
"""


class PromptChecks(unittest.TestCase):
    def test_valid_variants(self):
        variants = [BASE, BASE.replace("–", "-"), BASE.replace("–", "—"),
                    BASE.replace("时间线（4秒）", "时间线"),
                    BASE.replace("时间线（4秒）", "## 时间线（4秒）"),
                    BASE.replace("画面内容", "**画面内容**"),
                    BASE.replace("[00:00–00:01.25]\n", "[00:00–00:01.25] "),
                    "\ufeff" + BASE.replace("\n", "\r\n"),
                    "```plaintext\n" + BASE + "```",
                    BASE.replace("4秒", "30秒").replace("00:04]", "00:30]")]
        for text in variants:
            with self.subTest(text=text):
                report = validate(text)
                self.assertTrue(report["ok"], report)
                self.assertEqual(report["scope"], "structure_and_timing_only")

    def test_detects_structural_faults(self):
        cases = [
            (BASE.replace("[00:01.25", "[00:01.5"), "gap"),
            (BASE.replace("[00:01.25", "[00:01"), "overlap"),
            (BASE.replace("[00:01.25", "[00:00"), "overlap"),
            (BASE.replace("[00:00", "[00:00.1"), "gap"),
            (BASE.replace("[00:01.25–00:04]", "[00:01.25–00:01.25]"), "nonpositive_span"),
            (BASE.replace("4秒", "5秒"), "declared_duration"),
            (BASE.replace("00:04]", "00:31]"), "duration_range"),
            (BASE.replace("00:04]", "00:03]"), "duration_range"),
            (BASE.replace("00:04]", "00:60]"), "timecode"),
            (BASE.replace("[00:01.25–00:04]", "[bad–00:04]"), "declared_duration"),
            (BASE.replace("[00:00–00:01.25]", "[0–1.25]"), "timecode"),
            (BASE.replace("[00:00", "全段保持正面。\n[00:00"), "timeline_preamble"),
            ("说明\n" + BASE, "preamble"),
            (BASE + "声音设计\n风声。", "sound_section"),
            (BASE.replace("全局约束", "声音设计"), "sections"),
            (BASE + "全局约束\n无旁白。", "sections"),
            (BASE.replace("猫抬头。\n", ""), "empty_segment"),
            (BASE.replace("无背景音乐。", ""), "empty_section"),
            (BASE + "## 其他说明\n文字。", "extra_heading"),
            (BASE + "[00:04–00:05]\n文字。", "misplaced_timecode"),
            ("```text\n" + BASE + "```\n说明", "code_block"),
            ("```\n" + BASE + "```\n```\n内容\n```", "code_block"),
        ]
        for text, code in cases:
            with self.subTest(code=code, text=text):
                report = validate(text)
                self.assertFalse(report["ok"])
                self.assertIn(code, [e["code"] for e in report["errors"]])

    def test_requested_duration_and_wrapper(self):
        self.assertTrue(validate(BASE, "4.0")["ok"])
        self.assertFalse(validate(BASE, "5")["ok"])
        for value in ("NaN", "Infinity", "oops", "0", "31"):
            self.assertFalse(validate(BASE, value)["ok"])
        self.assertFalse(validate(BASE, require_code_block=True)["ok"])
        self.assertTrue(validate("```\n" + BASE + "```", require_code_block=True)["ok"])

    def test_bundled_examples(self):
        reference = SCRIPT.parent.parent / "references" / "prompt-delivery.md"
        examples = re.findall(r"```text\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S)
        self.assertGreaterEqual(len(examples), 2)
        for example in examples:
            report = validate(example)
            self.assertTrue(report["ok"], report)

    def test_cli_input_and_exit_codes(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "-", "--duration", "4"],
                             input=BASE.encode("utf-8"), capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout.decode("utf-8"))["ok"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "提示词.txt"
            path.write_text(BASE, encoding="utf-8-sig")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--duration", "5"], capture_output=True)
            self.assertEqual(run.returncode, 1)
            run = subprocess.run([sys.executable, str(SCRIPT), str(path.with_name("missing.txt"))], capture_output=True)
            self.assertEqual(run.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
