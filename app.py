"""Run from this folder: python -m streamlit run app.py."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analytics.core import (
    AGGREGATIONS, build_report, chart_suggestions, check_claim, descriptive_summary,
    evidence_cells, grouped_summary, interpretation_feedback, numeric_columns,
    numeric_view, profile, quality_observations, question_hints, read_data,
)

st.set_page_config(page_title="MSIM Data-to-Decision Lab", page_icon="📊", layout="wide")
st.title("MSIM Data-to-Decision Lab")
st.caption("MSIM • FROM BUSINESS QUESTION TO INFORMED DECISION • VERSION 1")
st.write("Investigate a dataset, explain what the evidence supports, and recommend a next step.")
st.subheader("Data → Information → Analysis → Insight → Decision")
st.markdown("""- **Data** = raw observations
- **Information** = organized/contextualized data
- **Analysis** = examining patterns and relationships
- **Insight** = understanding why the result matters
- **Decision** = determining what action should be considered""")
st.caption("Move from describing results to explaining their business significance. Each step needs evidence and judgment.")

with st.sidebar:
    st.header("Your workspace")
    demo = st.toggle("Instructor Demo Mode", help="Loads fictional data and reveals teaching notes. Student writing is never filled in automatically.")
    st.caption("Nine stages • Fully local and deterministic • No API key")
    st.info("Work is held in this browser session. Download your decision brief before closing or reloading.")
    st.markdown("**Workflow**\n\n1. Upload\n2. Understand\n3. Frame\n4. Explore\n5. Visualize\n6. Insight Ladder\n7. Interpret\n8. Challenge Your Conclusion\n9. Recommend")

st.session_state.setdefault("evidence", [])


def save_evidence(title, table, context):
    if len(table) > 500:
        st.warning("This table exceeds 500 rows. Choose broader groups or fewer variables before adding it to your brief.")
        return
    entry = {"title": title, "table": table.copy(), "context": context}
    current = st.session_state.evidence
    # Replace the same analysis instead of accumulating repeated clicks.
    current[:] = [item for item in current if item["title"] != title]
    current.append(entry)
    st.success("Evidence added. It is available in Interpret and your downloaded brief.")


with st.expander("1 · Upload Data", expanded=True):
    st.caption("Start with the source: useful decisions depend on knowing what was observed and how it was recorded.")
    if demo:
        raw = (Path(__file__).parent / "data" / "demo_sales.csv").read_bytes()
        filename, sheet, encoding, separator = "demo_sales.csv (fictional)", 0, "utf-8-sig", ","
        source = "Fictional monthly store sales, January–June 2025; one row = one store-month."
        df = read_data(raw, "demo_sales.csv")
        st.info("Instructor dataset: store sales, marketing spend, and customer satisfaction. Intentional missing values, inconsistent labels, and a repeated record are included.")
    else:
        upload = st.file_uploader("Choose a CSV or Excel workbook", type=["csv", "xlsx", "xls"])
        st.caption("Up to 20 MB, 100,000 rows, and 200 columns. First row is the header. Blank cells count as missing; labels such as NA remain text. Headers may be disambiguated by the reader.")
        if upload is None:
            st.info("Upload a file to begin, or enable Instructor Demo Mode in the sidebar.")
            st.stop()
        raw, filename = upload.getvalue(), upload.name
        sheet, encoding, separator = 0, "utf-8-sig", ","
        if len(raw) > 20 * 1024 * 1024:
            st.error("Choose a file under 20 MB.")
            st.stop()
        try:
            if filename.lower().endswith(".csv"):
                c1, c2 = st.columns(2)
                encoding = c1.selectbox("CSV encoding", ["utf-8-sig", "cp1252", "latin-1"])
                delimiter = c2.selectbox("CSV separator", ["Comma", "Semicolon", "Tab"])
                separator = {"Comma": ",", "Semicolon": ";", "Tab": "\t"}[delimiter]
            else:
                engine = "xlrd" if filename.lower().endswith(".xls") else "openpyxl"
                with pd.ExcelFile(BytesIO(raw), engine=engine) as workbook:
                    sheet = st.selectbox("Worksheet", workbook.sheet_names)
            df = read_data(raw, filename, sheet, encoding, separator)
        except Exception as exc:
            st.error(f"Could not read this table: {exc}")
            st.caption("Check the separator/encoding, select another worksheet, or export an unencrypted workbook as CSV.")
            st.stop()
        source = f"{filename}" + (f"; worksheet: {sheet}" if isinstance(sheet, str) else "")

    identity = sha256(raw + repr((sheet, encoding, separator, demo)).encode()).hexdigest()
    if st.session_state.get("dataset_id") != identity:
        # Never carry writing or evidence silently into a different dataset or sheet.
        for key in list(st.session_state):
            if key.startswith("work_"):
                del st.session_state[key]
        st.session_state.evidence = []
        st.session_state.dataset_id = identity
    nums, columns = numeric_columns(df), list(df.columns)
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{len(df):,}")
    b.metric("Columns", len(columns))
    c.metric("Missing cells", int(df.isna().sum().sum()))
    d.metric("Repeated rows", int(df.duplicated().sum()))
    st.caption("Repeated rows counts exact repeats after their first occurrence, across all columns.")
    st.subheader("Preview · first 50 rows")
    st.dataframe(df.head(50).astype(str), width="stretch", hide_index=True)
    st.subheader("Column guide")
    st.dataframe(profile(df), width="stretch", hide_index=True)

if demo:
    with st.expander("Instructor walkthrough · Data to Decision", expanded=True):
        north = df.loc[df.region == "North", "sales"].mean()
        west = df.loc[df.region == "West", "sales"].mean()
        st.markdown(f"""**Teaching case:** Where should an operations manager investigate store performance before considering a budget change?

