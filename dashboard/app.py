import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

st.set_page_config(page_title="GitHub Repo Analytics", layout="wide")

@st.cache_resource
def get_engine():
    url = DB_URL.replace("postgresql://", "postgresql+psycopg2://")
    return create_engine(url)


@st.cache_data(ttl=3600)
def run_query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, get_engine())


st.title("GitHub Repository Analytics")

df = run_query("SELECT * FROM company_total_stars ORDER BY snapshot_date")
fig = px.line(df, x="snapshot_date", y="total_stars", color="company_name")
st.plotly_chart(fig, use_container_width=True)