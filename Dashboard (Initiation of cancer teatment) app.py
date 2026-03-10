# oncology_dashboard_dynamic.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard (Dynamic Metrics)")

# -------------------------
# 1️⃣ Upload raw Excel
# -------------------------
uploaded_file = st.file_uploader("Upload Excel Workbook", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # -------------------------
    # Columns
    # -------------------------
    month_col = df.columns[0]
    cancer_col = df.columns[1]
    parameter_cols = list(df.columns[2:])

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
        # Filtered Data
        # -------------------------
        df_filtered = df[
            (df[month_col].isin(month_filter)) &
            (df[cancer_col].isin(selected_cancer))
        ]

        # -------------------------
        # Compute metric
        # -------------------------
        rows = []
        for param in parameter_cols:
            value = metric_dict[metric_filter](df_filtered[param].values)
            rows.append({
                "Parameter": param,
                "Value": value
            })

        metric_df = pd.DataFrame(rows)

        # -------------------------
        # View Mode
        # -------------------------
        view_mode = st.radio("View Mode", options=["Graph", "Table"], horizontal=True)

        if view_mode == "Graph":
            st.subheader(f"{metric_filter} by Parameter")
            fig = px.bar(
                metric_df,
                x="Value",
                y="Parameter",
                orientation="h",
                text="Value",
                template="plotly_white",
                color="Parameter",
                title=f"{metric_filter} by Parameter"
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
            st.dataframe(metric_df, height=500)
            # CSV download
            csv_buffer = io.StringIO()
            metric_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.csv",
                mime="text/csv"
            )
