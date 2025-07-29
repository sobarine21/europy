import streamlit as st
import pandas as pd
import altair as alt
from esma_data_py import EsmaDataLoader

# Page setup
st.set_page_config(page_title="ESMA Regulatory Data Explorer", layout="wide")
st.title("📊 ESMA Regulatory Data Explorer")

st.markdown("""
Access & analyze datasets from **ESMA**:
- 🧾 MiFID II Instruments
- 📂 FIRDS Reference Data
- 📉 SSR Short Selling Reports
""")

edl = EsmaDataLoader()
dataset = st.sidebar.radio("Choose a dataset", ["MiFID", "FIRDS", "SSR"])

# ---------------- MiFID ----------------
if dataset == "MiFID":
    st.header("🧾 MiFID II Dataset")
    try:
        files = edl.load_mifid_file_list()
        files["publication_date"] = pd.to_datetime(files["publication_date"], errors="coerce")
        files.dropna(subset=["publication_date"], inplace=True)

        dates = sorted(files["publication_date"].unique(), reverse=True)
        if dates:
            selected_date = st.date_input("Select publication date", value=dates[0])
            filtered = files[files["publication_date"] == pd.to_datetime(selected_date)]

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

                    # Simple Column Stats
                    st.subheader("📊 Basic Summary")
                    st.write(df.describe(include="all"))

                    if "instrument_id" in df.columns:
                        counts = df["instrument_id"].value_counts().reset_index().rename(columns={"index": "Instrument", "instrument_id": "Count"})
                        st.altair_chart(
                            alt.Chart(counts[:10]).mark_bar().encode(
                                x=alt.X("Instrument", sort="-y"),
                                y="Count"
                            ).properties(width=600, height=300),
                            use_container_width=True
                        )

        else:
            st.warning("No publication dates found.")

    except Exception as e:
        st.error(f"Error loading MiFID data: {e}")

# ---------------- FIRDS ----------------
elif dataset == "FIRDS":
    st.header("📂 FIRDS Reference Data")
    try:
        files = edl.load_latest_files()
        if "instrument_type" not in files.columns:
            st.error("Missing 'instrument_type' in FIRDS dataset.")
        else:
            st.dataframe(files.head(50))

            filter_value = st.text_input("🔍 Filter by instrument type (e.g., SHRS, BOND, ETFS)")
            if filter_value:
                filtered = files[files["instrument_type"].str.contains(filter_value.upper(), na=False)]
            else:
                filtered = files

            if not filtered.empty:
                st.write(f"{len(filtered)} records found.")
                st.dataframe(filtered.head(50))

                st.subheader("📈 Instrument Type Breakdown")
                breakdown = filtered["instrument_type"].value_counts().reset_index()
                breakdown.columns = ["Type", "Count"]
                st.altair_chart(
                    alt.Chart(breakdown).mark_bar().encode(
                        x=alt.X("Type", sort="-y"),
                        y="Count"
                    ).properties(width=700, height=300),
                    use_container_width=True
                )
            else:
                st.warning("No matching FIRDS entries.")

    except Exception as e:
        st.error(f"Error loading FIRDS data: {e}")

# ---------------- SSR ----------------
elif dataset == "SSR":
    st.header("📉 SSR (Short Selling Exemptions)")
    try:
        df = edl.load_ssr_exempted_shares()

        issuer = st.text_input("🔍 Filter by Issuer Name")
        if issuer:
            df = df[df["issuer_name"].str.contains(issuer, case=False, na=False)]

        st.dataframe(df.head(100))

        if not df.empty:
            st.download_button("⬇ Download CSV", df.to_csv(index=False), file_name="ssr_data.csv")

            st.subheader("📊 Top Issuers by Number of Exemptions")
            top_issuers = df["issuer_name"].value_counts().reset_index()
            top_issuers.columns = ["Issuer", "Count"]
            st.altair_chart(
                alt.Chart(top_issuers[:10]).mark_bar().encode(
                    x=alt.X("Issuer", sort="-y"),
                    y="Count"
                ).properties(width=600, height=300),
                use_container_width=True
            )
        else:
            st.warning("No SSR records for this issuer.")

    except Exception as e:
        st.error(f"Error loading SSR data: {e}")

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("Built with ❤️ using `esma_data_py`, Streamlit & Altair. [GitHub](https://github.com/European-Securities-Markets-Authority/esma_data_py)")
