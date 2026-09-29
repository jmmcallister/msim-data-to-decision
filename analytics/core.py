"""Data operations are read-only; no imputation, deduplication, or model training."""
from io import BytesIO
import re

import numpy as np
import pandas as pd

MAX_ROWS = 100_000
MAX_COLUMNS = 200
AGGREGATIONS = {"Mean": "mean", "Median": "median", "Sum": "sum",
                "Minimum": "min", "Maximum": "max", "Standard deviation": "std",
                "Non-missing count": "count"}


def read_data(raw, filename, sheet=0, encoding="utf-8-sig", separator=","):
    """Blank cells are missing; literal strings such as 'NA' remain labels."""
    options = dict(keep_default_na=False, na_values=[""])
    stream = BytesIO(raw)
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(stream, encoding=encoding, sep=separator,
                         nrows=MAX_ROWS + 1, **options)
    else:
        engine = "xlrd" if filename.lower().endswith(".xls") else "openpyxl"
        df = pd.read_excel(stream, sheet_name=sheet, engine=engine,
                           nrows=MAX_ROWS + 1, **options)
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError(f"Use at most {MAX_ROWS:,} rows and {MAX_COLUMNS} columns. No partial dataset was loaded.")
    if df.empty:
        raise ValueError("This table has no data rows. Choose a sheet/file with a header and data.")
    # Display-safe unique names, including collisions between numeric and text headers.
    names, used = [], set()
    for original in df.columns:
        base, candidate, n = str(original), str(original), 2
        while candidate in used:
            candidate = f"{base} ({n})"
            n += 1
        used.add(candidate)
        names.append(candidate)
    df.columns = names
    return df


def numeric_columns(df):
    return [c for c in df.select_dtypes(include="number").columns
            if not pd.api.types.is_bool_dtype(df[c])]


def profile(df):
    return pd.DataFrame({"Column": df.columns,
                         "Inferred type": [str(df[c].dtype) for c in df],
                         "Missing": df.isna().sum().values,
                         "Missing (%)": (df.isna().mean() * 100).round(1).values,
                         "Distinct non-missing values": df.nunique().values})


def quality_observations(df):
    notes = []
    for col in df:
        s = df[col]
        missing = int(s.isna().sum())
        if missing:
            notes.append(f"{col}: {missing:,} missing values ({missing / len(df):.1%}). Ask why they are missing before deciding how to handle them.")
        if col in numeric_columns(df):
            nonfinite = int(np.isinf(s.to_numpy(dtype=float, na_value=np.nan)).sum())
            if nonfinite:
                notes.append(f"{col}: {nonfinite} infinite values. Summaries and charts exclude these invalid numeric values and disclose the exclusion.")
        else:
            values = s.dropna().astype(str)
            if values.empty:
                continue
            parsed = pd.to_numeric(values, errors="coerce")
            count = int(parsed.notna().sum())
            if 0 < count < len(values):
                notes.append(f"{col}: {count} of {len(values)} non-missing entries look numeric, while others do not. This may be mixed formats or a legitimate category/identifier; inspect before converting.")
            if values.str.strip().eq("").any():
                notes.append(f"{col}: whitespace-only entries appear present but may represent missing information.")
            if values.nunique() > values.str.strip().str.casefold().nunique():
                notes.append(f"{col}: labels differ only by spaces or capitalization. Decide whether they mean the same thing.")
    duplicates = int(df.duplicated().sum())
    if duplicates:
        notes.append(f"{duplicates:,} exact repeated rows after the first occurrence. Repeated transactions may be valid; verify before removing anything.")
    return notes


def numeric_view(df):
    result = df.copy(deep=True)
    nums = numeric_columns(result)
    result[nums] = result[nums].replace([np.inf, -np.inf], np.nan)
    return result


def descriptive_summary(df, columns):
    clean = numeric_view(df)
    rows = []
    for col in columns:
        s = clean[col]
        row = {"Variable": col, "Valid count": int(s.notna().sum()),
               "Missing / invalid": int(s.isna().sum()), "Distinct values": int(s.nunique())}
        if col in numeric_columns(clean):
            row.update({"Mean": s.mean(), "Median": s.median(), "Minimum": s.min(),
                        "Maximum": s.max(), "Standard deviation": s.std()})
        rows.append(row)
    return pd.DataFrame(rows)


def grouped_summary(df, groups, value=None, aggregation="Row count"):
    clean = numeric_view(df)
    grouped = clean.groupby(groups, dropna=False, observed=True, sort=False)
    if aggregation == "Row count":
        result = grouped.size().rename("Result")
    else:
        series = grouped[value]
        if aggregation == "Sum":
            result = series.sum(min_count=1).rename("Result")
        else:
            result = series.agg(AGGREGATIONS[aggregation]).rename("Result")
    # reset_index can collide with a user column named Result.
    result.name = next(name for name in ["Result", "Calculated result", "Calculated result (2)"] if name not in groups)
    return result.reset_index()


