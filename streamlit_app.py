import streamlit as st
import pandas as pd
import altair as alt
from esma_data_py import EsmaDataLoader

st.set_page_config(page_title="ESMA Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer")

st.markdown("""
Browse key ESMA datasets:
- 🧾 MiFID II Instruments
- 📂 FIRDS Reference Data
- 📉 SSR Short Selling Reports
""")

edl = EsmaDataLoader()
dataset = st.sidebar.radio("Choose a dataset", ["MiFID", "FIRDS", "SSR"])

if dataset == "MiFID":
    st.header("🧾 MiFID II File List")
    try:
        files = edl.load_mifid_file_list()
        if files.empty:
            st.warning("No MiFID files available.")
        else:
            files["publication_date"] = files["publication_date"].astype(str)
            dates = sorted(files["publication_date"].unique(), reverse=True)
            selected_date = st.selectbox("Select publication date", dates)
            filtered = files[files["publication_date"] == selected_date]

            if filtered.empty:
                st.warning("No files for selected date.")
            else:
                st.dataframe(filtered)
                chosen = st.selectbox("Choose a file to download", filtered["file_name"])
                row = filtered[filtered["file_name"] == chosen].iloc[0]
                url = row.get("download_link") or row.get("downloadUrl")

                if st.button("📥 Download & Analyze"):
                    df = edl.download_file(url)
                    st.subheader("Preview")
                    st.dataframe(df.head(100))
                    st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="mifid.csv")

                    st.subheader("Summary Statistics")
                    st.write(df.describe(include="all"))
                    if "instrument_id" in df.columns:
                        top = df["instrument_id"].value_counts().head(10).reset_index()
                        top.columns = ["Instrument", "Count"]
                        st.altair_chart(
                            alt.Chart(top).mark_bar().encode(
                                x="Instrument", y="Count"
                            ).properties(width=600, height=300),
                            use_container_width=True
                        )
    except Exception as e:
        st.error(f"MiFID error: {e}")

elif dataset == "FIRDS":
    st.header("📂 FIRDS Instrument Data")
    try:
        files = edl.load_latest_files()
        if files.empty:
            st.warning("No FIRDS data.")
        else:
            st.dataframe(files.head(50))
            instr = st.text_input("Filter by instrument_type (e.g. SHRS)")
            if instr:
                files = files[files["instrument_type"].str.contains(instr.upper(), na=False)]
            if files.empty:
                st.warning("No matching instrument types.")
            else:
                st.subheader(f"{len(files)} records found")
                st.dataframe(files.head(100))
                counts = files["instrument_type"].value_counts().reset_index()
                counts.columns = ["Type", "Count"]
                st.altair_chart(
                    alt.Chart(counts).mark_bar().encode(x="Type", y="Count"),
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"FIRDS error: {e}")

elif dataset == "SSR":
    st.header("📉 SSR Short‑Selling Exemptions")
    try:
        df = edl.load_ssr_exempted_shares()
        if df.empty:
            st.warning("No SSR data.")
        else:
            issuer = st.text_input("Filter by issuer_name")
            if issuer:
                df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]
            if df.empty:
                st.warning("No matching SSR entries.")
            else:
                st.dataframe(df.head(100))
                st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="ssr.csv")
                top = df["issuer_name"].value_counts().head(10).reset_index()
                top.columns = ["Issuer", "Count"]
                st.altair_chart(
                    alt.Chart(top).mark_bar().encode(x="Issuer", y="Count"),
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"SSR error: {e}")

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit & esma_data_py")
