"""DevEx Dashboard - Commit Activity Page"""
import streamlit as st

# Import components and utilities
from utils.database import get_database_connection
from components.sidebar import render_sidebar
from components.metrics.commits import render_commit_metrics

# Page configuration
st.set_page_config(
    page_title="DevEx Dashboard - Commit Activity",
    page_icon="📝",
    layout="wide"
)

# Connect to database
conn = get_database_connection()

# Header
st.title("📝 Commit Activity")
st.markdown("""
Examine code contribution patterns, repository activity, and code churn metrics.

Use the filters in the sidebar to customize the view for specific repositories and time periods.
""")

# Render sidebar and get filter values
selected_repos, selected_projects, start_date, end_date = render_sidebar()

# Render commit metrics with selected filters
render_commit_metrics(selected_repos, start_date, end_date)

# Footer
st.markdown("---")
st.caption("DevEx Dashboard - Data refreshed on demand")