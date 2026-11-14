import re
import time
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="GitHub Repo Analytics", layout="wide")

CACHE_TTL = 3600      # seconds; ingestion runs daily, so 1h is fresh enough
MAX_ROWS = 1000       # row cap for the SQL explorer
REPO_URL = "https://github.com/Chandan22805/github-repo-analytics-platform"


# ---------------------------------------------------------------- data layer
@st.cache_resource
def get_engine():
    url = st.secrets["DB_URL"]
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]
            break
    return create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=0)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    # Postgres SUM() returns Decimal; convert so plotly/pandas treat it as numbers.
    for col in df.columns:
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return _clean(pd.read_sql(text(sql), conn, params=params))


def plot(fig):
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), legend_title_text="")
    st.plotly_chart(fig, width="stretch")


def empty_notice(df: pd.DataFrame) -> bool:
    if df.empty:
        st.info("No data for this selection yet.")
        return True
    return False


# ------------------------------------------------------------- SQL explorer
BANNED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|vacuum)\b",
    re.IGNORECASE,
)

EXAMPLES = {
    "Top 10 repos by stars": (
        "SELECT company_name, repo_name, stars\n"
        "FROM top_repos_per_company\n"
        "ORDER BY stars DESC\n"
        "LIMIT 10"
    ),
    "Stars gained in the last 7 days": (
        "SELECT c.company_name, r.name AS repo, SUM(g.star_growth) AS stars_gained\n"
        "FROM repo_daily_growth g\n"
        "JOIN repos r ON r.id = g.repo_id\n"
        "JOIN companies c ON c.company_id = r.company_id\n"
        "WHERE g.snapshot_date > CURRENT_DATE - 7\n"
        "GROUP BY c.company_name, r.name\n"
        "HAVING SUM(g.star_growth) IS NOT NULL\n"
        "ORDER BY stars_gained DESC\n"
        "LIMIT 10"
    ),
    "Language mix per company": (
        "SELECT company_name, language_name, total_bytes\n"
        "FROM language_popularity_by_company\n"
        "ORDER BY company_name, total_bytes DESC"
    ),
    "Repos with the most open issues": (
        "SELECT company_name, repo_name, open_issues\n"
        "FROM most_open_issues_repos"
    ),
}


def validate(sql: str) -> tuple[str | None, str | None]:
    """Return (clean_sql, error). Light checks only: the read-only DB role is the real guard."""
    q = sql.strip().rstrip(";").strip()
    if not q:
        return None, "Enter a query."
    if ";" in q:
        return None, "Only one statement allowed."
    if not re.match(r"^(select|with)\b", q, re.IGNORECASE):
        return None, "Only SELECT / WITH queries are allowed."
    if BANNED.search(q):
        return None, "Query contains a keyword that is not allowed (read-only access)."
    return q, None


def run_user_query(sql: str) -> pd.DataFrame:
    wrapped = f"SELECT * FROM (\n{sql}\n) AS _q LIMIT {MAX_ROWS}"
    escaped = wrapped.replace(":", "\\:")  # stop SQLAlchemy reading ':' as a bind param
    with get_engine().connect().execution_options(postgresql_readonly=True) as conn:
        return _clean(pd.read_sql(text(escaped), conn))


def load_example():
    st.session_state.sql = EXAMPLES[st.session_state.example]


# ------------------------------------------------------------------- header
st.title("GitHub Repository Analytics")
st.caption(
    "Daily-refreshed analytics on GitHub organisations: incremental ingestion, "
    "PostgreSQL warehouse, Parquet archive on S3. "
    f"[Source code]({REPO_URL})"
)

meta = load(
    """
    SELECT
        (SELECT COUNT(*) FROM companies) AS companies,
        (SELECT COUNT(*) FROM repos) AS repos,
        (SELECT COALESCE(SUM(stars), 0) FROM current_repo_metrics) AS stars,
        (SELECT COALESCE(SUM(forks), 0) FROM current_repo_metrics) AS forks,
        (SELECT MAX(snapshot_date) FROM repo_snapshots) AS last_snapshot
    """
).iloc[0]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Companies", f"{int(meta.companies):,}")
k2.metric("Repositories", f"{int(meta.repos):,}")
k3.metric("Total stars", f"{int(meta.stars):,}")
k4.metric("Total forks", f"{int(meta.forks):,}")
k5.metric("Data as of", str(meta.last_snapshot))

all_companies = load("SELECT company_name FROM companies ORDER BY 1")["company_name"].tolist()
selected = st.sidebar.multiselect("Companies", all_companies, default=all_companies)
if not selected:
    st.warning("Select at least one company in the sidebar.")
    st.stop()
st.sidebar.caption(f"Cached for {CACHE_TTL // 60} min. Pipeline runs daily.")

tab_over, tab_repos, tab_lang, tab_sql = st.tabs(
    ["Overview", "Repos", "Languages", "SQL explorer"]
)

