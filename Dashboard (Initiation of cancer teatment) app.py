# app_oncology_dashboard_auto.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Interactive Dashboard", layout="wide")
st.title("Oncology Metrics Dashboard")
st.markdown("Upload your Excel file. Dashboard will generate automatically using predefined columns.")

# -------------------------
# 1️⃣ Upload File
# -------------------------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")
    st.dataframe(df.head())

    # -------------------------
    # 2️⃣ Fixed Columns
    # -------------------------
    cancer_col = "Cancer Category"
    month_col = "Month"
    metric_cols = [
        "1st visit - WIC acceptance",
        "WIC acceptance - 1st OPD visit",
        "1st OPD visit - MDT",
        "MDT - 1st day of treatment",
        "Number of days"
    ]

    # -------------------------
    # 3️⃣ Ensure metrics are numeric
    # -------------------------
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # -------------------------
    # 4️⃣ Compute Metrics
    # -------------------------
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

    # -------------------------
    # 5️⃣ Filters for End User
    # -------------------------
    st.subheader("Dashboard Controls")
    metric_filter = st.selectbox("Select Metric", final_df["Metric"].unique(), index=0)
    month_filter = st.multiselect("Select Month(s)", final_df[month_col].unique(), default=final_df[month_col].unique())

    df_filtered = final_df[
        (final_df["Metric"] == metric_filter) &
        (final_df[month_col].isin(month_filter))
    ]

    # -------------------------
    # 6️⃣ Plotly Grouped Bar Chart
    # -------------------------
    fig = px.bar(
        df_filtered,
        x=cancer_col,
        y="Value",
        color="Parameter",
        barmode="group",
        text="Value",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Plotly,
        title=f"{metric_filter} of Parameters by Cancer Category"
    )

    fig.update_layout(
        xaxis_title="Cancer Category",
        yaxis_title=metric_filter,
        width=1200,
        height=600
    )
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # 7️⃣ Export Interactive HTML
    # -------------------------
    st.subheader("Download Interactive HTML")
    buffer = io.BytesIO()
    fig.write_html(buffer, include_plotlyjs='cdn', full_html=True)

    st.download_button(
        label="Download HTML Dashboard",
        data=buffer.getvalue(),
        file_name=f"Oncology_Dashboard_{metric_filter}.html",
        mime="text/html"
    )
