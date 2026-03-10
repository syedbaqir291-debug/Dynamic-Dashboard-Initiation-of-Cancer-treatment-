# oncology_dashboard_multi_sheet.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard SKMCH & RC )")

# -------------------------
# 1️⃣ Upload Excel
# -------------------------
uploaded_file = st.file_uploader("Upload Excel Workbook with Precomputed Metrics", type=["xlsx"])

if uploaded_file:
    # Load all sheets
    xl = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names  # ["Mean", "Median", "Standard Deviation", "Maximum", "Minimum"]

    st.success(f"Workbook loaded with sheets: {sheet_names}")

    # -------------------------
    # 2️⃣ Metric selection (Sheet name)
    # -------------------------
    metric_filter = st.radio("Select Metric", options=sheet_names, horizontal=True)

    # Read the selected sheet
    df = pd.read_excel(uploaded_file, sheet_name=metric_filter)

    # Assume:
    # Column 0 = Cancer Category
    # Columns 1-5 = Parameters
    cancer_col = df.columns[0]
    parameter_cols = list(df.columns[1:])

    # -------------------------
    # 3️⃣ Cancer Category Buttons
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
        # 4️⃣ View Mode
        # -------------------------
        view_mode = st.radio("View Mode", options=["Graph", "Table"], horizontal=True)

        # Filtered Data
        df_filtered = df[df[cancer_col].isin(selected_cancer)]

        # -------------------------
        # 5️⃣ Graph
        # -------------------------
        if view_mode == "Graph":
            st.subheader(f"{metric_filter} by Cancer Category")
            # Melt parameters to long format
            df_long = df_filtered.melt(id_vars=[cancer_col], value_vars=parameter_cols,
                                       var_name="Parameter", value_name="Value")

            fig = px.bar(
                df_long,
                y=cancer_col,
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

        # -------------------------
        # 6️⃣ Table
        # -------------------------
        else:
            st.subheader(f"Data Table for {metric_filter}")
            st.dataframe(df_filtered, height=500)

            # CSV download
            csv_buffer = io.StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.csv",
                mime="text/csv"
            )