1. **Data:** inspect the raw store-month observations, including missing values and a repeated record. *Ask: What does one row tell us—and what does it leave out?*
2. **Information:** identify stores, regions, January–June 2025, and sales units. For this fictional class discussion, assume sales are in dollars. *Ask: Why must units and coverage be confirmed before comparing results?*
3. **Analysis:** group by `region`, choose **Mean** of `sales`, and select a bar chart. North averages **{north:,.0f}** across six observed sales values; West averages **{west:,.0f}** across five. Missing sales are excluded; repeated rows remain. *Ask: Are these regions comparable when each represents just one store?*
4. **Insight:** the observed gap identifies a performance question worth investigating; it does not establish a regional effect or show that marketing caused sales. *Ask: How might store size, demand, or the missing month change what this means to the manager?*
5. **Decision:** consider a focused operational review before reallocating budget. Ask the operations manager to obtain comparable store size, margins, demand, and the missing sales record, then reassess. *Ask: What evidence would make us abandon this action?*

Reveal this example for discussion, then have students write their own Insight Ladder and challenge it. Examples are teaching material, not automatically entered student answers.""")

with st.expander("2 · Understand the Data", expanded=demo):
    st.caption("Turn observations into information by establishing their meaning, coverage, and reliability.")
    st.write("An inferred type is the reader's best guess, not a business definition. A numeric customer ID is still an identifier.")
    observations = quality_observations(df)
    if not observations:
        st.success("No issues detected by these basic checks. Confirm meaning, coverage, units, and collection methods with the data owner.")
    for observation in observations:
        st.warning(observation)
    st.caption("These are review prompts. Original values and repeated rows are retained; no cleaning changes are written to your file.")
    keys = st.multiselect("Which columns should identify a unique record? (optional)", columns, key="work_keys")
    if keys:
        repeated = df.duplicated(subset=keys, keep=False)
        st.write(f"{int(repeated.sum()):,} rows share the selected key with another row. Missing keys also need review.")
        st.dataframe(df.loc[repeated].head(50).astype(str), hide_index=True)
    st.text_area("What does one row represent? Note the source, units, time period, and quality concerns.", key="work_context")

with st.expander("3 · Frame the Business Question", expanded=True):
    st.caption("A useful business question connects the analysis to a decision someone actually needs to make.")
    question = st.text_area("What business question will you investigate?", key="work_question",
                            placeholder="Example: How do average monthly sales compare across regions?")
    st.markdown("**Descriptive:** What happened?  \n**Predictive:** What might happen?  \n**Prescriptive:** What should we do?")
    if question.strip():
        hints = question_hints(question)
        st.info("Wording suggests: " + (", ".join(hints) if hints else "no clear category") + ". Choose based on the purpose; questions may combine types.")
    category = st.selectbox("Choose the primary question type", ["Choose…", "Descriptive", "Predictive", "Prescriptive"], key="work_category")
    if category in ["Predictive", "Prescriptive"]:
        st.info("Version 1 can explore historical evidence for this question. It does not forecast outcomes or optimize decisions. Identify what additional evidence would be needed.")
    decision = st.text_area("What decision should this analysis support, and who will make it?", key="work_decision")
    if demo:
        st.caption("Teaching example: compare mean sales by region to decide where to investigate performance. Ask why regional differences alone cannot justify moving the marketing budget.")

with st.expander("4 · Explore the Data", expanded=demo):
    st.caption("Do not calculate everything simply because you can. Look for evidence relevant to your business question.")
    selected = st.multiselect("Choose variables to explore", columns, default=["sales", "region"] if demo else [], key="work_variables")
    st.caption("Counts are non-missing observations; numeric summaries exclude missing/infinite values. Standard deviation describes spread and uses the sample formula (n−1). It is undefined for fewer than two valid values.")
    if selected:
        summary = descriptive_summary(df, selected)
        st.dataframe(summary, hide_index=True, width="stretch")
        if st.button("Add descriptive summary to evidence"):
            save_evidence("Descriptive summary", summary, f"Variables: {', '.join(selected)}. Full dataset: {len(df)} rows; no duplicate removal. Numeric summaries exclude missing/infinite values.")
        for col in [c for c in selected if c not in nums]:
            st.write(f"**Counts: {col}** (including missing; first 100 categories shown)")
            st.dataframe(df[col].value_counts(dropna=False).head(100).rename("Count"))
    st.subheader("Grouped summary / pivot table")
    g1, g2, g3 = st.columns(3)
    group = g1.selectbox("Group rows by", ["Choose…"] + columns, key="work_group")
    second = g2.selectbox("Pivot columns (optional)", ["None"] + [c for c in columns if c != group], key="work_second")
    agg = g3.selectbox("Summary measure", ["Row count"] + list(AGGREGATIONS), key="work_agg")
    value = None
    if agg != "Row count":
        value = st.selectbox("Numeric variable to summarize", ["Choose…"] + nums, key="work_value")
    if group != "Choose…" and (agg == "Row count" or value not in [None, "Choose…"]):
        groups = [group] + ([] if second == "None" else [second])
        result = grouped_summary(df, groups, value, agg)
        st.caption("Missing group labels are retained. Row count includes every row; non-missing count excludes missing/invalid numeric values. Other measures use valid numeric values. A blank sum means no valid values, not zero.")
        if second != "None" and result[second].nunique(dropna=False) <= 50 and result[group].nunique(dropna=False) <= 100:
            # Rendering missing labels as strings preserves their explicit group in a pivot.
            display = result.copy()
            for col in groups:
                display[col] = display[col].map(lambda v: "(missing)" if pd.isna(v) else repr(v))
            st.dataframe(display.pivot(index=group, columns=second, values=result.columns[-1]), width="stretch")
        else:
            st.dataframe(result.head(500), width="stretch", hide_index=True)
            if len(result) > 500:
                st.info("Preview limited to 500 groups. Choose broader grouping for a manageable evidence table.")
        if st.button("Add grouped summary to evidence"):
            save_evidence("Grouped summary", result, f"{agg} of {value if agg != 'Row count' else 'records'} by {', '.join(groups)}. Source rows: {len(df)}; missing group labels retained; duplicate rows retained.")

with st.expander("5 · Visualize", expanded=demo):
    st.caption("The best visualization is the one that makes the important comparison clear.")
    st.write("Start with the comparison you want your reader to make. You choose the chart and its variables.")
    for hint in chart_suggestions(df, selected, question):
        st.info(hint)
    chart = st.selectbox("Choose a chart", ["Choose…", "Bar chart", "Line chart", "Histogram", "Box plot", "Scatterplot"], key="work_chart")
    fig, chart_table, chart_context = None, None, ""
    clean = numeric_view(df)
    try:
        if chart == "Bar chart":
            x = st.selectbox("Category", columns, key="work_bar_x")
            measure = st.selectbox("Bar height", ["Row count", "Mean", "Median", "Sum"], key="work_bar_measure")
            y = st.selectbox("Numeric variable", nums, key="work_bar_y") if measure != "Row count" and nums else None
            if measure != "Row count" and not nums:
                st.info("No numeric columns available. Choose Row count.")
            else:
                table = grouped_summary(df, [x], y, measure)
                if len(table) > 50:
                    st.warning("This variable has more than 50 groups. Choose a simpler category for a readable bar chart.")
                else:
                    chart_table = table
                    plot = table.copy()
                    plot[x] = plot[x].map(lambda v: "(missing)" if pd.isna(v) else str(v))
                    fig = px.bar(plot, x=x, y=table.columns[-1], labels={table.columns[-1]: measure + (f" of {y}" if y else "")})
                    fig.update_xaxes(type="category")
                    chart_context = f"Bar chart: {measure} of {y or 'records'} by {x}. Missing category labels included; numeric summaries exclude missing/infinite values."
        elif chart in ["Histogram", "Box plot", "Scatterplot", "Line chart"]:
            if not nums:
                st.info("This chart needs a numeric variable. Review the inferred types in Upload Data.")
            else:
                y = st.selectbox("Numeric variable", nums, key="work_chart_y")
                if chart in ["Histogram", "Box plot"]:
                    group_by = st.selectbox("Compare groups (optional)", ["None"] + [c for c in columns if c != y], key="work_box_group") if chart == "Box plot" else "None"
                    plot = clean[[y] + ([] if group_by == "None" else [group_by])].dropna(subset=[y]).copy()
                    st.caption(f"{len(plot):,} valid numeric rows shown; {len(df)-len(plot):,} excluded for missing/invalid {y}.")
                    if group_by != "None":
                        plot[group_by] = plot[group_by].map(lambda v: "(missing)" if pd.isna(v) else str(v))
                    if group_by != "None" and plot[group_by].nunique() > 30:
                        st.warning("Choose a grouping variable with at most 30 categories.")
                    elif len(plot):
                        if chart == "Histogram":
                            bins = st.slider("Number of bins", 5, 50, 15, key="work_bins")
                            counts, edges = np.histogram(plot[y], bins=bins)
                            chart_table = pd.DataFrame({"Bin lower": edges[:-1], "Bin upper": edges[1:], "Count": counts})
                            fig = px.bar(chart_table, x=(edges[:-1] + edges[1:]) / 2, y="Count", labels={"x": y})
                            fig.update_traces(width=np.diff(edges), customdata=chart_table[["Bin lower", "Bin upper"]], hovertemplate="[%{customdata[0]}, %{customdata[1]}): %{y}<extra></extra>")
                        else:
                            fig = px.box(plot, y=y, x=None if group_by == "None" else group_by, points=False)
                            chart_table = descriptive_summary(clean, [y]) if group_by == "None" else grouped_summary(clean, [group_by], y, "Median")
                        chart_context = f"{chart} of {y}; grouping: {group_by}; {len(plot)} valid rows, {len(df)-len(plot)} excluded. Histogram bins include the lower bound; the last bin also includes its upper bound. Box-plot evidence table reports descriptive statistics or group medians."
                elif chart == "Scatterplot":
                    others = [c for c in nums if c != y]
                    if not others:
                        st.info("Choose a dataset with at least two numeric variables.")
                    else:
                        x = st.selectbox("Horizontal numeric variable", others, key="work_scatter_x")
                        plot = clean[[x, y]].dropna()
                        st.caption(f"{len(plot)} complete pairs; {len(df)-len(plot)} rows excluded. No trend line, prediction, or causal inference is fitted.")
                        if len(plot) > 10000:
                            st.warning("More than 10,000 pairs: use grouped charts for readability. No points have been silently sampled.")
                        elif len(plot):
                            fig = px.scatter(plot, x=x, y=y, opacity=0.6)
                            chart_table = descriptive_summary(plot, [x, y])
                            chart_context = f"Scatterplot: {x} and {y}. Table summarizes {len(plot)} complete pairs, not a relationship test; {len(df)-len(plot)} excluded."
                else:
                    x = st.selectbox("Time or ordered numeric variable", [c for c in columns if c != y], key="work_line_x") if len(columns) > 1 else None
                    kind = st.radio("How should the horizontal variable be read?", ["Date / time", "Ordered number"], horizontal=True, key="work_line_kind")
                    fmt = st.text_input("Date format (for example %Y-%m-%d)", "%Y-%m-%d", key="work_date_format") if kind == "Date / time" else None
                    agg_line = st.selectbox("Combine rows at the same time/value using", ["Mean", "Sum", "Median"], key="work_line_agg")
                    if x:
                        plot = clean[[x, y]].copy()
                        plot[x] = pd.to_datetime(plot[x].astype(str), format=fmt, errors="coerce") if kind == "Date / time" else pd.to_numeric(plot[x], errors="coerce").replace([np.inf, -np.inf], np.nan)
                        plot = plot.dropna()
                        st.caption(f"{len(plot)} valid rows; {len(df)-len(plot)} excluded due to missing/unreadable horizontal values or missing/invalid {y}. Lines connect observed points; absent periods are not filled in.")
                        if len(plot):
                            chart_table = grouped_summary(plot, [x], y, agg_line).sort_values(x)
                            fig = px.line(chart_table, x=x, y=chart_table.columns[-1], markers=True, labels={chart_table.columns[-1]: f"{agg_line} of {y}"})
                            chart_context = f"Line chart: {agg_line} of {y} by {x} ({kind}); {len(plot)} valid rows; {len(df)-len(plot)} excluded."
        if fig is not None:
            fig.update_layout(template="plotly_white", height=420, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, width="stretch")
            st.caption(chart_context)
            st.dataframe(chart_table.head(100), hide_index=True, width="stretch")
            if st.button("Add chart's supporting table to evidence"):
                save_evidence(f"{chart} supporting table", chart_table, chart_context)
        elif chart != "Choose…":
            st.caption("A chart appears when the selected variables have enough valid data.")
    except (ValueError, TypeError, OverflowError) as exc:
        st.warning(f"This chart could not be created with these choices: {exc}. Check the variables and date format.")

with st.expander("6 · Insight Ladder", expanded=True):
    st.write("Observation → Analysis → Insight → Action")
    st.info("These are increasingly interpretive steps. An observation alone is not a business insight: explain why the evidence matters to this organization and decision maker. An insight need not establish a cause.")
    ladder = {}
    for name, prompt in [
        ("Observation", "What do you see?"),
        ("Analysis", "What pattern or relationship does the evidence suggest?"),
        ("Insight", "Why does this matter to the organization or decision maker?"),
        ("Action", "What should the decision maker consider doing?"),
    ]:
        ladder[name] = st.text_area(f"{name}: {prompt}", key=f"work_ladder_{name.lower()}")
    ladder_missing = [name for name, answer in ladder.items() if not answer.strip()]
    if ladder_missing:
        st.caption("Required for a completed brief — still to complete: " + ", ".join(ladder_missing) + ". Drafts can be saved at any time.")
    else:
        st.success("All four ladder steps are filled in. Review whether each step follows from the evidence; completion is not a judgment of correctness.")
    if demo:
        st.caption("Class discussion: 'North has higher mean sales' is an observation. What makes that finding relevant to an operations manager? Ask students to name an alternative explanation before proposing action.")

with st.expander("7 · Interpret", expanded=True):
    st.caption("Describe what the evidence supports before explaining what you think it means.")
    st.write("Use your Insight Ladder to write a connected interpretation. Distinguish the observed pattern from its business significance and your assumptions.")
    interpretation = st.text_area("Write your interpretation first", key="work_interpretation", height=150,
                                  placeholder="What pattern do you see? Cite the values, group, units, and period. What remains uncertain?")
    st.caption("Feedback is a rule-based writing aid, not an AI grader. It cannot establish that every free-text statement is supported. It never writes your interpretation.")
    evidence = st.session_state.evidence
    if st.button("Review my interpretation", disabled=not interpretation.strip()):
        st.subheader("Review prompts")
        for message in interpretation_feedback(interpretation, question, decision, bool(evidence)):
            st.write("• " + message)
    with st.expander("Advanced Evidence Check", expanded=False):
        st.caption("Optional: compare one numerical claim with a saved evidence value. This check is not required to complete the workflow.")
        if evidence:
            chosen = st.selectbox("Evidence to check against", range(len(evidence)), format_func=lambda i: evidence[i]["title"], key="work_evidence_choice")
            item = evidence[chosen]
            st.caption(item["context"])
            st.dataframe(item["table"], hide_index=True, width="stretch")
            cells = evidence_cells(item["table"])
            verify = st.checkbox("Check a specific numerical claim from my interpretation", key="work_verify")
            if verify and cells:
                cell = st.selectbox("Which evidence value does your claim refer to?", list(cells), key="work_claim_cell")
                claim = st.number_input("Number stated in your interpretation (use the table's units)", value=0.0, format="%.4f", key="work_claim")
                if st.button("Check numerical claim", disabled=not interpretation.strip()):
                    actual = cells[cell]
                    if check_claim(actual, claim):
                        st.success(f"Numerical claim matches the selected evidence within 0.005: {actual:,.4f}. This confirms only this value, not the full interpretation.")
                    else:
                        st.warning(f"Numerical claim does not match the selected evidence. You entered {claim:,.4f}; the table reports {actual:,.4f}. Check the metric, units, group, and denominator.")
            elif verify:
                st.info("This evidence table has no finite numeric values to compare.")
        else:
            st.info("Add a summary or a chart's supporting table to evidence to make a numerical comparison.")

with st.expander("8 · Challenge Your Conclusion", expanded=True):
    st.caption("Test your proposed action from the Insight Ladder before making a final recommendation. A useful conclusion can withstand questions and change when the evidence changes.")
    challenges = {}
    for key, prompt in [
        ("support", "What evidence supports your recommendation?"),
        ("change", "What evidence would make you change your conclusion?"),
        ("overclaim", "Are you claiming more than the data shows?"),
        ("manager", "What additional information would a manager want before acting?"),
    ]:
        challenges[prompt] = st.text_area(prompt, key=f"work_challenge_{key}")
    st.caption("Respond to all four questions for a completed brief. Explain your reasoning, including when your answer is 'no'.")

with st.expander("9 · Recommend", expanded=True):
    st.caption("Recommendations should follow from evidence rather than merely sound reasonable.")
    st.write("Build a decision brief with four distinct parts. Separate what you observed from what you think it means and what you propose doing.")
    st.subheader("Evidence")
    evidence_text = st.text_area("State the key facts, units, and comparisons", key="work_evidence_text")
    st.caption(f"{len(st.session_state.evidence)} supporting tables will be attached under Evidence in the downloaded brief.")
    if st.session_state.evidence and st.button("Clear saved evidence tables"):
        st.session_state.evidence = []
        st.rerun()
    st.subheader("Interpretation")
    st.write(interpretation or "Write your interpretation in step 7. It will appear here.")
    st.subheader("Recommendation")
    recommendation = st.text_area("What action do you recommend, who owns it, and how should its success be measured?", key="work_recommendation")
    st.subheader("Limitations")
    limitations = st.text_area("What could change this conclusion? Consider data quality, coverage, time period, and alternative explanations.", key="work_limitations")
    sections = {"Evidence": evidence_text, "Interpretation": interpretation,
                "Recommendation": recommendation, "Limitations": limitations}
    complete = bool(question.strip() and decision.strip() and category != "Choose…" and all(v.strip() for v in sections.values()) and not ladder_missing and all(v.strip() for v in challenges.values()))
    st.caption("A completed brief requires all four report sections, a question, a decision, a question type, all four Insight Ladder steps, and all four challenge responses. Advanced Evidence Check is optional. You can save a draft at any time.")
    report = build_report(question, decision, category, source + "\n\nStudent context: " + st.session_state.get("work_context", ""), sections, st.session_state.evidence, ladder=ladder, challenges=challenges)
    st.download_button("Download completed brief" if complete else "Download draft brief", report,
                       file_name="analytics-decision-brief.md", mime="text/markdown")
    with st.expander("Preview the decision brief"):
        st.markdown(report)
    if demo:
        with st.expander("Instructor discussion notes"):
            st.markdown("""1. Identify the repeated store-month before trusting totals.
2. Compare `region` labels: `East` and `east ` should prompt a question, not an automatic correction.
3. Discuss why a mean with missing sales describes only observed values.
4. Use a bar chart of mean sales by region, then a scatterplot of marketing spend and sales.
5. Ask students to distinguish an association from evidence that marketing caused sales.
6. Compare the four Insight Ladder answers: which sentence first explains business significance rather than just a pattern?
7. Ask another student to challenge the proposed action: what evidence would reverse it, and what else would a manager need?
8. Require a recommendation with an owner, a testable next step, and a limitation. Revisit the lifecycle: where did raw data become useful insight?

Demo mode reveals a worked Data → Information → Analysis → Insight → Decision example and selects two exploration variables. It leaves the question, chart choice, Insight Ladder, interpretation, challenge responses, and recommendation to the instructor or student.""")
