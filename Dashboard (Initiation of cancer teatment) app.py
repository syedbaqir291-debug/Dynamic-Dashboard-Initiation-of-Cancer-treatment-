# app_oncology_precompute.py

import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Oncology Precompute Metrics", layout="wide")
st.title("Oncology Metrics Precompute (Multi-Sheet)")

# 1️⃣ Upload raw data
uploaded_file = st.file_uploader("Upload Raw Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File loaded successfully!")
    st.dataframe(df.head(5))

    # 2️⃣ Select columns
    month_col = st.selectbox("Select Month Column", df.columns)
    cancer_col = st.selectbox("Select Cancer Category Column", df.columns)
    parameter_cols = st.multiselect(
        "Select up to 5 Parameters",
        df.columns,
        default=df.columns[:5]
    )

    if len(parameter_cols) > 5:
        st.warning("Please select no more than 5 parameters.")
    elif len(parameter_cols) == 0:
        st.warning("Select at least one parameter.")
    else:
        st.success("Ready to generate precomputed metrics.")

        # 3️⃣ Compute aggregations
        agg_funcs = {
            "Mean": "mean",
            "Median": "median",
            "Maximum": "max",
            "Minimum": "min",
            "SD": "std"
        }

        # 4️⃣ Prepare Excel writer
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for stat_name, func in agg_funcs.items():
                grouped = df.groupby([month_col, cancer_col])[parameter_cols].agg(func).reset_index()
                grouped.to_excel(writer, sheet_name=stat_name, index=False)

        # 5️⃣ Download button
        st.download_button(
            label="Download Precomputed Excel",
            data=output.getvalue(),
            file_name="oncology_metrics_precomputed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("Precomputed Excel ready with 5 sheets (Mean, Median, Max, Min, SD)!")
