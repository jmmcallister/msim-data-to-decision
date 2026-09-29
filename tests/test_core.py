from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from analytics.core import (read_data, profile, quality_observations, descriptive_summary,
                            grouped_summary, interpretation_feedback, check_claim,
                            build_report, question_hints)


class DataTests(unittest.TestCase):
    def test_csv_preserves_labels_and_reports_missing(self):
        df = read_data(b"region,value\nNA,10\nEast,\nEast,20\n", "sample.csv")
        self.assertEqual(df.iloc[0, 0], "NA")
        self.assertEqual(profile(df).set_index("Column").loc["value", "Missing"], 1)

    def test_csv_encoding_separator(self):
        df = read_data("region;value\nCafé;10\n".encode("cp1252"), "sample.csv", encoding="cp1252", separator=";")
        self.assertEqual(df.iloc[0, 0], "Café")

    def test_excel_sheet_selection(self):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"x": [1]}).to_excel(writer, sheet_name="First", index=False)
            pd.DataFrame({"x": [99]}).to_excel(writer, sheet_name="Second", index=False)
        self.assertEqual(read_data(buf.getvalue(), "test.xlsx", sheet="Second").iloc[0, 0], 99)

    def test_old_excel_engine(self):
        with patch("analytics.core.pd.read_excel", return_value=pd.DataFrame({"x": [1]})) as reader:
            read_data(b"placeholder", "old.xls")
            self.assertEqual(reader.call_args.kwargs["engine"], "xlrd")

    def test_empty_and_limit(self):
        with self.assertRaises(ValueError):
            read_data(b"x,y\n", "empty.csv")
        with patch("analytics.core.MAX_ROWS", 1):
            with self.assertRaises(ValueError):
                read_data(b"x\n1\n2\n", "big.csv")

    def test_quality_does_not_modify_original(self):
        df = pd.DataFrame({"label": ["East", "east ", "east "], "mixed": ["10", "unknown", "unknown"]})
        before = df.copy(deep=True)
        notes = " ".join(quality_observations(df))
        self.assertIn("look numeric", notes)
        self.assertIn("capitalization", notes)
        self.assertIn("repeated rows", notes)
        pd.testing.assert_frame_equal(df, before)

    def test_summary_and_invalid_values(self):
        df = pd.DataFrame({"x": [1.0, 3.0, None, np.inf]})
        result = descriptive_summary(df, ["x"]).iloc[0]
        self.assertEqual(result["Mean"], 2)
        self.assertEqual(result["Median"], 2)
        self.assertEqual(result["Valid count"], 2)
        self.assertEqual(result["Missing / invalid"], 2)
        self.assertAlmostEqual(result["Standard deviation"], 2 ** 0.5)
        self.assertTrue(np.isinf(df.iloc[-1, 0]))

    def test_missing_groups_and_empty_sum(self):
        df = pd.DataFrame({"g": ["A", "A", None, "B"], "v": [1, 3, 5, np.nan]})
        sums = grouped_summary(df, ["g"], "v", "Sum")
        self.assertEqual(len(sums), 3)
        self.assertEqual(sums.loc[sums.g == "A", "Result"].iloc[0], 4)
        self.assertTrue(pd.isna(sums.loc[sums.g == "B", "Result"].iloc[0]))
        counts = grouped_summary(df, ["g"])
        self.assertEqual(counts.Result.sum(), 4)

    def test_result_column_name_collision(self):
        df = pd.DataFrame({"Result": ["A", "A"], "Calculated result": ["B", "B"], "v": [1, 2]})
        result = grouped_summary(df, ["Result", "Calculated result"], "v", "Mean")
        self.assertEqual(result.iloc[0, -1], 1.5)

    def test_feedback_and_claim(self):
        text = "This proves marketing caused sales and will always work."
        feedback = " ".join(interpretation_feedback(text, "", "", False))
        for phrase in ["Causation", "Overstatement", "Context", "Support", "Business relevance"]:
            self.assertIn(phrase, feedback)
        self.assertTrue(check_claim(1.234, 1.23))
        self.assertFalse(check_claim(100, 105))
        self.assertIn("Predictive", question_hints("What will sales be next month?"))

    def test_report_sections_and_evidence(self):
        report = build_report("Question", "Decision", "Descriptive", "demo", {},
                              [{"title": "Summary", "context": "25 rows", "table": pd.DataFrame({"Mean": [10]})}])
        headings = [report.index("## " + s) for s in ["Evidence", "Interpretation", "Recommendation", "Limitations"]]
        self.assertEqual(headings, sorted(headings))
        self.assertIn("Mean\n10", report)

    def test_demo_expected_quality(self):
        raw = (Path(__file__).resolve().parents[1] / "data/demo_sales.csv").read_bytes()
        df = read_data(raw, "demo.csv")
        self.assertEqual(len(df), 25)
        self.assertEqual(int(df.duplicated().sum()), 1)
        self.assertEqual(int(df.isna().sum().sum()), 2)

    def test_reflections_export_with_four_main_sections(self):
        ladder = {"Observation": "Sales differ.", "Analysis": "A persistent gap.", "Insight": "Investigate capacity.", "Action": "Review stores."}
        challenge = {"What would change your conclusion?": "Comparable capacity data."}
        report = build_report("Q", "D", "Descriptive", "demo", {}, [], ladder=ladder, challenges=challenge)
        self.assertEqual([line for line in report.splitlines() if line.startswith("## ")],
                         ["## Evidence", "## Interpretation", "## Recommendation", "## Limitations"])
        for answer in [*ladder.values(), *challenge.values()]:
            self.assertIn(answer, report)
        self.assertIn("### Insight Ladder", report)
        self.assertIn("### Challenge Your Conclusion", report)


if __name__ == "__main__":
    unittest.main()
