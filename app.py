import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Financial Risk Dashboard", layout="wide")

DB_NAME = "finance_dashboard.db"


def risk_skoru_hesapla(gelir, gider, tasarruf, borc):
    if gelir <= 0:
        return 100.0

    harcama_orani = gider / gelir
    borc_orani = borc / gelir
    tasarruf_orani = tasarruf / gelir

    skor = (harcama_orani * 45) + (borc_orani * 40) - (tasarruf_orani * 25)
    skor = max(0, min(100, skor * 100 / 85))
    return round(skor, 2)


def risk_seviyesi_belirle(skor):
    if skor < 35:
        return "Low Risk"
    elif skor < 65:
        return "Medium Risk"
    return "High Risk"


def veriyi_kaydet_sqlite(df, db_name=DB_NAME):
    conn = sqlite3.connect(db_name)
    df.to_sql("financial_records", conn, if_exists="replace", index=False)
    conn.close()


def oneriler_uret(row):
    oneriler = []

    if row["gider"] > row["gelir"] * 0.7:
        oneriler.append("Your expenses are high compared to your income.")
    if row["borc"] > row["gelir"] * 0.4:
        oneriler.append("Your debt level is relatively high.")
    if row["tasarruf"] < row["gelir"] * 0.1:
        oneriler.append("Your savings rate is low.")

    if not oneriler:
        oneriler.append("Your financial profile looks balanced.")

    return " ".join(oneriler)


def ornek_veri_olustur():
    return pd.DataFrame(
        {
            "gelir": [25000, 18000, 30000, 22000, 27000, 16000, 24000, 35000],
            "gider": [12000, 15000, 14000, 17000, 13000, 14000, 16000, 18000],
            "tasarruf": [5000, 1000, 8000, 2000, 7000, 500, 2500, 10000],
            "borc": [3000, 7000, 2000, 6000, 2500, 9000, 5500, 3000],
        }
    )


st.title("📊 Financial Risk Dashboard")
st.write(
    "Upload your CSV file or use sample data to analyze income, expenses, savings, and debt."
)

st.sidebar.header("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

required_columns = ["gelir", "gider", "tasarruf", "borc"]

df = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif use_sample:
    df = ornek_veri_olustur()

if df is not None:
    eksik = [col for col in required_columns if col not in df.columns]
    if eksik:
        st.error(f"Missing columns in CSV: {eksik}")
        st.stop()

    df["risk_skoru"] = df.apply(
        lambda row: risk_skoru_hesapla(
            row["gelir"], row["gider"], row["tasarruf"], row["borc"]
        ),
        axis=1,
    )
    df["risk_seviyesi"] = df["risk_skoru"].apply(risk_seviyesi_belirle)
    df["oneriler"] = df.apply(oneriler_uret, axis=1)

    veriyi_kaydet_sqlite(df)

    st.subheader("📌 Data Preview")
    st.dataframe(df, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"{df['gelir'].sum():,.0f}")
    col2.metric("Total Expenses", f"{df['gider'].sum():,.0f}")
    col3.metric("Total Savings", f"{df['tasarruf'].sum():,.0f}")
    col4.metric("Average Risk Score", f"{df['risk_skoru'].mean():.1f}")

    st.subheader("📈 Expense Distribution")
    fig1, ax1 = plt.subplots()
    ax1.bar(df.index.astype(str), df["gider"])
    ax1.set_xlabel("Record")
    ax1.set_ylabel("Expense")
    ax1.set_title("Expense by Record")
    st.pyplot(fig1)

    st.subheader("📉 Risk Score Distribution")
    fig2, ax2 = plt.subplots()
    ax2.bar(df.index.astype(str), df["risk_skoru"])
    ax2.set_xlabel("Record")
    ax2.set_ylabel("Risk Score")
    ax2.set_title("Risk Score by Record")
    st.pyplot(fig2)

    st.subheader("🥧 Risk Level Distribution")
    risk_counts = df["risk_seviyesi"].value_counts()
    fig3, ax3 = plt.subplots()
    ax3.pie(risk_counts, labels=risk_counts.index, autopct="%1.1f%%")
    ax3.set_title("Risk Level Breakdown")
    st.pyplot(fig3)

    st.subheader("💡 Personalized Recommendations")
    for i, row in df.iterrows():
        st.write(f"**Record {i}** — {row['risk_seviyesi']} ({row['risk_skoru']})")
        st.write(row["oneriler"])

    st.success("Analysis completed and saved to SQLite database.")
    st.caption(f"Database file: {os.path.abspath(DB_NAME)}")

else:
    st.info(
        "Upload a CSV file with columns: gelir, gider, tasarruf, borc — or click 'Use Sample Data'."
    )

    st.subheader("Expected CSV Format")
    st.code(
        """gelir,gider,tasarruf,borc
25000,12000,5000,3000
18000,15000,1000,7000
30000,14000,8000,2000""",
        language="csv",
    )
