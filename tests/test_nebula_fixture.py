"""3Q 발표 픽스처 경로 — demo --input과 FakeClient의 미분류 재현."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nebula.demo import FakeClient, source
from nebula.pipeline import run


class DemoInput(unittest.TestCase):
    def test_demo_input_replaces_builtin_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = source()[:3]
            inputs[0]["name"] = "입력 파일 인물"
            (root / "in.json").write_text(json.dumps(inputs, ensure_ascii=False))
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nebula",
                    "demo",
                    "--input",
                    str(root / "in.json"),
                    "--out",
                    str(root / "run"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("persons=3 ", proc.stdout)
            written = json.loads((root / "run" / "synthetic-persons.json").read_text())
            self.assertEqual(written[0]["name"], "입력 파일 인물")

    def test_fake_client_leaves_other_tasks_unclassified(self):
        other = "기타 개인 관심 과제를 추진하고 싶다."
        known = "병렬 테스트 개선 과제를 추진하고 싶다."
        person = {"id": "1", "pjt": "테스트 개발", "text": other + "\n\n" + known}
        with tempfile.TemporaryDirectory() as out:
            data = run([person], out, FakeClient())
        task_of = {t["quote"]: t["id"] for t in data["tasks"]}
        category_of = {a["task_id"]: a["category_id"] for a in data["assignments"]}
        self.assertIsNone(category_of[task_of[other]])
        self.assertIsNotNone(category_of[task_of[known]])


if __name__ == "__main__":
    unittest.main()
