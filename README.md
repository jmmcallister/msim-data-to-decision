# MSIM Data-to-Decision Lab — Version 1

A Python/Streamlit classroom app for graduate MSIM business students learning to translate data into useful business insight. This is a refinement of the original Version 1, preserving its import, quality-review, exploration, charting, and reporting tools. Students make choices, explain business significance, challenge their reasoning, and propose an action. All behavior is local and deterministic: no AI API, LLM, model training, or API key.

## Pedagogical purpose

The landing page introduces **Data → Information → Analysis → Insight → Decision**, visible before a file is uploaded:

- **Data** = raw observations.
- **Information** = organized/contextualized data.
- **Analysis** = examining patterns and relationships.
- **Insight** = understanding why the result matters.
- **Decision** = determining what action should be considered.

An observation alone is not a business insight. The course emphasis is on connecting a supported finding to an organizational concern and a decision maker, while making assumptions and uncertainty explicit. Brief prompts throughout the app explain why each stage matters in business language. For example: “Do not calculate everything simply because you can. Look for evidence relevant to your business question.”

## Run locally on Windows (PowerShell)

1. Install **Python 3.12 (64-bit)** from [python.org](https://www.python.org/downloads/windows/). Include the Python launcher when prompted. Close and reopen PowerShell after installation.
2. Download/extract this project if necessary. Open PowerShell in the folder containing `app.py` and `requirements.txt`. For this delivered copy:

   ```powershell
   cd "C:\Users\jmnor\Documents\Codex\2026-09-28\build-a-simple-web-application-for\outputs\msim-analytics"
   ```

3. Create an isolated environment and install dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

5. Open **http://localhost:8501** if your browser does not open automatically. Upload data or turn on **Instructor Demo Mode** in the sidebar. Keep PowerShell open while using the app. Press **Ctrl+C** in PowerShell to stop it.

On later visits, repeat only steps 2 and 4. Environment activation is unnecessary, so PowerShell's script execution policy does not need to change. Installing dependencies requires internet access; routine app use does not.

If `py` is not recognized, use the full path to the installed Python executable in step 3, or use `python -m venv .venv` after confirming `python --version` is 3.12. Do not type the commands into Python's `>>>` prompt. If port 8501 is occupied, append `--server.port 8502` and open http://localhost:8502. If importing a module fails, run the installation command again with the same `.venv` interpreter used to launch the app.

Official command-line setup reference: [Streamlit installation](https://docs.streamlit.io/get-started/installation/command-line).

## Project structure

```text
msim-analytics/
  app.py                      # Nine-stage guided Streamlit interface
  analytics/
    __init__.py
    core.py                   # Import, summaries, coaching, report helpers
  data/
    demo_sales.csv            # Fictional store-month observations
  tests/
    test_core.py              # Import and analytical correctness checks
    test_app.py               # Interactive workflow/chart smoke checks
  .streamlit/
    config.toml               # Classroom theme, local binding, upload cap
  .gitignore
  requirements.txt
  README.md
```

## Classroom workflow

1. **Upload Data:** CSV, `.xlsx`, or legacy `.xls`; select the Excel sheet or CSV separator/encoding. Inspect a 50-row preview, row/column totals, inferred types, missing counts, distinct counts, and repeated rows.
2. **Understand the Data:** review missing values, mixed numeric/text entries, whitespace/case differences, and exact repeats. Select business keys to inspect possible duplicate records. Record units, source, and what one row represents. No automatic repairs are made.
3. **Frame the Business Question:** write a question, inspect simple keyword suggestions, choose descriptive/predictive/prescriptive, and identify the decision and decision maker. Predictive and prescriptive questions are allowed, but V1 supplies only exploratory historical evidence.
4. **Explore the Data:** explicitly choose variables, inspect numeric summaries and category counts, and create grouped or two-way pivot summaries. Click **Add … to evidence** to retain a table for the brief.
5. **Visualize:** read suggestions informed by variable types and question wording; choose a bar chart, line chart, histogram, box plot, or scatterplot. Choose the variables and aggregation. Add a chart's supporting table to evidence if useful.
6. **Insight Ladder:** after exploration and visualization, complete four increasingly interpretive steps: **Observation** (What do you see?), **Analysis** (What pattern or relationship does the evidence suggest?), **Insight** (Why does this matter to the organization or decision maker?), and **Action** (What should the decision maker consider doing?). All four responses are required for a completed brief. Insight concerns business significance; it does not require an unsupported causal explanation.
7. **Interpret:** use the ladder to write a connected interpretation first, then request rule-based feedback. Review causation, certainty, statistical-significance wording, context, and missing evidence. The optional, collapsed **Advanced Evidence Check** contains the evidence-table/cell selector and numerical claim entry. Its separate **Check numerical claim** button checks agreement within 0.005 in the table's units. Neither opening this section nor running a numerical check is required. The app does **not** extract or validate every claim in free text, assess study design, or grade students.
8. **Challenge Your Conclusion:** before the final recommendation, reflect on the proposed action from the ladder. Answer all four questions: What evidence supports your recommendation? What evidence would make you change your conclusion? Are you claiming more than the data shows? What additional information would a manager want before acting?
9. **Recommend:** complete four distinct report sections: **Evidence, Interpretation, Recommendation, Limitations**. Recommendations should follow from evidence rather than merely sound reasonable. Download a Markdown brief with saved evidence tables and source context. The interpretation is reused from step 7; the Insight Ladder appears as a subsection under Interpretation, and challenge responses under Limitations, preserving the four main report sections.

The completed-brief label requires a question, decision, selected question type, all four report sections, all four ladder responses, and all four challenge responses. Whitespace-only responses are incomplete. Students can navigate freely and download a draft at any time; this supports revision without skipping required reflection in a completed brief. The label means required fields are filled in, not that the reasoning is correct. The instructor remains responsible for evaluating claims. Support checks are deliberately transparent heuristics and can miss nuanced wording or flag cautious statements.

## Instructor Demo Mode

The sidebar toggle loads 25 fictional store-month records (January–June 2025), expands the workflow, selects `sales` and `region` for exploration, and reveals discussion prompts. It includes:

- One exact repeated record (24 distinct records).
- One missing sales value and one missing satisfaction score.
- `East` versus `east ` category labels.
- An `unknown` staff-count value mixed with numeric-looking entries.

An expanded **Instructor walkthrough · Data to Decision** demonstrates the full lifecycle using the existing dataset. It reveals teaching examples and discussion questions without filling in student answers:

1. **Data:** inspect raw records. What can one store-month observation tell us, and what does it omit?
2. **Information:** establish store, region, time period, units, and quality issues. For this fictional classroom example, assume sales are dollars; discuss why real units must be confirmed.
3. **Analysis:** compare mean sales by region with a bar chart. The walkthrough calculates the displayed values from the demo data: North 55,500 over six observed sales values; West 39,200 over five. Why do missing records and one store per region limit comparability?
4. **Insight:** the observed gap identifies a performance question worth investigating. What could store size, local demand, or the missing month imply for its business significance? A regional difference does not establish a regional effect or a marketing cause.
5. **Decision:** consider an operational review before reallocating budget. What additional evidence would the manager need, and what would reverse the proposed action?

Have students complete the Insight Ladder, compare observations with insights, and challenge one another's proposed actions. Finish with an owner, a testable next step, and limitations. Additional instructor notes in Recommend connect these discussions back to the lifecycle. A marketing/sales scatterplot also supports discussion of association versus causation. The example represents a small observational sample, not evidence for a budget reallocation by itself.

## Data and calculation rules

- Original uploaded bytes and values are not overwritten. No deduplication, imputation, modeling, optimization, or automatic type conversion is applied to the source table.
- File readers infer types. Blank cells are missing; literal `NA`, `N/A`, and `unknown` remain text. Whitespace-only strings are flagged separately. Duplicate/blank headers may be renamed by pandas; the column guide shows the imported names. CSV type inference may strip leading zeroes from numeric-looking identifiers: inspect IDs and prepare a text-preserving source if those zeroes matter.
- Numeric summaries exclude missing and infinite values, disclose counts, and use sample standard deviation (`n−1`). Means are unweighted. A sum over no valid values is blank, not zero. Counts distinguish rows from non-missing observations. Numeric identifiers must not be treated as measures merely because their storage type is numeric.
- Exact repeated rows are counted after the first occurrence and retained in all calculations. Business-key checks show **all** rows participating in a repeated key.
- Grouping retains missing group labels. The pivot is a display of the same grouped result. For readability, wider pivots fall back to a long table. Saved evidence is limited to 500 rows per table; the app will ask for broader grouping rather than silently save a truncated table.
- Scatterplots use complete numeric pairs and stop above 10,000 pairs rather than silently sample. Bars allow up to 50 groups and grouped boxes up to 30. Line charts require an explicit date format or ordered-number choice; conversion is only for the chart, and excluded rows are disclosed. Same-time observations are aggregated by your chosen measure. Lines connect observed periods; missing periods are not imputed.
- Histogram bins include their lower bound; only the last bin includes its upper bound. Plotly box plots display distribution summaries without individual outlier points. Saved box-plot tables give descriptive statistics or group medians; scatterplot tables summarize complete pairs, not correlation or causation.
- Upload limits: 20 MB, 100,000 rows, 200 columns. Excel sheets with formulas must have cached values saved by Excel; encrypted workbooks are unsupported. Worksheet XML can be larger than the compressed workbook, so use classroom-sized trusted files.
- Saved evidence is a snapshot. Changing chart controls does not change an existing snapshot until **Add … to evidence** is clicked again. A new snapshot replaces the same named analysis. Changing file contents, sheet, import settings, or demo mode resets analysis fields and saved evidence to prevent mixing sources.

## Privacy and persistence

The app binds to localhost. Uploaded data are processed by your local Python process, without a database or external AI calls. No application code writes uploads to disk. Work and evidence are session-only; a browser refresh or server restart may lose them. Download the brief before leaving. The brief is Markdown and includes evidence tables as CSV blocks; charts themselves are not embedded. No student accounts, gradebook, collaboration, or automatic submission are included. Streamlit usage telemetry is disabled in the project configuration.

## Run the checks

From the project folder after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover CSV settings, Excel worksheet selection, legacy Excel engine routing, missing/invalid values, duplicate/format warnings, non-destructive operations, summary accuracy, report structure, demo integrity, all five chart paths, evidence selection, pivot interaction, and interpretation feedback. The legacy `.xls` test checks engine routing; use an actual legacy workbook for a manual compatibility check if your class relies on that format.

All 21 tests pass for this refinement. New coverage checks the renamed landing page and lifecycle before upload, workflow order, required ladder and challenge responses, whitespace rejection, optional/collapsed Advanced Evidence Check, matching and mismatching numerical claims, reflection export under four main sections, and demo guidance that leaves student answers blank. Changed-upload tests also verify that ladder and challenge responses reset with the previous evidence. Existing data-operation and chart tests are preserved. Requirements are unchanged and pin the six direct dependencies to the versions used for validation on Python 3.12; transitive dependencies are resolved by pip.