# ----------------------------------------------------------------- overview
with tab_over:
    st.subheader("Total stars over time")
    trend = load(
        "SELECT company_name, snapshot_date, total_stars FROM company_total_stars "
        "ORDER BY snapshot_date"
    )
    trend = trend[trend.company_name.isin(selected)]
    if not empty_notice(trend):
        plot(px.line(trend, x="snapshot_date", y="total_stars", color="company_name"))

    st.subheader("Fastest growing repos")
    days = st.slider("Window (days)", 1, 30, 7)
    growth = load(
        """
        SELECT c.company_name, r.name AS repo_name, SUM(g.star_growth) AS stars_gained
        FROM repo_daily_growth g
        JOIN repos r ON r.id = g.repo_id
        JOIN companies c ON c.company_id = r.company_id
        WHERE g.snapshot_date > CURRENT_DATE - CAST(:days AS INTEGER)
          AND c.company_name = ANY(:companies)
        GROUP BY c.company_name, r.name
        HAVING SUM(g.star_growth) IS NOT NULL
        ORDER BY stars_gained DESC
        LIMIT 10
        """,
        {"days": days, "companies": selected},
    )
    if not empty_notice(growth):
        fig = px.bar(growth, x="stars_gained", y="repo_name", color="company_name", orientation="h")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        plot(fig)

# -------------------------------------------------------------------- repos
with tab_repos:
    left, right = st.columns(2)

    with left:
        st.subheader("Most starred")
        top = load("SELECT company_name, repo_name, stars FROM top_repos_per_company")
        top = top[top.company_name.isin(selected)].head(15)
        if not empty_notice(top):
            fig = px.bar(top, x="stars", y="repo_name", color="company_name", orientation="h")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            plot(fig)

    with right:
        st.subheader("Most forked")
        forks = load("SELECT company_name, repo_name, forks FROM company_top_forked_repos")
        forks = forks[forks.company_name.isin(selected)].sort_values("forks", ascending=False).head(15)
        if not empty_notice(forks):
            fig = px.bar(forks, x="forks", y="repo_name", color="company_name", orientation="h")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            plot(fig)

    st.subheader("Most open issues")
    issues = load(
        """
        SELECT c.company_name, r.name AS repo_name, crm.open_issues
        FROM current_repo_metrics crm
        JOIN repos r ON r.id = crm.repo_id
        JOIN companies c ON c.company_id = r.company_id
        WHERE c.company_name = ANY(:companies)
        ORDER BY crm.open_issues DESC
        LIMIT 10
        """,
        {"companies": selected},
    )
    if not empty_notice(issues):
        st.dataframe(issues, hide_index=True, width="stretch")

    st.subheader("Activity score (stars + forks + open issues)")
    activity = load("SELECT company_name, repo_name, activity_score FROM repo_activity_score")
    activity = activity[activity.company_name.isin(selected)].head(20)
    if not empty_notice(activity):
        st.dataframe(activity, hide_index=True, width="stretch")

# ---------------------------------------------------------------- languages
with tab_lang:
    mix = load(
        "SELECT company_name, language_name, total_bytes FROM language_popularity_by_company"
    )
    mix = mix[mix.company_name.isin(selected)]

    left, right = st.columns(2)
    with left:
        st.subheader("Top languages (by bytes of code)")
        overall = (
            mix.groupby("language_name", as_index=False)["total_bytes"]
            .sum()
            .sort_values("total_bytes", ascending=False)
            .head(10)
        )
        if not empty_notice(overall):
            fig = px.bar(overall, x="total_bytes", y="language_name", orientation="h")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            plot(fig)

    with right:
        st.subheader("Language diversity")
        div = load("SELECT company_name, language_count FROM company_language_diversity")
        div = div[div.company_name.isin(selected)]
        if not empty_notice(div):
            fig = px.bar(div, x="company_name", y="language_count")
            plot(fig)

    st.subheader("Language mix for one company")
    one = st.selectbox("Company", selected)
    one_mix = mix[mix.company_name == one].sort_values("total_bytes", ascending=False).head(10)
    if not empty_notice(one_mix):
        plot(px.pie(one_mix, names="language_name", values="total_bytes"))

# ------------------------------------------------------------- SQL explorer
with tab_sql:
    st.subheader("Query the warehouse")
    st.caption(
        f"Read-only. One SELECT / WITH statement, results capped at {MAX_ROWS} rows."
    )

    if "sql" not in st.session_state:
        st.session_state.sql = next(iter(EXAMPLES.values()))

    st.selectbox("Load an example", list(EXAMPLES), key="example", on_change=load_example)
    st.text_area("SQL", key="sql", height=200)

    if st.button("Run query", type="primary"):
        clean, err = validate(st.session_state.sql)
        if err:
            st.session_state.result = ("error", err)
        else:
            try:
                start = time.time()
                df = run_user_query(clean)
                st.session_state.result = ("ok", df, time.time() - start)
            except Exception as e:
                st.session_state.result = ("error", str(getattr(e, "orig", e)))

    result = st.session_state.get("result")
    if result:
        if result[0] == "error":
            st.error(result[1])
        else:
            _, df, elapsed = result
            st.caption(f"{len(df):,} rows in {elapsed:.2f}s")
            st.dataframe(df, hide_index=True, width="stretch")
            st.download_button("Download CSV", df.to_csv(index=False), "query_result.csv", "text/csv")

    with st.expander("Schema (tables and views)"):
        schema = load(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' ORDER BY table_name, ordinal_position"
        )
        for name, grp in schema.groupby("table_name"):
            st.markdown(f"**{name}**")
            st.dataframe(grp[["column_name", "data_type"]], hide_index=True, width="stretch")