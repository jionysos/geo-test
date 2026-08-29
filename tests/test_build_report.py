import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_report.py"
SPEC = importlib.util.spec_from_file_location("build_report", MODULE_PATH)
build_report = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_report)


def judgment(mentioned=False, recommended=False, rank=None, rank_basis=None):
    return {
        "mentioned": mentioned,
        "recommended": recommended,
        "rank": rank,
        "rank_basis": rank_basis,
        "matched_names": ["매칭 이름"] if mentioned else [],
        "evidence": "판정 근거" if mentioned or recommended else "",
    }


def sample_data():
    questions = []
    for number in range(1, 6):
        questions.append(
            {
                "id": f"Q{number}",
                "type": "solution" if number == 1 else "recommendation",
                "question": f"질문 {number}",
                "response": f"답변 {number}",
                "target": judgment(),
                "brands": [],
                "sources": [],
            }
        )
    return {
        "schema_version": 1,
        "status": "complete",
        "measured_at": "2026-08-29",
        "target": {"name": "자사", "aliases": ["자사 제품"], "domain": "example.com"},
        "competitors": [],
        "technical": {
            "access_state": "접근 가능",
            "score": 80,
            "raw_score": 80,
            "cap_reason": "",
            "audited_urls": ["https://example.com/"],
            "sections": [],
            "trust_summary": "일부 보완",
        },
        "questions": questions,
        "hypotheses": [],
        "priorities": [],
        "limitations": [],
    }


class MetricTests(unittest.TestCase):
    def test_self_only_recommendations_produce_100_percent_sov(self):
        data = sample_data()
        data["questions"][1]["target"] = judgment(True, True, 1, "explicit")
        data["questions"][2]["target"] = judgment(True, True, 2, "ordered-list")
        build_report.validate_data(data)
        metrics = build_report.calculate_metrics(data)
        self.assertEqual(metrics["total_recommendations"], 2)
        self.assertEqual(metrics["target"]["sov"], "100%")
        self.assertEqual(build_report._rank_label(metrics["target"]), "1.5위 (2/2건 순위 확인)")

    def test_specified_absent_and_discovered_competitor_share_one_universe(self):
        data = sample_data()
        data["competitors"] = [{"name": "지정사", "aliases": [], "specified": True}]
        data["questions"][1]["target"] = judgment(True, True)
        data["questions"][1]["brands"] = [
            {"name": "발견사", "specified": False, **judgment(True, True)}
        ]
        data["questions"][2]["brands"] = [
            {"name": "발견사", "specified": False, **judgment(True, True)}
        ]
        build_report.validate_data(data)
        metrics = build_report.calculate_metrics(data)
        by_name = {item["name"]: item for item in metrics["brands"]}
        self.assertEqual(metrics["total_recommendations"], 3)
        self.assertEqual(by_name["자사"]["sov"], "33%")
        self.assertEqual(by_name["지정사"]["recommendations"], 0)
        self.assertEqual(by_name["발견사"]["recommendations"], 2)

    def test_q1_recommendation_is_visible_but_excluded_from_metrics(self):
        data = sample_data()
        data["questions"][0]["target"] = judgment(True, True, 1, "explicit")
        build_report.validate_data(data)
        metrics = build_report.calculate_metrics(data)
        self.assertEqual(metrics["target"]["mentions"], 1)
        self.assertEqual(metrics["target"]["recommendations"], 0)
        self.assertEqual(metrics["total_recommendations"], 0)
        self.assertEqual(build_report._sov_label(metrics["target"], 0), "N/A")

    def test_plain_appearance_order_is_not_an_allowed_rank_basis(self):
        data = sample_data()
        data["questions"][1]["target"] = judgment(True, True, 1, "appearance-order")
        with self.assertRaises(build_report.ReportDataError):
            build_report.validate_data(data)

    def test_recommendation_must_also_be_a_mention(self):
        data = sample_data()
        data["questions"][1]["target"] = {
            **judgment(False, True),
            "evidence": "추천 문장",
        }
        with self.assertRaises(build_report.ReportDataError):
            build_report.validate_data(data)


class RenderingTests(unittest.TestCase):
    def test_external_text_is_html_escaped(self):
        data = sample_data()
        payload = '<script>alert("x")</script></details>'
        data["questions"][0]["response"] = payload
        build_report.validate_data(data)
        rendered = build_report.render_html(data, build_report.calculate_metrics(data))
        self.assertNotIn(payload, rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;/details&gt;", rendered)

    def test_gauge_uses_score_band_boundaries(self):
        gauge = build_report._gauge_svg(80)
        self.assertIn("M20 100 A80 80 0 0 1 100 20", gauge)
        self.assertIn("M100 20 A80 80 0 0 1 147.02 35.28", gauge)
        self.assertIn("M147.02 35.28 A80 80 0 0 1 176.08 75.28", gauge)
        self.assertIn("M176.08 75.28 A80 80 0 0 1 180 100", gauge)
        self.assertIn('rotate(54.0 100 100)', gauge)

    def test_build_writes_run_files_and_optional_download_copy(self):
        data = sample_data()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "report-data.json"
            input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            run_dir = root / "run"
            download = root / "Downloads" / "sample.html"
            markdown_path, html_path = build_report.build(input_path, run_dir, download)
            self.assertTrue(markdown_path.exists())
            self.assertTrue(html_path.exists())
            self.assertTrue(download.exists())
            self.assertIn("<!-- geo-test-run: complete -->", markdown_path.read_text(encoding="utf-8"))

    def test_insufficient_technical_coverage_renders_without_a_score(self):
        data = sample_data()
        data["technical"]["score"] = None
        data["technical"]["access_state"] = "확인 불가"
        build_report.validate_data(data)
        metrics = build_report.calculate_metrics(data)
        rendered = build_report.render_html(data, metrics)
        self.assertIn("확인 범위 부족", rendered)
        self.assertNotIn("None/100", rendered)

    def test_generated_html_has_balanced_major_containers(self):
        data = sample_data()
        build_report.validate_data(data)
        rendered = build_report.render_html(data, build_report.calculate_metrics(data))
        for tag in ("div", "section", "table", "details"):
            self.assertEqual(rendered.count(f"<{tag}"), rendered.count(f"</{tag}>"), tag)


if __name__ == "__main__":
    unittest.main()
