"""
Streamlit UI for sentiment analysis on uploaded CSV files.
Upload a CSV, choose text column, run analysis, view summary and examples, download result.
"""

import streamlit as st
import pandas as pd

from csv_utils import (
    read_uploaded_csv,
    detect_text_column,
    run_sentiment_on_df,
    to_csv_bytes,
)


st.set_page_config(page_title="Sentiment Analysis", layout="wide")
st.title("Customer review sentiment analysis")
st.markdown("Upload a CSV with a text column (e.g. reviews). We assign **positive**, **neutral**, or **negative** and optional confidence.")

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if not uploaded:
    st.info("Upload a CSV file to start.")
    st.stop()

df = read_uploaded_csv(uploaded)
detected = detect_text_column(df)
text_col = st.selectbox(
    "Column containing review text",
    options=df.columns.tolist(),
    index=df.columns.tolist().index(detected) if detected and detected in df.columns else 0,
)

if st.button("Run sentiment analysis"):
    with st.spinner("Running sentiment analysis…"):
        result = run_sentiment_on_df(df, text_col)
    st.session_state["result_df"] = result
    st.session_state["text_col"] = text_col

if "result_df" not in st.session_state:
    st.stop()

result = st.session_state["result_df"]
text_col = st.session_state["text_col"]

st.subheader("Summary")
counts = result["sentiment"].value_counts()
cols = st.columns(3)
for i, (label, count) in enumerate(counts.items()):
    cols[i].metric(label.capitalize(), int(count))
st.bar_chart(counts)

st.subheader("Example positive reviews")
pos = result[result["sentiment"] == "positive"].head(5)
if pos.empty:
    st.caption("No positive examples.")
else:
    for _, row in pos.iterrows():
        st.caption(f"Confidence: {row['sentiment_confidence']}")
        st.write(row[text_col][:300] + ("…" if len(str(row[text_col])) > 300 else ""))

st.subheader("Example negative reviews")
neg = result[result["sentiment"] == "negative"].head(5)
if neg.empty:
    st.caption("No negative examples.")
else:
    for _, row in neg.iterrows():
        st.caption(f"Confidence: {row['sentiment_confidence']}")
        st.write(row[text_col][:300] + ("…" if len(str(row[text_col])) > 300 else ""))

st.subheader("Download")
st.download_button(
    label="Download processed CSV",
    data=to_csv_bytes(result),
    file_name="reviews_with_sentiment.csv",
    mime="text/csv",
)
