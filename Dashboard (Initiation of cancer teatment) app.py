# oncology_dashboard_precomputed.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

# -------------------------
# 1️⃣ Page Config
# -------------------------
st.set_page_config(page_title="Oncology Dashboard", layout="wide")
st.title("Oncology Dashboard (Precomputed Metrics)")

# -------------------------
# 2️⃣ Upload Excel
# -------------------------
uploaded_file = st.file_uploader("Upload Aggregated Excel File", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # Identify columns
    cancer_col = "Cancer Category"
    month_col = "Month"
    
    # All metric columns (exclude cancer and month)
    metric_cols = [col for col in df.columns if col not in [cancer_col, month_col]]

    # -------------------------
    # 3️⃣ Select Metric
    # -------------------------
    metric_filter = st.radio(
        "Select Metric to Display",
        options=metric_cols,
        horizontal=True
    )

    # -------------------------
    # 4️⃣ Cancer Category Buttons
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
        # 5️⃣ View Mode
        # -------------------------
        view_mode = st.radio("View Mode", options=["Graph", "Table"], horizontal=True)

        # Filtered Data
        df_filtered = df[df[cancer_col].isin(selected_cancer)]

        # -------------------------
        # 6️⃣ Graph
        # -------------------------
        if view_mode == "Graph":
            st.subheader(f"{metric_filter} by Cancer Category")
            fig = px.bar(
                df_filtered,
                x=cancer_col,
                y=metric_filter,
                color=cancer_col,
                text=metric_filter,
                template="plotly_white"
            )
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # -------------------------
            # Download HTML
            # -------------------------
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs="cdn", full_html=True)
            st.download_button(
                label="Download Interactive HTML",
                data=buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.html",
                mime="text/html"
            )

        # -------------------------
        # 7️⃣ Table
        # -------------------------
        else:
            st.subheader(f"Data Table for {metric_filter}")
            st.dataframe(
                df_filtered[[cancer_col, month_col, metric_filter]].sort_values(by=cancer_col),
                height=500
            )
            # CSV download
            csv_buffer = io.StringIO()
            df_filtered[[cancer_col, month_col, metric_filter]].to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_{metric_filter}.csv",
                mime="text/csv"
            )
