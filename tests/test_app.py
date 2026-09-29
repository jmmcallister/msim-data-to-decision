from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def demo(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        app.toggle[0].set_value(True).run()
        self.assertFalse(app.exception)
        return app

    def click(self, app, label):
        next(b for b in app.button if b.label == label).click().run()
        self.assertFalse(app.exception)

    def test_workflow(self):
        app = self.demo()
        app.text_area(key="work_question").set_value("How do average sales compare by region?")
        app.text_area(key="work_decision").set_value("The manager will choose where to investigate.")
        app.selectbox(key="work_category").select("Descriptive").run()
        self.click(app, "Add descriptive summary to evidence")
        app.selectbox(key="work_group").select("region").run()
        app.selectbox(key="work_agg").select("Mean").run()
        app.selectbox(key="work_value").select("sales").run()
        self.click(app, "Add grouped summary to evidence")
        app.text_area(key="work_interpretation").set_value("Marketing always causes higher sales in this sample of 25 records.").run()
        self.click(app, "Review my interpretation")
        self.assertTrue(any("Causation check" in x.value for x in app.markdown))
        self.assertEqual(len(app.session_state["evidence"]), 2)
        self.click(app, "Clear saved evidence tables")
        self.assertEqual(len(app.session_state["evidence"]), 0)

    def test_all_chart_types(self):
        app = self.demo()
        for chart in ["Bar chart", "Histogram", "Box plot", "Scatterplot", "Line chart"]:
            app.selectbox(key="work_chart").select(chart).run()
            self.assertFalse(app.exception, chart)
            self.assertEqual(len(app.get("plotly_chart")), 1, chart)
            self.click(app, "Add chart's supporting table to evidence")
        self.assertEqual(len(app.session_state["evidence"]), 5)

    def test_numeric_claim_and_pivot(self):
        app = self.demo()
        app.selectbox(key="work_group").select("region").run()
        app.selectbox(key="work_second").select("month").run()
        self.click(app, "Add grouped summary to evidence")
        app.text_area(key="work_interpretation").set_value("There are 999 records in this group in the sample.")
        app.checkbox(key="work_verify").check().run()
        app.number_input(key="work_claim").set_value(999).run()
        self.click(app, "Check numerical claim")
        self.assertTrue(any("does not match" in x.value for x in app.warning))
        app.number_input(key="work_claim").set_value(2).run()
        self.click(app, "Check numerical claim")
        self.assertTrue(any("Numerical claim matches" in x.value for x in app.success))

    def test_uploaded_data_change_resets_work(self):
        # AppTest has no file-uploader setter; replace only that widget's return
        # value while exercising the real reader and the rest of the app.
        script = f'''
import streamlit as st
from io import BytesIO
from pathlib import Path
fixture = st.selectbox("Test dataset", ["first", "second"])
raw = b"group,value\\nA,1\\nB,2\\n" if fixture == "first" else b"group,value\\nC,99\\nD,100\\n"
upload = BytesIO(raw)
upload.name = "class.csv"
st.file_uploader = lambda *args, **kwargs: upload
__file__ = {str(APP)!r}
exec(compile(Path(__file__).read_text(encoding="utf-8"), __file__, "exec"))
'''
        app = AppTest.from_string(script, default_timeout=30).run()
        self.assertFalse(app.exception)
        app.text_area(key="work_question").set_value("Old question")
        app.text_area(key="work_ladder_insight").set_value("Old insight")
        app.text_area(key="work_challenge_change").set_value("Old challenge")
        app.multiselect(key="work_variables").set_value(["value"]).run()
        self.click(app, "Add descriptive summary to evidence")
        app.selectbox[0].select("second").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area(key="work_question").value, "")
        self.assertEqual(len(app.session_state["evidence"]), 0)
        self.assertEqual(app.multiselect(key="work_variables").value, [])
        self.assertEqual(app.text_area(key="work_ladder_insight").value, "")
        self.assertEqual(app.text_area(key="work_challenge_change").value, "")

    def test_lifecycle_visible_before_upload(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertEqual(app.title[0].value, "MSIM Data-to-Decision Lab")
        self.assertIn("Data → Information → Analysis → Insight → Decision", [s.value for s in app.subheader])
        text = " ".join(x.value for x in app.markdown)
        for definition in ["raw observations", "organized/contextualized data", "examining patterns", "why the result matters", "what action should be considered"]:
            self.assertIn(definition, text)

    def test_required_reflections_and_optional_advanced_check(self):
        app = self.demo()
        labels = [e.label for e in app.expander]
        self.assertLess(labels.index("5 · Visualize"), labels.index("6 · Insight Ladder"))
        self.assertLess(labels.index("8 · Challenge Your Conclusion"), labels.index("9 · Recommend"))
        advanced = next(e for e in app.expander if e.label == "Advanced Evidence Check")
        self.assertFalse(advanced.proto.expanded)
        app.text_area(key="work_question").set_value("Where should we investigate sales?")
        app.text_area(key="work_decision").set_value("Operations manager chooses a review.")
        app.selectbox(key="work_category").select("Descriptive")
        for key in ["work_evidence_text", "work_interpretation", "work_recommendation", "work_limitations"]:
            app.text_area(key=key).set_value("A student response.")
        app.run()
        self.assertEqual(app.get("download_button")[0].label, "Download draft brief")
        for name in ["observation", "analysis", "insight", "action"]:
            app.text_area(key=f"work_ladder_{name}").set_value("A reasoned ladder response.")
        app.run()
        self.assertEqual(app.get("download_button")[0].label, "Download draft brief")
        for name in ["support", "change", "overclaim", "manager"]:
            app.text_area(key=f"work_challenge_{name}").set_value("A considered challenge response.")
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.get("download_button")[0].label, "Download completed brief")
        report = next(x.value for x in app.markdown if x.value.startswith("# MSIM Data-to-Decision Lab — Decision brief"))
        self.assertIn("### Insight Ladder", report)
        self.assertIn("### Challenge Your Conclusion", report)
        self.assertIn("A reasoned ladder response.", report)
        self.assertIn("A considered challenge response.", report)
        app.text_area(key="work_ladder_insight").set_value("   ").run()
        self.assertEqual(app.get("download_button")[0].label, "Download draft brief")

    def test_demo_teaches_without_filling_answers(self):
        app = self.demo()
        notes = " ".join(m.value for m in app.markdown)
        for stage in ["Data", "Information", "Analysis", "Insight", "Decision"]:
            self.assertIn(f"**{stage}:**", notes)
        self.assertIn("55,500", notes)
        self.assertIn("39,200", notes)
        self.assertIn("What evidence would make us abandon this action?", notes)
        for area in app.text_area:
            if area.key.startswith(("work_ladder_", "work_challenge_")):
                self.assertEqual(area.value, "")

    def test_text_only_data_chart_guard(self):
        script = f'''
import streamlit as st
from io import BytesIO
from pathlib import Path
upload = BytesIO(b"category,empty\\nA,\\nB,\\n")
upload.name = "text.csv"
st.file_uploader = lambda *args, **kwargs: upload
__file__ = {str(APP)!r}
exec(compile(Path(__file__).read_text(encoding="utf-8"), __file__, "exec"))
'''
        app = AppTest.from_string(script, default_timeout=30).run()
        self.assertFalse(app.exception)
        app.selectbox(key="work_chart").select("Histogram").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("plotly_chart")), 0)


if __name__ == "__main__":
    unittest.main()
