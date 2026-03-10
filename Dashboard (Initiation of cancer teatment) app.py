# app_oncology_dashboard_final_v3.py

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

    # Ensure numeric columns and NaNs
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # -------------------------
    # 4️⃣ Compute Metrics (Excel-compatible)
    # -------------------------
    metrics_dict = {
        "Mean": lambda x: np.nanmean(x),       # Excel AVERAGE
        "Median": lambda x: np.nanmedian(x),   # Excel MEDIAN
        "SD": lambda x: np.nanstd(x, ddof=1),  # Excel STDEV.S (sample SD)
        "Max": lambda x: np.nanmax(x),
        "Min": lambda x: np.nanmin(x)
    }

    rows = []
    for param in metric_cols:
        for metric_name, func in metrics_dict.items():
            grouped = df.groupby([cancer_col, month_col])[param].apply(func).reset_index(name="Value")
            grouped["Value"] = grouped["Value"].round(2)  # Round like Excel
            grouped["Parameter"] = param
            grouped["Metric"] = metric_name
            rows.append(grouped)

    final_df = pd.concat(rows, ignore_index=True)

    # -------------------------
    # 5️⃣ Controls
    # -------------------------
    st.subheader("Controls")

    # Metric Buttons
    metric_filter = st.radio(
        "Select Metric",
        options=final_df["Metric"].unique(),
        horizontal=True
    )

    # Month Multi-select
    month_filter = st.multiselect(
        "Select Month(s)",
        options=final_df[month_col].unique(),
        default=final_df[month_col].unique()
    )

    # Initialize session state for selected cancer categories
    if "selected_cancer" not in st.session_state:
        st.session_state.selected_cancer = []

    # Cancer Category Buttons (compact 2 rows)
    st.markdown("**Select Cancer Category(s)** (click to toggle)")
    cancer_options = list(final_df[cancer_col].unique())
    num_per_row = 6
    for i in range(0, len(cancer_options), num_per_row):
        cols = st.columns(num_per_row)
        for j, cancer in enumerate(cancer_options[i:i+num_per_row]):
            if cols[j].button(cancer):
                if cancer in st.session_state.selected_cancer:
                    st.session_state.selected_cancer.remove(cancer)
                else:
                    st.session_state.selected_cancer.append(cancer)

    selected_cancer = st.session_state.selected_cancer

    if not selected_cancer:
        st.info("Click on Cancer Category button(s) to generate graph or table.")
    else:
        # View Toggle
        view_mode = st.radio(
            "View Mode",
            options=["Graph", "Table"],
            horizontal=True
        )

        # -------------------------
        # 6️⃣ Filtered Data
        # -------------------------
        df_filtered = final_df[
            (final_df["Metric"] == metric_filter) &
            (final_df[month_col].isin(month_filter)) &
            (final_df[cancer_col].isin(selected_cancer))
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
                xaxis=dict(title_font=dict(size=12), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=12), tickfont=dict(size=12)),
                legend=dict(font=dict(size=12)),
                height=600,
                margin=dict(l=50, r=50, t=80, b=50)
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

            # HTML Export
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs='cdn', full_html=True)
            st.download_button(
                label="Download Interactive HTML",
                data=buffer.getvalue(),
                file_name=f"Oncology_Dashboard_{metric_filter}.html",
                mime="text/html"
            )

        else:
            st.subheader(f"Data Table: {metric_filter}")
            st.dataframe(
                df_filtered[[cancer_col, month_col, "Parameter", "Value"]].sort_values(by=cancer_col),
                height=500
            )
            # CSV download
            csv_buffer = io.StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Table CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_Dashboard_{metric_filter}.csv",
                mime="text/csv"
            )
