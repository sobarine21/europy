import streamlit as st
import pandas as pd
import altair as alt
from esma_data_py import EsmaDataLoader
from datetime import datetime

st.set_page_config(page_title="ESMA Advanced Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer – Production Edition")

edl = EsmaDataLoader()

# --- Utility Function ---
def show_schema(df, label):
    with st.expander(f"🧬 Schema: {label}"):
        st.dataframe(pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str)
        }))

# --- Sidebar ---
dataset = st.sidebar.radio("Select Dataset", ["MiFID", "FIRDS", "SSR"])

# --- MiFID Section ---
if dataset == "MiFID":
    st.header("🧾 MiFID II")
    try:
        files = edl.load_mifid_file_list()
        if files.empty:
            st.warning("No MiFID file metadata found.")
        else:
            # Normalize to naive datetime (drop timezone) files["publication_date"] = pd.to_datetime(files["publication_date"]).dt.tz_localize(None)
            show_schema(files, "MiFID File List")

            # Date range filter
            min_date, max_date = files["publication_date"].min(), files["publication_date"].max()
            date_range = st.date_input("Filter by publication date range", [min_date, max_date])
            filtered = files[(files["publication_date"] >= pd.to_datetime(date_range[0])) & 
                             (files["publication_date"] <= pd.to_datetime(date_range[1]))]

            st.subheader(f"{len(filtered)} files found")
            st.dataframe(filtered)

            selected_files = st.multiselect("Select files to download and analyze", filtered["file_name"])
            if st.button("📥 Download & Analyze Selected"):
                combined = pd.DataFrame()
                for fname in selected_files:
                    row = filtered[filtered["file_name"] == fname].iloc[0]
                    url = row.get("download_link") or row.get("downloadUrl")
                    df = edl.download_file(url)
                    df["source_file"] = fname
                    combined = pd.concat([combined, df], ignore_index=True)

                if not combined.empty:
                    st.subheader("Preview Combined Data")
                    search_term = st.text_input("🔍 Search within preview")
                    if search_term:
                        combined = combined[combined.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)]
                    st.dataframe(combined.head(100))
                    st.download_button("⬇ Download Combined CSV", combined.to_csv(index=False), file_name="mifid_combined.csv")
                    show_schema(combined, "Combined MiFID Data")
    except Exception as e:
        st.error(f"MiFID error: {e}")

# --- FIRDS Section ---
elif dataset == "FIRDS":
    st.header("📂 FIRDS Instrument Reference Data")
    try:
        files = edl.load_latest_files()
        if files.empty:
            st.warning("No FIRDS data available.")
        else:
            show_schema(files, "FIRDS Metadata")

            isin = st.text_input("Filter by ISIN (optional)")
            cfi = st.text_input("Filter by CFI Code (optional)")

            if isin:
                files = files[files["isin"].str.contains(isin.upper(), na=False)]
            if cfi:
                files = files[files["cfi_code"].str.contains(cfi.upper(), na=False)]

            st.subheader(f"{len(files)} records found")
            st.dataframe(files.head(100))
            st.download_button("⬇ Download FIRDS CSV", files.to_csv(index=False), file_name="firds_filtered.csv")

            # Profile Summary Table
            if not files.empty:
                summary = files.groupby("isin", as_index=False).agg({
                    "issuer_name": "first",
                    "maturity_date": "first",
                    "cfi_code": "first"
                })
                st.subheader("📋 Instrument Summary")
                st.dataframe(summary.head(50))
                st.download_button("⬇ Download Summary", summary.to_csv(index=False), file_name="firds_summary.csv")
    except Exception as e:
        st.error(f"FIRDS error: {e}")

# --- SSR Section ---
elif dataset == "SSR":
    st.header("📉 SSR Short Selling Exemptions")
    try:
        df = edl.load_ssr_exempted_shares()
        if df.empty:
            st.warning("No SSR data.")
        else:
            show_schema(df, "SSR Data")
            issuer = st.text_input("Filter by Issuer Name (optional)")
            if issuer:
                df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]

            st.subheader(f"{len(df)} records")
            st.dataframe(df.head(100))
            st.download_button("⬇ Download SSR CSV", df.to_csv(index=False), file_name="ssr_filtered.csv")

            # Time trend
            if "publication_date" in df.columns:
                df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
                df["month"] = df["publication_date"].dt.to_period("M").astype(str)
                trend = df.groupby("month").size().reset_index(name="count")
                chart = alt.Chart(trend).mark_line(point=True).encode(
                    x=alt.X("month:T", title="Month"),
                    y=alt.Y("count:Q", title="Number of Exemptions")
                )
                st.subheader("📈 SSR Monthly Trend")
                st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"SSR error: {e}")

# --- Data Freshness Report ---
st.markdown("---")
st.subheader("📅 Data Freshness")
try:
    mifid_files = edl.load_mifid_file_list()
    mifid_latest = pd.to_datetime(mifid_files["publication_date"]).max()
    st.write(f"Latest MiFID publication date: **{mifid_latest.date()}** ({(datetime.now() - mifid_latest).days} days ago)")
except: pass

try:
    firds_files = edl.load_latest_files()
    if "publication_date" in firds_files.columns:
        firds_latest = pd.to_datetime(firds_files["publication_date"]).max()
        st.write(f"Latest FIRDS metadata date: **{firds_latest.date()}** ({(datetime.now() - firds_latest).days} days ago)")
except: pass

st.markdown("Built with ❤️ using Streamlit & `esma_data_py`")
