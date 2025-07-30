import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from esma_data_py import EsmaDataLoader

st.set_page_config(page_title="ESMA Regulatory Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer – Stable Edition")

edl = EsmaDataLoader()

# Utility: safe datetime conversion
def safe_datetime(series):
    return pd.to_datetime(series, errors="coerce").dt.tz_localize(None)

# Utility: schema viewer
def show_schema(df, label):
    with st.expander(f"📄 Schema: {label}"):
        st.dataframe(pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str)
        }))

# Dataset selector
dataset = st.sidebar.radio("Select dataset", ["MiFID", "FIRDS", "SSR"])

# ------------------- MiFID -------------------
if dataset == "MiFID":
    st.header("🧾 MiFID II")
    try:
        files = edl.load_mifid_file_list()
        if files.empty:
            st.warning("No MiFID metadata found.")
        else:
            files["publication_date"] = safe_datetime(files["publication_date"])
            show_schema(files, "MiFID File Metadata")

            # Date filtering
            min_date = files["publication_date"].min()
            max_date = files["publication_date"].max()
            start_date, end_date = st.date_input("📅 Filter by publication date range",
                                                 [min_date, max_date])
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            filtered = files[
                (files["publication_date"] >= start_date) &
                (files["publication_date"] <= end_date)
            ]

            st.subheader(f"{len(filtered)} files found")
            st.dataframe(filtered)

            selected_files = st.multiselect("Select files to download and analyze", filtered["file_name"])
            if st.button("📥 Download & Analyze Selected"):
                combined = pd.DataFrame()
                for fname in selected_files:
                    row = filtered[filtered["file_name"] == fname].iloc[0]
                    url = row.get("download_link") or row.get("downloadUrl")
                    if not url:
                        st.warning(f"No download URL for {fname}")
                        continue
                    df = edl.download_file(url)
                    df["source_file"] = fname
                    combined = pd.concat([combined, df], ignore_index=True)

                if not combined.empty:
                    st.subheader("🔍 Combined Preview")
                    search = st.text_input("Search within combined data")
                    if search:
                        combined = combined[combined.astype(str).apply(
                            lambda r: r.str.contains(search, case=False, na=False), axis=1
                        )]
                    st.dataframe(combined.head(100))
                    st.download_button("⬇ Download Combined CSV", combined.to_csv(index=False), "mifid_combined.csv")
                    show_schema(combined, "Combined MiFID Data")
    except Exception as e:
        st.error(f"MiFID error: {e}")

# ------------------- FIRDS -------------------
elif dataset == "FIRDS":
    st.header("📂 FIRDS Instrument Reference Data")
    try:
        files = edl.load_latest_files()
        if files.empty:
            st.warning("No FIRDS metadata available.")
        else:
            show_schema(files, "FIRDS Metadata")

            isin = st.text_input("Filter by ISIN (optional)").strip().upper()
            cfi = st.text_input("Filter by CFI Code (optional)").strip().upper()

            if isin:
                files = files[files["isin"].astype(str).str.contains(isin, na=False)]
            if cfi:
                files = files[files["cfi_code"].astype(str).str.contains(cfi, na=False)]

            st.subheader(f"{len(files)} records found")
            st.dataframe(files.head(100))
            st.download_button("⬇ Download FIRDS CSV", files.to_csv(index=False), "firds_filtered.csv")

            if not files.empty:
                st.subheader("📋 Instrument Summary")
                summary = files.groupby("isin", as_index=False).agg({
                    "issuer_name": "first",
                    "maturity_date": "first",
                    "cfi_code": "first"
                })
                st.dataframe(summary.head(50))
                st.download_button("⬇ Download Summary CSV", summary.to_csv(index=False), "firds_summary.csv")
    except Exception as e:
        st.error(f"FIRDS error: {e}")

# ------------------- SSR -------------------
elif dataset == "SSR":
    st.header("📉 SSR Short Selling Exemptions")
    try:
        df = edl.load_ssr_exempted_shares()
        if df.empty:
            st.warning("No SSR data.")
        else:
            show_schema(df, "SSR Data")

            issuer = st.text_input("Filter by Issuer Name (optional)").strip()
            if issuer:
                df = df[df["issuer_name"].astype(str).str.contains(issuer, case=False, na=False)]

            st.subheader(f"{len(df)} records found")
            st.dataframe(df.head(100))
            st.download_button("⬇ Download SSR CSV", df.to_csv(index=False), "ssr_filtered.csv")

            if "publication_date" in df.columns:
                df["publication_date"] = safe_datetime(df["publication_date"])
                df["month"] = df["publication_date"].dt.to_period("M").astype(str)
                trend = df.groupby("month").size().reset_index(name="count")
                trend["month"] = pd.to_datetime(trend["month"])
                st.subheader("📈 SSR Monthly Trend")
                chart = alt.Chart(trend).mark_line(point=True).encode(
                    x=alt.X("month:T", title="Month"),
                    y=alt.Y("count:Q", title="Records")
                )
                st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"SSR error: {e}")

# ------------------- Freshness Check -------------------
st.markdown("---")
st.subheader("📅 Data Freshness Overview")
try:
    mifid_files = edl.load_mifid_file_list()
    mifid_latest = safe_datetime(mifid_files["publication_date"]).max()
    st.write(f"Latest MiFID publication: **{mifid_latest.date()}** ({(datetime.now() - mifid_latest).days} days ago)")
except: pass

try:
    firds_files = edl.load_latest_files()
    if "publication_date" in firds_files.columns:
        firds_latest = safe_datetime(firds_files["publication_date"]).max()
        st.write(f"Latest FIRDS publication: **{firds_latest.date()}** ({(datetime.now() - firds_latest).days} days ago)")
except: pass

st.markdown("Built with ❤️ using Streamlit & `esma_data_py`")
