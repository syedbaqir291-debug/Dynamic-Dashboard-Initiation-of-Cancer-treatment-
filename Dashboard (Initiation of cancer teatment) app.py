# oncology_dashboard_raw_metrics.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard")

# Upload raw Excel
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Columns
    month_col = "Month"
    cancer_col = "Cancer Category"
    parameter_cols = [
        "1st visit - WIC acceptance",
        "WIC acceptance - 1st OPD visit",
        "1st OPD visit - MDT",
        "MDT - 1st day of treatment",
        "Number of days"
    ]

    # Ensure numeric for parameters
    for col in parameter_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Metric selector
    metric = st.radio(
        "Select Metric",
        ["Mean", "Median", "SD", "Maximum", "Minimum"],
        horizontal=True
    )

    # Month filter
    months = st.multiselect(
        "Select Month",
        options=df[month_col].unique(),
        default=df[month_col].unique()
    )

    # Cancer category buttons
    if "selected_cancer" not in st.session_state:
        st.session_state.selected_cancer = []

    cancers = df[cancer_col].unique()
    st.markdown("### Select Cancer Category")
    cols = st.columns(5)

    for i, cancer in enumerate(cancers):
        if cols[i % 5].button(cancer):
            if cancer in st.session_state.selected_cancer:
                st.session_state.selected_cancer.remove(cancer)
            else:
                st.session_state.selected_cancer.append(cancer)

    selected_cancer = st.session_state.selected_cancer

    if selected_cancer:

        # Filter by month and selected cancers
        filtered = df[
            (df[month_col].isin(months)) &
            (df[cancer_col].isin(selected_cancer))
        ]

        results = []

        for cancer in selected_cancer:
            temp = filtered[filtered[cancer_col] == cancer]
            row = {"Cancer Category": cancer}

            for param in parameter_cols:
                data = temp[param].dropna()  # Use all raw data

                # Compute metrics faithfully
                if metric == "Mean":
                    value = data.mean() if not data.empty else 0
                elif metric == "Median":
                    value = data.median() if not data.empty else 0
                elif metric == "SD":
                    value = data.std() if len(data) > 1 else 0
                elif metric == "Maximum":
                    value = data.max() if not data.empty else 0
                elif metric == "Minimum":
                    value = data.min() if not data.empty else 0

                row[param] = value

            results.append(row)

        result_df = pd.DataFrame(results)

        # View selector
        view = st.radio("View", ["Graph", "Table"], horizontal=True)

        if view == "Graph":
            # Reshape for Plotly
            long_df = result_df.melt(
                id_vars="Cancer Category",
                var_name="Parameter",
                value_name="Value"
            )

            fig = px.bar(
                long_df,
                y="Cancer Category",
                x="Value",
                color="Parameter",
                orientation="h",
                text="Value",
                barmode="group",
                title=f"{metric} by Cancer Category (Raw Data)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Download interactive HTML
            buffer = io.StringIO()
            fig.write_html(buffer)
            st.download_button(
                "Download Interactive HTML",
                buffer.getvalue(),
                file_name="oncology_dashboard.html",
                mime="text/html"
            )

        else:
            st.dataframe(result_df)
