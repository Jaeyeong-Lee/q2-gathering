"""Public pipeline/build contract tests with synthetic sources only."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from nebula.demo import FakeClient, source
from nebula.model import ValidationError, digest
from nebula.pipeline import run, with_review
from nebula.render import build_view


class PipelineContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
        self.inputs = source()[:3]

    def tearDown(self):
        self.temp.cleanup()

    def test_input_to_matrix_keeps_sources_counts_and_unlinked_work(self):
        data = run(self.inputs, self.out, FakeClient())
        self.assertEqual(len(data["persons"]), 3)
        self.assertEqual(len(data["tasks"]), 5)
        view = build_view(data)
        for task in view["tasks"]:
            person = next(p for p in self.inputs if p["id"] == task["person_id"])
            self.assertIn(task["quote"], person["text"])
            for skill in task["skills"]:
                self.assertIn(task["quote"], skill["relation_quote"])
                self.assertIn(skill["quote"], skill["relation_quote"])
        self.assertTrue(any(t["horizon"] == "mid" for t in view["tasks"]))
        self.assertEqual(len(build_view(data, approved_only=True)["tasks"]), 0)

    def test_identical_run_uses_validated_cache(self):
        first = run(self.inputs, self.out, FakeClient())

        class NeverCall(FakeClient):
            def complete(self, *args):
                raise AssertionError("unexpected LLM call")

        second = run(self.inputs, self.out, NeverCall())
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(json.loads((self.out / "status.json").read_text())["calls"], 0)

    def test_corrected_extraction_revalidates_evidence_and_invalidates_review(self):
        original = run(self.inputs, self.out, FakeClient())
        correction = copy.deepcopy(original["corrections_template"])
        correction["persons"] = correction["persons"][:1]
        correction.pop("taxonomies", None)
        correction["persons"][0]["extraction"]["tasks"][0][
            "label"
        ] = "검토자가 정리한 업무"
        changed = run(self.inputs, self.out, FakeClient(), corrections=correction)
        self.assertNotEqual(original["run_id"], changed["run_id"])
        self.assertEqual(original["tasks"][0]["id"], changed["tasks"][0]["id"])
        with self.assertRaises(ValidationError):
            with_review(changed, {"run_id": original["run_id"], "decisions": {}})
        correction["persons"][0]["extraction"]["tasks"][0]["quote"] = "원문에 없는 문장"
        with self.assertRaises(ValidationError):
            run(self.inputs, self.out, FakeClient(), corrections=correction)


class RecoveryAndReviewContract(unittest.TestCase):
    def test_failed_call_is_not_cached_but_finished_people_resume(self):
        class Failing(FakeClient):
            def complete(self, stage, system, payload):
                if stage == "extract" and payload["person_id"] == "2":
                    return {
                        "tasks": [{"quote": "INVALID"}],
                        "capabilities": [],
                        "links": [],
                    }
                return super().complete(stage, system, payload)

        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValidationError):
                run(source()[:3], out, Failing())
            status = json.loads((Path(out) / "status.json").read_text())
            self.assertEqual(status["state"], "failed")
            self.assertEqual(
                len(list((Path(out) / "cache" / "extract").glob("*.json"))), 1
            )
            result = run(source()[:3], out, FakeClient())
            self.assertEqual(len(result["tasks"]), 5)
            self.assertGreaterEqual(
                json.loads((Path(out) / "status.json").read_text())["cache_hits"], 1
            )

    def test_review_filters_rejects_and_category_change_requires_local_evidence(self):
        with tempfile.TemporaryDirectory() as out:
            data = run(source()[:3], out, FakeClient())
            task = data["tasks"][0]
            review = {
                "run_id": data["run_id"],
                "decisions": {
                    task["id"]: {
                        "status": "approved",
                        "note": "분류 근거 재검토",
                        "category_id": None,
                    }
                },
            }
            reviewed = with_review(data, review)
            view = build_view(reviewed, True)
            self.assertEqual(len(view["tasks"]), 1)
            self.assertIsNone(view["tasks"][0]["category_id"])
            review["decisions"][task["id"]]["category_id"] = "unknown-id"
            with self.assertRaises(ValidationError):
                with_review(data, review)
            edited = copy.deepcopy(data)
            edited["tasks"][0]["quote"] = "altered"
            with self.assertRaises(ValidationError):
                with_review(edited, {"run_id": data["run_id"], "decisions": {}})

    def test_empty_signal_retains_person_and_unlinked_capability(self):
        inputs = [
            {
                "id": "silent",
                "pjt": "PJT",
                "text": "앞으로도 열심히 하겠습니다.\n\n별도로 문서 작성 경험을 갖고 있다.",
            }
        ]
        with tempfile.TemporaryDirectory() as out:
            result = run(inputs, out, FakeClient())
            view = build_view(result)
            self.assertEqual(view["tasks"], [])
            self.assertEqual(view["bubbles"], [])
            self.assertEqual(view["no_task_person_ids"], ["silent"])
            self.assertEqual(len(view["unlinked_capabilities"]), 1)

    def test_taxonomy_can_be_corrected_without_reextracting_people(self):
        with tempfile.TemporaryDirectory() as out:
            result = run(source()[:2], out, FakeClient())
            correction = copy.deepcopy(result["corrections_template"])
            correction["persons"] = []
            correction["taxonomies"][0]["categories"][0]["definition"] += " 검토 완료"

            class NoExtraction(FakeClient):
                def complete(self, stage, *args):
                    if stage == "extract":
                        raise AssertionError("must reuse extraction")
                    return super().complete(stage, *args)

            updated = run(source()[:2], out, NoExtraction(), corrections=correction)
            self.assertNotEqual(result["run_id"], updated["run_id"])
            correction["taxonomies"][0]["input_hash"] = "stale"
            with self.assertRaises(ValidationError):
                run(source()[:2], out, FakeClient(), corrections=correction)

    def test_same_person_many_mentions_count_once_in_a_bubble(self):
        inputs = [
            {
                "id": "one",
                "pjt": "PJT",
                "text": "단기 개선 A를 추진한다. 단기 개선 B를 추진한다. 이를 위해 분석 경험을 활용한다.",
            }
        ]

        class Fixture(FakeClient):
            def complete(self, stage, system, payload):
                if stage == "extract":
                    tasks = [
                        {
                            "ref": ref,
                            "label": "공통 개선",
                            "quote": q,
                            "occurrence": 1,
                            "horizon": "short",
                            "time_quote": q,
                        }
                        for ref, q in [
                            ("t1", "단기 개선 A를 추진한다."),
                            ("t2", "단기 개선 B를 추진한다."),
                        ]
                    ]
                    return {
                        "tasks": tasks,
                        "capabilities": [
                            {
                                "ref": "c1",
                                "label": "분석",
                                "kind": "have",
                                "quote": "이를 위해 분석 경험을 활용한다.",
                                "occurrence": 1,
                            }
                        ],
                        "links": [
                            {
                                "task_ref": ref,
                                "capability_ref": "c1",
                                "relation_quote": inputs[0]["text"],
                            }
                            for ref in ("t1", "t2")
                        ],
                    }
                return super().complete(stage, system, payload)

        with tempfile.TemporaryDirectory() as out:
            view = build_view(run(inputs, out, Fixture()))
            self.assertEqual(len(view["bubbles"]), 1)
            self.assertEqual(view["bubbles"][0]["people"], 1)
            self.assertEqual(len(view["bubbles"][0]["task_ids"]), 2)


class ReviewRegressions(unittest.TestCase):
    def test_invalid_rerun_marks_failure_and_retires_old_current_html(self):
        with tempfile.TemporaryDirectory() as out:
            run(source()[:2], out, FakeClient())
            root = Path(out)
            (root / "matrix.html").write_text("prior result")
            with self.assertRaises(ValidationError):
                run(source()[:2], out, FakeClient(), network={"unknown": []})
            self.assertEqual(
                json.loads((root / "status.json").read_text())["state"], "failed"
            )
            self.assertFalse((root / "matrix.html").exists())
            self.assertEqual(
                (root / "matrix.previous.html").read_text(), "prior result"
            )

    def test_run_publishes_full_correction_template_before_unlocking(self):
        with tempfile.TemporaryDirectory() as out:
            result = run(source()[:2], out, FakeClient())
            persisted = json.loads(
                (Path(out) / "corrections-template.json").read_text()
            )
            self.assertEqual(persisted, result["corrections_template"])

    def test_reviewed_snapshot_retains_immutable_assignment_baseline(self):
        with tempfile.TemporaryDirectory() as out:
            result = run(source()[:2], out, FakeClient())
            task = result["tasks"][0]
            revised = with_review(
                result,
                {
                    "run_id": result["run_id"],
                    "decisions": {
                        task["id"]: {
                            "status": "approved",
                            "category_id": None,
                            "note": "분류 정정",
                        }
                    },
                },
            )
            self.assertEqual(revised["original_assignments"], result["assignments"])

    def test_successive_partial_corrections_survive_resume_and_explicit_reset(self):
        with tempfile.TemporaryDirectory() as out:
            original = run(source()[:3], out, FakeClient())
            a, b = copy.deepcopy(original["corrections_template"]["persons"][:2])
            a["extraction"]["tasks"][0]["label"] += " 첫 정정"
            b["extraction"]["tasks"][0]["label"] += " 두 번째 정정"
            run(source()[:3], out, FakeClient(), corrections={"persons": [a]})
            run(source()[:3], out, FakeClient(), corrections={"persons": [b]})
            resumed = run(source()[:3], out, FakeClient())
            self.assertEqual(resumed["corrections_template"]["persons"][:2], [a, b])
            self.assertEqual(len(resumed["applied_corrections"]["persons"]), 2)
            reset = run(source()[:3], out, FakeClient(), reset_corrections=True)
            self.assertEqual(reset["tasks"], original["tasks"])
            self.assertEqual(reset["applied_corrections"]["persons"], [])

    def test_changed_source_discards_inherited_but_rejects_explicit_stale_patch(self):
        with tempfile.TemporaryDirectory() as out:
            inputs = source()[:2]
            initial = run(inputs, out, FakeClient())
            patch = copy.deepcopy(initial["corrections_template"]["persons"][0])
            patch["extraction"]["tasks"][0]["label"] += " 정정"
            run(inputs, out, FakeClient(), corrections={"persons": [patch]})
            inputs[0]["text"] += "\n추가 설명."
            fresh = run(inputs, out, FakeClient())
            self.assertEqual(fresh["applied_corrections"]["persons"], [])
            with self.assertRaises(ValidationError):
                run(inputs, out, FakeClient(), corrections={"persons": [patch]})

    def test_cli_parse_failure_marks_old_output_failed(self):
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as out:
            run(source()[:2], out, FakeClient())
            root = Path(out)
            (root / "matrix.html").write_text("old")
            (root / "bad.json").write_text("{broken")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nebula",
                    "run",
                    "--input",
                    str(root / "bad.json"),
                    "--out",
                    out,
                ],
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(
                json.loads((root / "status.json").read_text())["state"], "failed"
            )
            self.assertFalse((root / "matrix.html").exists())

    def test_output_lock_blocks_other_process_until_outer_context_exits(self):
        import subprocess
        import sys
        from nebula.storage import output_lock

        with tempfile.TemporaryDirectory() as out:
            command = [
                sys.executable,
                "-c",
                "import sys\nfrom nebula.storage import output_lock\nwith output_lock(sys.argv[1]): pass",
                out,
            ]
            with output_lock(out):
                with output_lock(out):
                    pass
                blocked = subprocess.run(command, capture_output=True)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertIn(b"output directory is in use", blocked.stderr)
            released = subprocess.run(command, capture_output=True)
            self.assertEqual(released.returncode, 0, released.stderr)

    def test_taxonomy_override_persists_then_invalidates_when_tasks_change(self):
        with tempfile.TemporaryDirectory() as out:
            inputs = source()[:2]
            initial = run(inputs, out, FakeClient())
            taxonomy_patch = copy.deepcopy(
                initial["corrections_template"]["taxonomies"][0]
            )
            taxonomy_patch["categories"][0]["definition"] += " 검토 완료"
            revised = run(
                inputs, out, FakeClient(), corrections={"taxonomies": [taxonomy_patch]}
            )
            resumed = run(inputs, out, FakeClient())
            self.assertEqual(resumed["run_id"], revised["run_id"])
            person_patch = copy.deepcopy(resumed["corrections_template"]["persons"][0])
            person_patch["extraction"]["tasks"][0]["label"] += " 범위 변경"
            changed = run(
                inputs, out, FakeClient(), corrections={"persons": [person_patch]}
            )
            self.assertEqual(changed["applied_corrections"]["taxonomies"], [])
