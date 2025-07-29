import streamlit as st
import pandas as pd
import altair as alt
from esma_data_py import EsmaDataLoader

st.set_page_config(page_title="ESMA Regulatory Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer")

st.markdown("""
Explore datasets from **ESMA (European Securities and Markets Authority)**:
- 🧾 MiFID II Instruments
- 📂 FIRDS Reference Data
- 📉 SSR Short Selling Reports
- 🧮 CFI Codes
- 🏢 LEI Data
""")

edl = EsmaDataLoader()
dataset = st.sidebar.radio("Choose a dataset", ["MiFID", "FIRDS", "SSR", "CFI Codes", "LEI Data", "MiFIR Instruments"])

# ---------------- MiFID ----------------
if dataset == "MiFID":
    st.header("🧾 MiFID II Dataset")

    try:
        files = edl.load_mifid_file_list()
        files["publication_date"] = files["publication_date"].astype(str)

        available_dates = sorted(files["publication_date"].unique(), reverse=True)
        selected_date = st.selectbox("Select publication date", available_dates)

        filtered = files[files["publication_date"] == selected_date]

        if filtered.empty:
            st.warning("No files found for selected date.")
        else:
            st.dataframe(filtered)
            selected_file = st.selectbox("Select file to download", filtered["file_name"])
            row = filtered[filtered["file_name"] == selected_file].iloc[0]
            download_link = row.get("download_link") or row.get("downloadUrl")

            if st.button("📥 Download & Analyze File"):
                df = edl.download_file(download_link)
                st.subheader("Preview")
                st.dataframe(df.head(100))
                st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="mifid_data.csv")

                st.subheader("📊 Summary Stats")
                st.write(df.describe(include="all"))

                if "instrument_id" in df.columns:
                    top = df["instrument_id"].value_counts().reset_index()
                    top.columns = ["Instrument", "Count"]
                    st.altair_chart(
                        alt.Chart(top[:10]).mark_bar().encode(x="Instrument", y="Count"),
                        use_container_width=True
                    )
    except Exception as e:
        st.error(f"MiFID Error: {e}")

# ---------------- FIRDS ----------------
elif dataset == "FIRDS":
    st.header("📂 FIRDS Instrument Reference Data")
    try:
        files = edl.load_latest_files()
        if files.empty:
            st.warning("No FIRDS data available.")
        else:
            st.dataframe(files.head(50))
            filter_val = st.text_input("🔍 Filter by instrument type (e.g., SHRS, BOND, ETFS)")
            if filter_val:
                files = files[files["instrument_type"].str.contains(filter_val.upper(), na=False)]

            if not files.empty:
                st.subheader("📊 Instrument Type Breakdown")
                chart_data = files["instrument_type"].value_counts().reset_index()
                chart_data.columns = ["Type", "Count"]
                st.altair_chart(
                    alt.Chart(chart_data).mark_bar().encode(x="Type", y="Count"),
                    use_container_width=True
                )
                st.dataframe(files.head(100))
            else:
                st.warning("No matching instrument types found.")
    except Exception as e:
        st.error(f"FIRDS Error: {e}")

# ---------------- SSR ----------------
elif dataset == "SSR":
    st.header("📉 SSR Short Selling Exemptions")
    try:
        df = edl.load_ssr_exempted_shares()
        filter_val = st.text_input("🔍 Filter by Issuer Name")
        if filter_val:
            df = df[df["issuer_name"].str.contains(filter_val, case=False, na=False)]

        if not df.empty:
            st.dataframe(df.head(100))
            st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="ssr_data.csv")

            st.subheader("📊 Top Issuers")
            top_issuers = df["issuer_name"].value_counts().reset_index()
            top_issuers.columns = ["Issuer", "Count"]
            st.altair_chart(
                alt.Chart(top_issuers[:10]).mark_bar().encode(x="Issuer", y="Count"),
                use_container_width=True
            )
        else:
            st.warning("No SSR entries found.")
    except Exception as e:
        st.error(f"SSR Error: {e}")

# ---------------- CFI ----------------
elif dataset == "CFI Codes":
    st.header("🧮 Classification of Financial Instruments (CFI)")
    try:
        df = edl.load_cfi_codes()
        st.dataframe(df)
        st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="cfi_codes.csv")
    except Exception as e:
        st.error(f"CFI Error: {e}")

# ---------------- LEI ----------------
elif dataset == "LEI Data":
    st.header("🏢 Legal Entity Identifiers (LEI)")
    try:
        df = edl.load_lei_data()
        search = st.text_input("🔍 Filter by Entity Name or LEI")
        if search:
            df = df[df["legal_name"].str.contains(search, case=False, na=False)]

        st.dataframe(df.head(100))
        st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="lei_data.csv")
    except Exception as e:
        st.error(f"LEI Error: {e}")

# ---------------- MiFIR ----------------
elif dataset == "MiFIR Instruments":
    st.header("📊 MiFIR Transaction Data")
    try:
        df = edl.load_mifir_instruments()
        st.dataframe(df.head(100))
        st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="mifir_data.csv")
    except Exception as e:
        st.error(f"MiFIR Error: {e}")

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("Built with ❤️ using `esma_data_py`, Streamlit & Altair.")
