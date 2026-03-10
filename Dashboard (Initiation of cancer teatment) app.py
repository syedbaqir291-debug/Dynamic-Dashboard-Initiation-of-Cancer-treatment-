# oncology_dashboard_multi_sheet_aggregated.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard by QPSD SKMCH & RC V.1")

# -------------------------
# 1️⃣ Upload Excel
# -------------------------
uploaded_file = st.file_uploader("Upload Excel Workbook with Precomputed Metrics", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # -------------------------
    # Columns
    # -------------------------
    month_col = df.columns[0]       # Month
    cancer_col = df.columns[1]      # Cancer Category
    parameter_cols = list(df.columns[2:])  # Parameters

    # Ensure numeric columns
    for col in parameter_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # -------------------------
    # Metric selection
    # -------------------------
    metric_dict = {
        "Mean": np.mean,
        "Median": np.median,
        "SD": lambda x: np.std(x, ddof=1),
        "Max": np.max,
        "Min": np.min
    }

    metric_filter = st.radio("Select Metric", options=list(metric_dict.keys()), horizontal=True)

    # -------------------------
    # Month multi-select
    # -------------------------
    month_filter = st.multiselect(
        "Select Month(s)",
        options=df[month_col].unique(),
        default=list(df[month_col].unique())
    )

    # -------------------------
    # Cancer Category Buttons
    # -------------------------
    if "selected_cancer" not in st.session_state:
        st.session_state.selected_cancer = []

    st.markdown("**Select Cancer Category(s)**")
    cancer_options = list(df[cancer_col].unique())
    num_per_row = 6
    for i in range(0, len(cancer_options), num_per_row):
        cols = st.columns(num_per_row)
        for j, cancer in enumerate(cancer_options[i:i + num_per_row]):
            if cols[j].button(cancer):
                if cancer in st.session_state.selected_cancer:
                    st.session_state.selected_cancer.remove(cancer)
                else:
                    st.session_state.selected_cancer.append(cancer)

    selected_cancer = st.session_state.selected_cancer

    if not selected_cancer:
        st.info("Click cancer category button(s) to generate graph or table.")
    else:
        # -------------------------
        # Filtered Data by Month and Cancer Category
        # -------------------------
        df_filtered = df[
            (df[month_col].isin(month_filter)) &
            (df[cancer_col].isin(selected_cancer))
        ]

        # -------------------------
        # Aggregate metric per Cancer Category
        # -------------------------
        rows = []
        for cancer in selected_cancer:
            temp = df_filtered[df_filtered[cancer_col] == cancer]
            row = {"Cancer Category": cancer}
            for param in parameter_cols:
                row[param] = metric_dict[metric_filter](temp[param].values)
            rows.append(row)

        df_metric = pd.DataFrame(rows)

        # -------------------------
        # View Mode
        # -------------------------
        view_mode = st.radio("View Mode", options=["Graph", "Table"], horizontal=True)

        if view_mode == "Graph":
            st.subheader(f"{metric_filter} by Cancer Category")
            df_long = df_metric.melt(id_vars=["Cancer Category"],
                                     value_vars=parameter_cols,
                                     var_name="Parameter",
                                     value_name="Value")

            fig = px.bar(
                df_long,
                y="Cancer Category",
                x="Value",
                color="Parameter",
                orientation="h",
                barmode="group",
                text="Value",
                template="plotly_white",
                title=f"{metric_filter} by Cancer Category"
            )
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # Download HTML
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs="cdn", full_html=True)
            st.download_button(
                label="Download Interactive HTML",
                data=buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.html",
                mime="text/html"
            )

        else:
            st.subheader(f"Data Table for {metric_filter}")
            st.dataframe(df_metric, height=500)

            # CSV download
            csv_buffer = io.StringIO()
            df_metric.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.csv",
                mime="text/csv"
            )
