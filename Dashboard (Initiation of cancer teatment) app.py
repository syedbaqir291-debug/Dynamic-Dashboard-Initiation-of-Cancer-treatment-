# app_oncology_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Oncology Metrics Dashboard", layout="wide")

st.title("Interactive Oncology Metrics Dashboard")
st.markdown("Upload your Excel file and select the columns to generate a dynamic interactive chart.")

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
    # 2️⃣ Map Columns
    # -------------------------
    st.subheader("Map Columns")
    cancer_col = st.selectbox("Select Cancer Category column", df.columns)
    month_col = st.selectbox("Select Month column", df.columns)
    
    metric_cols = st.multiselect(
        "Select Metrics Columns",
        df.columns,
        default=[
            '1st visit - WIC acceptance',
            'WIC acceptance - 1st OPD visit',
            '1st OPD visit - MDT',
            'MDT - 1st day of treatment',
            'Number of days'
        ]
    )
    
    if len(metric_cols) == 0:
        st.warning("Please select at least one metric column.")
    
    else:
        # -------------------------
        # 3️⃣ Metric Selector
        # -------------------------
        st.subheader("Select Metric to Display")
        metric_option = st.radio("Metric", ["Mean", "Median", "SD", "Max", "Min"], horizontal=True)
        
        # -------------------------
        # 4️⃣ Filter Slicers
        # -------------------------
        st.subheader("Apply Filters")
        months_selected = st.multiselect("Select Month(s)", df[month_col].unique(), default=df[month_col].unique())
        cancers_selected = st.multiselect("Select Cancer Category(s)", df[cancer_col].unique(), default=df[cancer_col].unique())
        
        df_filtered = df[df[month_col].isin(months_selected) & df[cancer_col].isin(cancers_selected)]
        
        # -------------------------
        # 5️⃣ Compute Metrics
        # -------------------------
        def calc_metric(series, metric):
            if metric == "Mean":
                return np.mean(series)
            elif metric == "Median":
                return np.median(series)
            elif metric == "SD":
                return np.std(series, ddof=0)
            elif metric == "Max":
                return np.max(series)
            elif metric == "Min":
                return np.min(series)
        
        grouped = df_filtered.groupby(cancer_col)[metric_cols].agg(
            lambda x: calc_metric(x, metric_option)
        ).reset_index()
        
        # -------------------------
        # 6️⃣ Plotly Bar Chart
        # -------------------------
        fig = go.Figure()
        for col in metric_cols:
            fig.add_trace(go.Bar(
                x=grouped[cancer_col],
                y=grouped[col],
                name=col,
                text=np.round(grouped[col], 2),
                textposition='auto'
            ))
        
        fig.update_layout(
            barmode='group',
            xaxis_title="Cancer Category",
            yaxis_title=metric_option,
            template='plotly_white',
            colorway=px.colors.qualitative.Plotly,
            width=1200,
            height=600,
            title=f"{metric_option} of Parameters by Cancer Category"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # -------------------------
        # 7️⃣ Export Interactive HTML
        # -------------------------
        st.subheader("Download Interactive Graph")
        buffer = io.BytesIO()
        fig.write_html(buffer, include_plotlyjs='cdn', full_html=True)
        
        st.download_button(
            label="Download Interactive HTML",
            data=buffer.getvalue(),
            file_name=f"Oncology_Dashboard_{metric_option}.html",
            mime="text/html"
        )
