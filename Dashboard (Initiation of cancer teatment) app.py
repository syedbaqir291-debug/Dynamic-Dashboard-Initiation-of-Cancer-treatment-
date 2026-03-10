# app_oncology_dashboard_full.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

# -------------------------
# 1️⃣ Page Config
# -------------------------
st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Interactive Dashboard")

# -------------------------
# 2️⃣ File Upload
# -------------------------
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # -------------------------
    # 3️⃣ Fixed Columns
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

    # Ensure numeric columns
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
    # 5️⃣ Controls: Metric Buttons + Month Multi-select + View Toggle
    # -------------------------
    st.subheader("Controls")
    col1, col2, col3 = st.columns([4, 4, 2])

    with col1:
        metric_filter = st.radio("Select Metric", options=final_df["Metric"].unique(), horizontal=True)

    with col2:
        month_filter = st.multiselect("Select Month(s)", options=final_df[month_col].unique(), default=final_df[month_col].unique())

    with col3:
        view_mode = st.radio("View Mode", options=["Graph", "Table"], horizontal=True)

    # -------------------------
    # 6️⃣ Filtered Data
    # -------------------------
    df_filtered = final_df[
        (final_df["Metric"] == metric_filter) &
        (final_df[month_col].isin(month_filter))
    ]

    # -------------------------
    # 7️⃣ Graph or Table
    # -------------------------
    if view_mode == "Graph":
        st.subheader(f"{metric_filter} of Parameters by Cancer Category")
        fig = px.bar(
            df_filtered,
            y=cancer_col,
            x="Value",
            color="Parameter",
            orientation='h',
            barmode="group",
            text="Value",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Plotly,
            title=f"{metric_filter} by Cancer Category"
        )
        fig.update_layout(
            xaxis_title=metric_filter,
            yaxis_title="Cancer Category",
            height=600,
            margin=dict(l=50, r=50, t=80, b=50)
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

    else:  # Table view
        st.subheader(f"Data Table: {metric_filter}")
        st.dataframe(df_filtered[[cancer_col, month_col, "Parameter", "Value"]].sort_values(by=cancer_col))
        # Optional CSV download
        csv_buffer = io.StringIO()
        df_filtered.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Table CSV",
            data=csv_buffer.getvalue(),
            file_name=f"Oncology_Dashboard_{metric_filter}.csv",
            mime="text/csv"
        )