def question_hints(question):
    q = question.lower()
    suggestions = []
    if re.search(r"\b(should|recommend|allocate|optimi[sz]e|best action)\b", q):
        suggestions.append("Prescriptive")
    if re.search(r"\b(predict|forecast|future|next|will|likely)\b", q):
        suggestions.append("Predictive")
    if re.search(r"\b(how many|what happened|average|compare|trend|which|difference)\b", q):
        suggestions.append("Descriptive")
    return suggestions


def chart_suggestions(df, columns, question):
    nums = [c for c in columns if c in numeric_columns(df)]
    notes = []
    if nums:
        notes.append("Histogram: see how one numeric variable is distributed. Box plot: inspect its spread and unusual values.")
    if len(nums) >= 2:
        notes.append("Scatterplot: inspect the relationship between two numeric variables; a pattern does not establish causation.")
    if columns:
        notes.append("Bar chart: compare category counts or a numeric summary across groups.")
    if re.search(r"trend|time|month|year|week|day", question, re.I) or any(pd.api.types.is_datetime64_any_dtype(df[c]) for c in columns):
        notes.append("Line chart: show change over a confirmed date or ordered numeric variable. Check date format and ordering first.")
    return notes


def interpretation_feedback(text, question, decision, has_evidence):
    """Coaching prompts, never a semantic truth verdict on arbitrary prose."""
    messages = []
    if re.search(r"\b(caus\w*|causation|because|leads? to|drives?|results? in|impact\w*)\b", text, re.I):
        messages.append("Causation check: this wording may claim cause and effect. Observational summaries show patterns; explain the study design or use 'associated with'.")
    if re.search(r"\b(proves?|always|never|guarantee\w*|everyone|certainly|definitely|will)\b", text, re.I):
        messages.append("Overstatement check: replace certainty or universal claims with wording limited to this sample and its conditions.")
    if re.search(r"\b(significant|significance)\b", text, re.I):
        messages.append("Statistical claim check: Version 1 does not test statistical significance. Describe the observed size of the difference instead.")
    if not re.search(r"\d", text):
        messages.append("Evidence check: cite a relevant number, unit, group, and source table so a reader can trace your claim.")
    if not re.search(r"\b(sample|dataset|records?|period|month|year|week|survey|respondents?|rows?)\b", text, re.I):
        messages.append("Context check: identify the population or sample and the time period. State what one row represents.")
    if not has_evidence:
        messages.append("Support check: add an evidence table in Explore or Visualize before assessing your conclusion.")
    if not question.strip() or not decision.strip():
        messages.append("Business relevance check: enter both the business question and the decision it supports.")
    messages.append("Scope check: consider missing values, duplicate records, selection bias, group sizes, and other explanations. A matching number alone does not validate a recommendation or a causal claim.")
    return messages


def evidence_cells(table):
    """Expose numeric evidence with its row labels for an explicit claim check."""
    choices = {}
    for idx, row in table.head(500).iterrows():
        labels = ", ".join(f"{col}={row[col]}" for col in table if col not in numeric_columns(table))
        for col in numeric_columns(table):
            value = row[col]
            if pd.notna(value) and np.isfinite(value):
                choices[f"Row {idx} | {labels} | {col}"] = float(value)
    return choices


def check_claim(actual, claimed):
    # Match to two decimal places, matching classroom reporting convention.
    return abs(actual - claimed) <= 0.005000001


def build_report(question, decision, category, source, sections, evidence, ladder=None, challenges=None):
    parts = ["# MSIM Data-to-Decision Lab — Decision brief", f"Business question: {question}",
             f"Decision: {decision}", f"Question type: {category}", f"Data source: {source}"]
    for title in ["Evidence", "Interpretation", "Recommendation", "Limitations"]:
        parts.append(f"## {title}\n\n{sections.get(title, '').strip() or '(Not yet completed)'}")
        if title == "Evidence":
            for item in evidence:
                csv_text = item['table'].to_csv(index=False, lineterminator="\n").strip()
                parts.append(f"### {item['title']}\n\n{item['context']}\n\n```csv\n{csv_text}\n```")
        if title == "Interpretation" and ladder is not None:
            parts.append("### Insight Ladder")
            for name in ["Observation", "Analysis", "Insight", "Action"]:
                parts.append(f"**{name}:** {ladder.get(name, '').strip() or '(Not yet completed)'}")
        if title == "Limitations" and challenges is not None:
            parts.append("### Challenge Your Conclusion")
            for prompt, answer in challenges.items():
                parts.append(f"**{prompt}**\n\n{answer.strip() or '(Not yet completed)'}")
    return "\n\n".join(parts) + "\n"
