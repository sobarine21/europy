import streamlit as st
import pandas as pd
from esma_data_py import EsmaDataLoader

# App config
st.set_page_config(page_title="ESMA Regulatory Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer")

st.markdown("""
Explore datasets from **ESMA (European Securities and Markets Authority)**:
- 🧾 MiFID II Instruments
- 📂 FIRDS Reference Data
- 📉 SSR Short Selling Reports
""")

# Initialize ESMA data loader
edl = EsmaDataLoader()

# Sidebar
dataset = st.sidebar.radio("Choose a dataset", ["MiFID", "FIRDS", "SSR"])

if dataset == "MiFID":
    st.header("🧾 MiFID II Dataset")
    try:
        files = edl.load_mifid_file_list()
        files["publication_date"] = pd.to_datetime(files["publication_date"])
        date = st.date_input("Select publication date", value=files["publication_date"].max())
        filtered = files[files["publication_date"] == pd.to_datetime(date)]
        st.dataframe(filtered)
        index = st.selectbox("Select file row", filtered.index)
        row = filtered.loc[index]

        if st.button("Download & Preview File"):
            df = edl.download_file(row.download_link)
            st.write(df.head(100))
            st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="mifid_data.csv")

    except Exception as e:
        st.error(f"Error: {e}")

elif dataset == "FIRDS":
    st.header("📂 FIRDS (Instrument Reference Data)")
    try:
        files = edl.load_latest_files()
        st.dataframe(files.head(50))

        instrument = st.text_input("Filter by instrument type (optional)")
        if instrument:
            filtered = files[files["instrument_type"].str.contains(instrument.upper(), na=False)]
            st.dataframe(filtered)

        index = st.selectbox("Select file row", files.index)
        row = files.loc[index]

        if st.button("Download & Preview File"):
            df = edl.download_file(row.download_link)
            st.write(df.head(100))
            st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="firds_data.csv")

    except Exception as e:
        st.error(f"Error: {e}")

elif dataset == "SSR":
    st.header("📉 SSR (Short Selling Exemptions)")
    try:
        df = edl.load_ssr_exempted_shares()
        issuer = st.text_input("Filter by Issuer Name (optional)")
        if issuer:
            df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]
        st.dataframe(df.head(100))
        st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="ssr_data.csv")

    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")
st.markdown("Built with ❤️ using `esma_data_py` + Streamlit. [GitHub](https://github.com/European-Securities-Markets-Authority/esma_data_py)")
