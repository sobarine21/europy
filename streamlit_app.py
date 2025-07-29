import streamlit as st
import pandas as pd
from esma_data_py import EsmaDataLoader

# Page config
st.set_page_config(page_title="ESMA Regulatory Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer")

st.markdown("""
Explore datasets from **ESMA (European Securities and Markets Authority)**:
- 🧾 MiFID II Instruments
- 📂 FIRDS Reference Data
- 📉 SSR Short Selling Reports
""")

# Initialize ESMA Data Loader
edl = EsmaDataLoader()

# Sidebar selection
dataset = st.sidebar.radio("Choose a dataset", ["MiFID", "FIRDS", "SSR"])

# ---------------- MiFID II ----------------
if dataset == "MiFID":
    st.header("🧾 MiFID II Dataset")

    try:
        files = edl.load_mifid_file_list()
        files["publication_date"] = pd.to_datetime(files["publication_date"], errors="coerce")
        unique_dates = sorted(files["publication_date"].dropna().unique(), reverse=True)

        if unique_dates:
            selected_date = st.date_input("Select publication date", value=unique_dates[0])
            filtered = files[files["publication_date"] == pd.to_datetime(selected_date)]

            if filtered.empty:
                st.warning("No files found for the selected date.")
            else:
                st.dataframe(filtered)
                file_options = filtered["file_name"].tolist()
                selected_file = st.selectbox("Select file to download", file_options)

                row = filtered[filtered["file_name"] == selected_file].iloc[0]

                if st.button("📥 Download & Preview File"):
                    download_link = row.get("download_link") or row.get("downloadUrl")
                    if download_link:
                        df = edl.download_file(download_link)
                        st.write(df.head(100))
                        st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="mifid_data.csv")
                    else:
                        st.error("Download link not available for this row.")
        else:
            st.warning("No valid publication dates found in MiFID II dataset.")

    except Exception as e:
        st.error(f"Error: {e}")

# ---------------- FIRDS ----------------
elif dataset == "FIRDS":
    st.header("📂 FIRDS (Instrument Reference Data)")

    try:
        files = edl.load_latest_files()
        st.dataframe(files.head(50))

        instrument = st.text_input("Filter by instrument type (optional)")
        if instrument:
            files = files[files["instrument_type"].str.contains(instrument.upper(), na=False)]

        if not files.empty:
            file_options = files["file_name"].tolist()
            selected_file = st.selectbox("Select file to download", file_options)

            row = files[files["file_name"] == selected_file].iloc[0]

            if st.button("📥 Download & Preview File"):
                download_link = row.get("download_link") or row.get("downloadUrl")
                if download_link:
                    df = edl.download_file(download_link)
                    st.write(df.head(100))
                    st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="firds_data.csv")
                else:
                    st.error("Download link not available for this row.")
        else:
            st.warning("No FIRDS files available to display.")

    except Exception as e:
        st.error(f"Error: {e}")

# ---------------- SSR ----------------
elif dataset == "SSR":
    st.header("📉 SSR (Short Selling Exemptions)")

    try:
        df = edl.load_ssr_exempted_shares()
        issuer = st.text_input("Filter by Issuer Name (optional)")
        if issuer:
            df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]

        if not df.empty:
            st.dataframe(df.head(100))
            st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="ssr_data.csv")
        else:
            st.warning("No SSR data found for the selected filter.")

    except Exception as e:
        st.error(f"Error: {e}")

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("Built with ❤️ using `esma_data_py` + Streamlit. [GitHub](https://github.com/European-Securities-Markets-Authority/esma_data_py)")
