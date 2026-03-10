# app_oncology_dashboard_horizontal.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Interactive Dashboard", layout="wide")
st.title("Oncology Metrics Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])
if uploaded_file:
    # Load file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # Fixed columns
    cancer_col = "Cancer Category"
    month_col = "Month"
    metric_cols = [
        "1st visit - WIC acceptance",
        "WIC acceptance - 1st OPD visit",
        "1st OPD visit - MDT",
        "MDT - 1st day of treatment",
        "Number of days"
    ]

    # Ensure numeric metrics
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Compute metrics
    metrics_dict = {
        "Mean": lambda x: np.mean(x),
        "Median": lambda x: np.median(x),
        "SD": lambda x: np.std(x, ddof=0),
        "Max": lambda x: np.max(x),
        "Min": lambda x: np.min(x)
    }

    rows = []
    for param in metric_cols:
        for metric_name, func in metrics_dict.items():
            grouped = df.groupby([cancer_col, month_col])[param].apply(func).reset_index(name="Value")
            grouped["Parameter"] = param
            grouped["Metric"] = metric_name
            rows.append(grouped)

    final_df = pd.concat(rows, ignore_index=True)

    # Layout: Graph Left 3/4, Controls Right 1/4
    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Filters / Metric")
        metric_filter = st.selectbox("Select Metric", final_df["Metric"].unique(), index=0)
        month_filter = st.multiselect("Select Month(s)", final_df[month_col].unique(), default=final_df[month_col].unique())

    df_filtered = final_df[
        (final_df["Metric"] == metric_filter) &
        (final_df[month_col].isin(month_filter))
    ]

    with col1:
        st.subheader(f"Horizontal Bar Graph: {metric_filter} by Cancer Category")
        fig = px.bar(
            df_filtered,
            y=cancer_col,         # category on Y axis
            x="Value",            # metric on X axis
            color="Parameter",
            orientation='h',      # horizontal bars
            barmode="group",
            text="Value",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Plotly,
            title=f"{metric_filter} of Parameters by Cancer Category"
        )

        fig.update_layout(
            xaxis_title=metric_filter,
            yaxis_title="Cancer Category",
            width=1200,
            height=600
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')

        st.plotly_chart(fig, use_container_width=True)

        # HTML Export
        buffer = io.BytesIO()
        fig.write_html(buffer, include_plotlyjs='cdn', full_html=True)

        st.download_button(
            label="Download Interactive HTML",
            data=buffer.getvalue(),
            file_name=f"Oncology_Dashboard_{metric_filter}.html",
            mime="text/html"
        )
