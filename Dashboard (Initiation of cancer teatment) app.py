# app_oncology_dashboard_dynamic.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Oncology Interactive Dashboard", layout="wide")
st.title("Oncology Metrics Dashboard")
st.markdown("Upload your Excel file and map the relevant columns. The dashboard will generate a fully interactive chart.")

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
    # 2️⃣ Column Mapping
    # -------------------------
    st.subheader("Map Columns")
    cancer_col = st.selectbox("Select Cancer Category column", df.columns)
    month_col = st.selectbox("Select Month column", df.columns)
    
    metric_cols = st.multiselect(
        "Select Metric Columns",
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
        st.success("Column mapping complete. Generating interactive dashboard...")

        # -------------------------
        # 3️⃣ Prepare Metrics Table
        # -------------------------
        metrics = ["Mean", "Median", "SD", "Max", "Min"]
        rows = []

        for param in metric_cols:
            for metric in metrics:
                grouped = df.groupby([cancer_col, month_col])[param].agg(
                    Mean=np.mean,
                    Median=np.median,
                    SD=lambda x: np.std(x, ddof=0),
                    Max=np.max,
                    Min=np.min
                ).reset_index()

                grouped = grouped[[cancer_col, month_col, metric]].rename(columns={metric: "Value"})
                grouped["Parameter"] = param
                grouped["Metric"] = metric
                rows.append(grouped)

        final_df = pd.concat(rows, ignore_index=True)

        st.subheader("Preview of Computed Metrics")
        st.dataframe(final_df.head(10))

        # -------------------------
        # 4️⃣ Plotly Interactive Chart
        # -------------------------
        st.subheader("Interactive Dashboard Preview")

        # Default selections
        default_metric = "Mean"
        default_months = final_df[month_col].unique().tolist()
        default_cancer = final_df[cancer_col].unique().tolist()

        # Dropdowns / filters for end user
        metric_filter = st.selectbox("Select Metric", final_df["Metric"].unique(), index=0)
        month_filter = st.multiselect("Select Month(s)", final_df[month_col].unique(), default=default_months)
        cancer_filter = st.multiselect("Select Cancer Category(s)", final_df[cancer_col].unique(), default=default_cancer)

        df_filtered = final_df[
            (final_df["Metric"] == metric_filter) &
            (final_df[month_col].isin(month_filter)) &
            (final_df[cancer_col].isin(cancer_filter))
        ]

        # Plot grouped bar chart
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
        # 5️⃣ Export Interactive HTML
        # -------------------------
        st.subheader("Download Interactive Dashboard (HTML)")

        buffer = io.BytesIO()
        fig.write_html(buffer, include_plotlyjs='cdn', full_html=True)

        st.download_button(
            label="Download Interactive HTML",
            data=buffer.getvalue(),
            file_name=f"Oncology_Dashboard_{metric_filter}.html",
            mime="text/html"
        )
