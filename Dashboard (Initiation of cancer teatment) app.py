# oncology_dashboard_multi_sheet.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard (Multi-Sheet Precomputed Metrics)")

# -------------------------
# 1 Upload Excel
# -------------------------
uploaded_file = st.file_uploader(
    "Upload Excel Workbook with Precomputed Metrics",
    type=["xlsx"]
)

if uploaded_file:

    # Load all sheets
    all_sheets = pd.read_excel(uploaded_file, sheet_name=None)

    sheet_names = list(all_sheets.keys())

    st.success(f"Workbook loaded with sheets: {sheet_names}")

    # -------------------------
    # 2 Parameter Selection
    # -------------------------
    sample_df = list(all_sheets.values())[0]

    month_col = sample_df.columns[0]
    cancer_col = sample_df.columns[1]
    parameter_cols = list(sample_df.columns[2:])

    parameter_selected = st.selectbox(
        "Select Parameter",
        parameter_cols
    )

    # -------------------------
    # 3 Metric Selection
    # -------------------------
    metric_filter = st.radio(
        "Select Metric (Sheet)",
        options=sheet_names,
        horizontal=True
    )

    df = all_sheets[metric_filter].copy()

    # -------------------------
    # 4 Month Selection
    # -------------------------
    months = df[month_col].unique()

    selected_months = st.multiselect(
        "Select Month",
        months,
        default=months
    )

    df = df[df[month_col].isin(selected_months)]

    # -------------------------
    # 5 Cancer Category Buttons
    # -------------------------
    if "selected_cancer" not in st.session_state:
        st.session_state.selected_cancer = []

    st.markdown("### Select Cancer Category")

    cancer_options = df[cancer_col].unique()

    num_per_row = 5

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

        st.info("Select cancer category to continue")

    else:

        df_filtered = df[df[cancer_col].isin(selected_cancer)]

        # -------------------------
        # 6 View Mode
        # -------------------------
        view_mode = st.radio(
            "View",
            ["Graph", "Table"],
            horizontal=True
        )

        if view_mode == "Graph":

            st.subheader(
                f"{metric_filter} : {parameter_selected}"
            )

            plot_df = df_filtered[
                [cancer_col, parameter_selected]
            ]

            fig = px.bar(
                plot_df,
                y=cancer_col,
                x=parameter_selected,
                orientation="h",
                text=parameter_selected,
                template="plotly_white"
            )

            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # Download HTML
            buffer = io.StringIO()

            fig.write_html(
                buffer,
                include_plotlyjs="cdn",
                full_html=True
            )

            st.download_button(
                "Download Interactive HTML",
                buffer.getvalue(),
                file_name=f"{metric_filter}_{parameter_selected}.html",
                mime="text/html"
            )

        else:

            st.subheader("Data Table")

            st.dataframe(df_filtered)

            csv_buffer = io.StringIO()

            df_filtered.to_csv(
                csv_buffer,
                index=False
            )

            st.download_button(
                "Download CSV",
                csv_buffer.getvalue(),
                file_name="oncology_data.csv",
                mime="text/csv"
            )
