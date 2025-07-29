import streamlit as st
import pandas as pd
import altair as alt
from esma_data_py import EsmaDataLoader

st.set_page_config(page_title="ESMA Advanced Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer – Advanced Edition")

st.markdown("""
This application uses **esma_data_py** to explore:
- 🧾 MiFID II
- 📂 FIRDS
- 📉 SSR
Includes safe filtering, visualizations, summaries, and error handling.
""")

edl = EsmaDataLoader()
dataset = st.sidebar.radio("Select dataset", ["MiFID", "FIRDS", "SSR"])

if dataset == "MiFID":
    st.header("🧾 MiFID II")
    try:
        files = edl.load_mifid_file_list()
        if files.empty:
            st.warning("No MiFID file metadata found.")
        else:
            files["publication_date"] = files["publication_date"].astype(str)
            dates = sorted(files["publication_date"].unique(), reverse=True)
            sel = st.selectbox("Select publication date", dates)
            filtered = files[files["publication_date"] == sel]

            if filtered.empty:
                st.warning("No files on that date.")
            else:
                st.dataframe(filtered)
                file_choice = st.selectbox("Choose file to download", filtered["file_name"])
                row = filtered[filtered["file_name"] == file_choice].iloc[0]
                url = row.get("download_link") or row.get("downloadUrl")
                if st.button("📥 Download & Analyze"):
                    df = edl.download_file(url)
                    st.subheader("Preview")
                    st.dataframe(df.head(50))
                    st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="mifid.csv")
                    st.subheader("Stats")
                    st.write(df.describe(include="all"))
                    # Show value counts for any categorical columns
                    cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
                    if cols:
                        col = st.selectbox("Show value counts for column", cols)
                        st.dataframe(df[col].value_counts().head(20).rename_axis(col).reset_index(name="count"))
    except Exception as e:
        st.error(f"MiFID error: {e}")

elif dataset == "FIRDS":
    st.header("📂 FIRDS Instrument Reference Data")
    try:
        files = edl.load_latest_files()
        if files.empty:
            st.warning("No FIRDS metadata available.")
        else:
            st.dataframe(files.head(50))
            if "instrument_type" in files.columns:
                instr_filter = st.text_input("Filter by instrument_type (e.g. SHRS)")
                if instr_filter:
                    files = files[files["instrument_type"].str.contains(instr_filter.upper(), na=False)]
            else:
                st.info("`instrument_type` not available. You can filter by ISIN or CFI code.")
            isin = st.text_input("Filter by ISIN (optional)")
            if isin and "isin" in files.columns:
                files = files[files["isin"].str.contains(isin.upper(), na=False)]
            cfi = st.text_input("Filter by CFI code (optional)")
            if cfi and "cfi_code" in files.columns:
                files = files[files["cfi_code"].str.contains(cfi.upper(), na=False)]
            
            if files.empty:
                st.warning("No matching FIRDS records found.")
            else:
                st.subheader(f"{len(files)} records found")
                st.dataframe(files.head(100))
                if "instrument_type" in files.columns:
                    cnt = files["instrument_type"].value_counts().reset_index()
                    cnt.columns = ["instrument_type", "count"]
                    st.subheader("Instrument Type Breakdown")
                    st.altair_chart(
                        alt.Chart(cnt).mark_bar().encode(x="instrument_type", y="count"),
                        use_container_width=True
                    )
    except Exception as e:
        st.error(f"FIRDS error: {e}")

elif dataset == "SSR":
    st.header("📉 SSR Short Selling Exemptions")
    try:
        df = edl.load_ssr_exempted_shares()
        if df.empty:
            st.warning("No SSR data.")
        else:
            issuer = st.text_input("Filter by issuer name")
            if issuer:
                df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]
            if df.empty:
                st.warning("No SSR records match filter.")
            else:
                st.dataframe(df.head(100))
                st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="ssr.csv")
                top = df["issuer_name"].value_counts().head(10).reset_index()
                top.columns = ["Issuer", "Count"]
                st.subheader("Top Issuers by Count")
                st.altair_chart(
                    alt.Chart(top).mark_bar().encode(x="Issuer", y="Count"),
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"SSR error: {e}")

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit & `esma_data_py`")
