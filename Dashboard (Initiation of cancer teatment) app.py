# oncology_dashboard_correct_logic.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard by QPSD SKMCH & RC")

# Upload file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Columns
    month_col = df.columns[0]
    cancer_col = df.columns[1]
    parameter_cols = list(df.columns[2:])

    # Ensure numeric
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

        # Apply filters
        filtered = df[
            (df[month_col].isin(months)) &
            (df[cancer_col].isin(selected_cancer))
        ]

        results = []

        for cancer in selected_cancer:

            temp = filtered[filtered[cancer_col] == cancer]

            row = {"Cancer Category": cancer}

            for param in parameter_cols:

                column_data = temp[param].dropna()

                if metric == "Maximum":
                    value = column_data.max()

                elif metric == "Minimum":
                    value = column_data.min()

                elif metric == "Mean":
                    value = column_data.mean()

                elif metric == "Median":
                    value = column_data.median()

                elif metric == "SD":
                    value = column_data.std()

                row[param] = value

            results.append(row)

        result_df = pd.DataFrame(results)

        view = st.radio("View", ["Graph", "Table"], horizontal=True)

        if view == "Graph":

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
                barmode="group"
            )

            st.plotly_chart(fig, use_container_width=True)

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
