# app_oncology_dashboard_v5_fixed.py

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

    # -------------------------
    # 4️⃣ Robust Numeric Cleanup
    # -------------------------
    for col in metric_cols:
        df[col] = df[col].astype(str).str.strip()  # remove spaces
        df[col] = pd.to_numeric(df[col].replace(r'[^\d.]', '', regex=True), errors='coerce')  # numeric only

    # -------------------------
    # 5️⃣ Aggregate Metrics per Cancer + Month
    # -------------------------
    agg_dict = {col: [np.nanmean, np.nanmedian, lambda x: np.nanstd(x, ddof=1), np.nanmax, np.nanmin]
                for col in metric_cols}

    grouped_all = df.groupby([cancer_col, month_col]).agg(agg_dict)

    # Flatten MultiIndex columns
    grouped_all.columns = [
        f"{col[0]}_{col[1].__name__ if hasattr(col[1], '__name__') else 'SD'}"
        for col in grouped_all.columns
    ]
    grouped_all = grouped_all.reset_index()

    # -------------------------
    # 6️⃣ Reshape for Dashboard
    # -------------------------
    final_df = pd.melt(
        grouped_all,
        id_vars=[cancer_col, month_col],
        var_name="Parameter_Metric",
        value_name="Value"
    )

    # Split into Parameter + Metric
    final_df[['Parameter', 'Metric']] = final_df['Parameter_Metric'].str.rsplit('_', n=1, expand=True)
    final_df = final_df.drop(columns=['Parameter_Metric'])

    # Rename metrics to friendly names
    metric_name_map = {
        'nanmean': 'Mean',
        'nanmedian': 'Median',
        'SD': 'SD',
        'nanmax': 'Max',
        'nanmin': 'Min'
    }
    final_df['Metric'] = final_df['Metric'].map(metric_name_map)
    final_df['Value'] = final_df['Value'].round(2)

    # -------------------------
    # 7️⃣ Controls
    # -------------------------
    st.subheader("Controls")

    metric_filter = st.radio(
        "Select Metric",
        options=["Mean", "Median", "SD", "Max", "Min"],
        horizontal=True
    )

    month_filter = st.multiselect(
        "Select Month(s)",
        options=final_df[month_col].unique(),
        default=final_df[month_col].unique()
    )

    if "selected_cancer" not in st.session_state:
        st.session_state.selected_cancer = []

    st.markdown("**Select Cancer Category(s)** (click to toggle)")
    cancer_options = list(final_df[cancer_col].unique())
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
        st.info("Click on Cancer Category button(s) to generate graph or table.")
    else:
        view_mode = st.radio(
            "View Mode",
            options=["Graph", "Table"],
            horizontal=True
        )

        # Filter data for selected metric, months, and cancer categories
        df_filtered = final_df[
            (final_df["Metric"] == metric_filter) &
            (final_df[month_col].isin(month_filter)) &
            (final_df[cancer_col].isin(selected_cancer))
        ]

        # -------------------------
        # 8️⃣ Graph or Table
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

            # Download HTML
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
            csv_buffer = io.StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Table CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Oncology_Dashboard_{metric_filter}.csv",
                mime="text/csv"
            )
