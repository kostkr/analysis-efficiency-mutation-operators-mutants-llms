import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import calculate_metrics as cm
from defect4j.generators import LLMConfig
from defect4j.generators.base import GeneratorJob
from defect4j.generators.llm.generator import LLMGenerator


class CalculateMetricsTest(unittest.TestCase):
    def write_bug_workspace(
        self,
        workspace: Path,
        bug_name: str,
        mutants_by_file: dict[str, list[dict]],
        results_by_file: dict[str, list[dict]],
        *,
        bug_profile: list[str] | None = None,
    ) -> None:
        bug_dir = workspace / bug_name
        (bug_dir / "mutants").mkdir(parents=True)
        (bug_dir / "results").mkdir()
        total_mutants = sum(len(items) for items in mutants_by_file.values())
        bug_id = int(bug_name.rsplit("_", 1)[-1])
        (bug_dir / "meta.json").write_text(
            json.dumps(
                {
                    "project": "BUG",
                    "bug_id": bug_id,
                    "bug_profile": {"failing_tests": ["T1"] if bug_profile is None else bug_profile},
                    "suite_profile": {"total_tests": 2},
                    "totals": {"input_mutants": total_mutants},
                }
            ),
            encoding="utf-8",
        )
        for file_name, mutants in mutants_by_file.items():
            (bug_dir / "mutants" / file_name).write_text(json.dumps(mutants), encoding="utf-8")
        for file_name, results in results_by_file.items():
            (bug_dir / "results" / file_name).write_text(json.dumps(results), encoding="utf-8")

    def make_bug_workspace(
        self,
        mutants_by_file: dict[str, list[dict]],
        results_by_file: dict[str, list[dict]],
        *,
        bug_profile: list[str] | None = None,
        bug_name: str = "BUG_1",
    ) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        workspace = Path(tmp.name)
        self.write_bug_workspace(
            workspace,
            bug_name,
            mutants_by_file,
            results_by_file,
            bug_profile=bug_profile,
        )
        return tmp, workspace

    def mutant(self, mutant_id: int, aftercode: str, line: int = 1) -> dict:
        return {
            "id": mutant_id,
            "filepath": "Example.java",
            "line": line,
            "precode": "return 1;",
            "aftercode": aftercode,
            "gen_time_s": 1.0,
        }

    def result(
        self,
        mutant_id: int,
        *,
        compiled: bool = True,
        timed_out: bool = False,
        failing_tests: list[str] | None = None,
        compile_error: str = "",
        run_time_s: float = 0.0,
    ) -> dict:
        return {
            "mutant_id": mutant_id,
            "compiled": compiled,
            "compile_error": compile_error,
            "run_time_s": run_time_s,
            "timed_out": timed_out,
            "test_executed": compiled and not timed_out and not compile_error,
            "profile_scope": "relevant_full",
            "test_command": "defects4j test -r",
            "failing_tests": [] if failing_tests is None else failing_tests,
        }

    def test_time_metrics_include_generation_and_execution_time(self) -> None:
        first = self.mutant(1, "return 2;")
        first["gen_time_s"] = 1.5
        second = self.mutant(2, "return 3;")
        second["gen_time_s"] = 2.5
        tmp, workspace = self.make_bug_workspace(
            {"gemma4_model.json": [first, second]},
            {"gemma4_model.json": [self.result(1, run_time_s=10.0), self.result(2, run_time_s=20.0)]},
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertAlmostEqual(metrics.generation_time_s, 4.0)
        self.assertAlmostEqual(metrics.execution_time_s, 30.0)
        self.assertAlmostEqual(metrics.total_time_s, 34.0)
        self.assertAlmostEqual(metrics.amgt or 0.0, 17.0)
        self.assertAlmostEqual(metrics.cpum or 0.0, 17.0)

    def test_timeout_counts_for_cmr_but_not_for_final_metrics(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {"gemma4_model.json": [self.mutant(1, "return 2;")]},
            {"gemma4_model.json": [self.result(1, compiled=True, timed_out=True)]},
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.generated, 1)
        self.assertEqual(metrics.timed_out, 1)
        self.assertEqual(metrics.compiled, 1)
        self.assertEqual(metrics.useful, 0)
        self.assertEqual(metrics.invalid, 1)
        self.assertEqual(metrics.cmr, 1.0)

    def test_empty_mutant_json_is_missing_data_warning(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {"gemma4_model.json": []},
            {"gemma4_model.json": []},
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            warnings = cm.readiness_warnings(bug, "gemma4", [])

        self.assertTrue(any("missing mutant data" in warning for warning in warnings))

    def test_cmr_uses_all_generated_mutants_as_denominator(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {"gemma4_model.json": [self.mutant(1, "return 2;"), self.mutant(2, "return 3;"), self.mutant(3, "return 4;")]},
            {"gemma4_model.json": [self.result(1, compiled=True), self.result(2, compiled=False, compile_error="javac")]}
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.result_records, 2)
        self.assertEqual(metrics.compiled, 1)
        self.assertAlmostEqual(metrics.cmr or 0.0, 1 / 3)

    def test_emr_excludes_duplicates_and_timeouts_from_denominator(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "gemma4_model.json": [
                    self.mutant(1, "return 2;"),
                    self.mutant(2, "return 2; // duplicate"),
                    self.mutant(3, "return 3;"),
                    self.mutant(4, "return 4;"),
                ]
            },
            {
                "gemma4_model.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=[]),
                    self.result(3, compiled=True, timed_out=True),
                    self.result(4, failing_tests=["T1"]),
                ]
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.duplicates, 1)
        self.assertEqual(metrics.compiled, 4)
        self.assertEqual(metrics.timed_out, 1)
        self.assertEqual(metrics.survived_useful, 1)
        self.assertAlmostEqual(metrics.emr or 0.0, 1 / 2)

    def test_final_metrics_exclude_timeout_duplicates_and_not_compiled(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [
                    self.mutant(1, "return 10;", line=1),
                    self.mutant(2, "return 20;", line=2),
                ],
                "gemma4_model.json": [
                    self.mutant(1, "return 10;", line=1),  # valid classic match
                    self.mutant(2, "return 10; // duplicate", line=1),  # duplicate
                    self.mutant(3, "return 30;", line=3),  # compile error
                    self.mutant(4, "return 40;", line=4),  # timeout
                    self.mutant(5, "return 50;", line=5),  # final new survived
                    self.mutant(6, "return 20;", line=2),  # final classic match
                ],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=["T1"]),
                    self.result(2, failing_tests=["T2"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T1"]),
                    self.result(3, compiled=False, compile_error="javac"),
                    self.result(4, compiled=True, timed_out=True),
                    self.result(5, failing_tests=[]),
                    self.result(6, failing_tests=["T2"]),
                ],
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.generated, 6)
        self.assertEqual(metrics.duplicates, 1)
        self.assertEqual(metrics.compiled, 5)
        self.assertEqual(metrics.compiled_duplicates, 1)
        self.assertEqual(metrics.compile_failed, 1)
        self.assertEqual(metrics.timed_out, 1)
        self.assertEqual(metrics.useful, 3)
        self.assertEqual(metrics.profile_ready, 3)
        self.assertEqual(metrics.invalid, 3)
        self.assertAlmostEqual(metrics.cmr or 0.0, 5 / 6)
        self.assertAlmostEqual(metrics.dmr or 0.0, 1 / 5)
        self.assertAlmostEqual(metrics.mutation_score or 0.0, 2 / 3)
        self.assertAlmostEqual(metrics.llm_nmr or 0.0, 1 / 3)
        self.assertAlmostEqual(metrics.rbdr or 0.0, 1.0)
        self.assertAlmostEqual(metrics.aor or 0.0, 1 / 3)
        self.assertAlmostEqual(metrics.cr or 0.0, 1 / 3)

    def test_aor_uses_ochiai_formula_for_each_valid_mutant(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "gemma4_model.json": [
                    self.mutant(1, "return 2;", line=1),
                    self.mutant(2, "return 3;", line=2),
                    self.mutant(3, "return 4;", line=3),
                    self.mutant(4, "return 5;", line=4),
                ]
            },
            {
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T1", "T2"]),
                    self.result(2, failing_tests=[]),
                    self.result(3, compiled=False, compile_error="javac"),
                    self.result(4, compiled=True, timed_out=True),
                ]
            },
            bug_profile=["T1", "T3"],
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.useful, 2)
        self.assertAlmostEqual(cm.ochiai({"T1", "T2"}, {"T1", "T3"}), 0.5)
        self.assertAlmostEqual(metrics.aor or 0.0, 0.25)

    def test_aor_averages_per_bug_across_all_defects_and_counts_empty_bug_as_zero(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        workspace = Path(tmp.name)
        self.write_bug_workspace(
            workspace,
            "BUG_1",
            {"gemma4_model.json": [self.mutant(1, "return 2;")]},
            {"gemma4_model.json": [self.result(1, failing_tests=["T1"])]},
            bug_profile=["T1"],
        )
        self.write_bug_workspace(
            workspace,
            "BUG_2",
            {"gemma4_model.json": [self.mutant(1, "return 2;")]},
            {"gemma4_model.json": [self.result(1, compiled=False, compile_error="javac")]},
            bug_profile=["T2"],
        )
        with tmp:
            bugs = cm.load_bugs(workspace, ())
            metrics = cm.calculate_metrics("ALL", "gemma4", bugs)

        self.assertEqual(metrics.detected_bugs, 1)
        self.assertAlmostEqual(metrics.rbdr or 0.0, 0.5)
        self.assertAlmostEqual(metrics.aor or 0.0, 0.5)

    def test_high_ochiai_mutant_rate_counts_mutants_above_threshold(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [
                    self.mutant(1, "return 2;", line=1),
                    self.mutant(2, "return 3;", line=2),
                ],
                "gemma4_model.json": [
                    self.mutant(1, "return 4;", line=1),
                    self.mutant(2, "return 5;", line=2),
                ],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=["T1"]),
                    self.result(2, failing_tests=["T2"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T1", "T2"]),
                    self.result(2, failing_tests=[]),
                ],
            },
            bug_profile=["T1", "T2"],
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.profile_ready, 2)
        self.assertEqual(metrics.high_ochiai_mutants, 1)
        self.assertAlmostEqual(metrics.high_ochiai_mutant_rate or 0.0, 0.5)

    def test_llm_nmr_uses_same_line_exact_test_set_matching_including_empty_profile(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [
                    self.mutant(1, "return 2;", line=1),
                    self.mutant(2, "return 3;", line=2),
                ],
                "gemma4_model.json": [
                    self.mutant(1, "return 4;", line=1),
                    self.mutant(2, "return 5;", line=2),
                    self.mutant(3, "return 3;", line=2),
                ],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=["T1"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=["T1"]),
                    self.result(3, failing_tests=["T2"]),
                ],
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.useful, 3)
        self.assertEqual(metrics.new_mutants, 0)
        self.assertAlmostEqual(metrics.llm_nmr or 0.0, 0.0)

    def test_llm_nmr_profile_match_requires_same_line(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [
                    self.mutant(1, "return 2;", line=1),
                ],
                "gemma4_model.json": [
                    self.mutant(1, "return 4;", line=2),
                ],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=["T1"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T1"]),
                ],
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.useful, 1)
        self.assertEqual(metrics.new_mutants, 1)
        self.assertAlmostEqual(metrics.llm_nmr or 0.0, 1.0)

    def test_llm_nmr_syntactic_signature_uses_normalized_precode_and_aftercode(self) -> None:
        classic = self.mutant(1, "return\t2; // classic", line=7)
        classic["precode"] = "return\t1; // original"
        llm_same = self.mutant(1, "return 2;", line=7)
        llm_same["precode"] = "return 1;"
        llm_new = self.mutant(2, "return 2;", line=7)
        llm_new["precode"] = "return 9;"
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [classic],
                "gemma4_model.json": [llm_same],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=["T1"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T2"]),
                ],
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(
            cm.llm_nmr_syntactic_signature(classic),
            cm.llm_nmr_syntactic_signature(llm_same),
        )
        self.assertNotEqual(
            cm.llm_nmr_syntactic_signature(classic),
            cm.llm_nmr_syntactic_signature(llm_new),
        )
        self.assertEqual(metrics.useful, 1)
        self.assertEqual(metrics.new_mutants, 0)
        self.assertAlmostEqual(metrics.llm_nmr or 0.0, 0.0)

    def test_aggregate_llm_nmr_skips_bugs_without_classic_mutants(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        workspace = Path(tmp.name)
        self.write_bug_workspace(
            workspace,
            "BUG_1",
            {
                "classic.json": [
                    self.mutant(1, "return 2;", line=1),
                    self.mutant(2, "return 3;", line=2),
                ],
                "gemma4_model.json": [
                    self.mutant(1, "return 2;", line=1),
                    self.mutant(2, "return 9;", line=2),
                ],
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=["T1"]),
                    self.result(2, failing_tests=["T2"]),
                ],
                "gemma4_model.json": [
                    self.result(1, failing_tests=["T1"]),
                    self.result(2, failing_tests=["T9"]),
                ],
            },
        )
        self.write_bug_workspace(
            workspace,
            "BUG_2",
            {"gemma4_model.json": [self.mutant(1, "return 4;", line=1)]},
            {"gemma4_model.json": [self.result(1, failing_tests=["T3"])]},
            bug_profile=["T3"],
        )
        with tmp:
            bugs = cm.load_bugs(workspace, ())
            metrics = cm.calculate_metrics("ALL_SELECTED", "gemma4", bugs)

        self.assertEqual(metrics.new_mutants, 1)
        self.assertAlmostEqual(metrics.llm_nmr or 0.0, 0.5)

    def test_llm_validation_keeps_all_records_and_marks_duplicates(self) -> None:
        job = GeneratorJob(
            project="BUG",
            bug_id=1,
            container_path="/tmp/BUG_1_f",
            host_path="",
            filepath="Example.java",
            class_fqn="Example",
            method_name="example",
            method_source="public int example() {\n    return 1;\n}",
            method_start=10,
            method_end=12,
            changed_lines=[11],
        )
        raw = [
            {"line": 999, "precode": "return 1;", "aftercode": "return 1;", "rule": "No-op"},
            {"line": 11, "precode": "return 1;", "aftercode": "return 2;", "rule": "Replace constant"},
            {"line": 11, "precode": "return 1;", "aftercode": "return 2;", "rule": "Repeated mutant"},
            {"line": 999, "precode": "return missing;", "aftercode": "return 3;", "rule": "Unmatched invalid"},
        ]

        mutants = LLMGenerator(LLMConfig())._validated_mutants(job, raw)

        self.assertEqual(len(mutants), 4)
        self.assertEqual([mutant.line for mutant in mutants], [999, 11, 11, 999])
        self.assertEqual([mutant.dublicate for mutant in mutants], [True, False, True, False])

    def test_dmr_uses_compiled_denominator_and_ignores_trailing_comments(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "gemma4_model.json": [
                    self.mutant(1, "return 1;"),
                    self.mutant(2, "return 2;"),
                    self.mutant(3, "return 2; // duplicate with comment"),
                ]
            },
            {
                "gemma4_model.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=["T1"]),
                    self.result(3, failing_tests=["T1"]),
                ]
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertTrue(cm.same_mutation_code("return 2;", "return 2; // duplicate with comment"))
        self.assertEqual(metrics.generated, 3)
        self.assertEqual(metrics.duplicates, 2)
        self.assertEqual(metrics.non_duplicate, 1)
        self.assertEqual(metrics.compiled_duplicates, 2)
        self.assertAlmostEqual(metrics.dmr or 0.0, 2 / 3)

    def test_classic_final_metrics_ignore_invalid_and_duplicates(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [
                    self.mutant(1, "return 1;"),
                    self.mutant(2, "return 2;"),
                    self.mutant(3, "return 3;"),
                ]
            },
            {
                "classic.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=["T1"]),
                    self.result(3, compiled=True, timed_out=True),
                ]
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "classic", (bug,))

        self.assertEqual(metrics.generated, 3)
        self.assertEqual(metrics.duplicates, 1)
        self.assertEqual(metrics.invalid, 2)
        self.assertEqual(metrics.cmr, 1.0)

    def test_metrics_row_shows_generated_count_as_a_separate_column(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "gemma4_model.json": [
                    self.mutant(1, "return 1;"),
                    self.mutant(2, "return 2;"),
                    self.mutant(3, "return 3;"),
                ]
            },
            {
                "gemma4_model.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=["T1"]),
                    self.result(3, compiled=False, compile_error="javac"),
                ]
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        row = cm.metrics_row(metrics)
        self.assertEqual(row[0], "gemma4")
        self.assertEqual(row[1], "3")
        self.assertIn("Mutants", cm.CHAPTER_5_METRICS)

    def test_generated_count_includes_duplicates_and_missing_results(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "gemma4_model.json": [
                    self.mutant(1, "return 2;"),
                    self.mutant(2, "return 2; // duplicate"),
                    self.mutant(3, "return 3;"),
                ]
            },
            {
                "gemma4_model.json": [
                    self.result(1, failing_tests=[]),
                    self.result(2, failing_tests=[]),
                ]
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]
            metrics = cm.calculate_metrics("BUG_1", "gemma4", (bug,))

        self.assertEqual(metrics.generated, 3)
        self.assertEqual(metrics.duplicates, 1)
        self.assertEqual(metrics.missing_results, 1)

    def test_bug_total_uses_meta_input_mutants(self) -> None:
        tmp, workspace = self.make_bug_workspace(
            {
                "classic.json": [self.mutant(1, "return 2;")],
                "gemma4_model.json": [self.mutant(1, "return 3;"), self.mutant(2, "return 4;")],
            },
            {
                "classic.json": [self.result(1)],
                "gemma4_model.json": [self.result(1), self.result(2)],
            },
        )
        with tmp:
            bug = cm.load_bugs(workspace, ())[0]

        self.assertEqual(bug.input_mutant_count, 3)


if __name__ == "__main__":
    unittest.main()
