"""DevEx Dashboard - Pull Request Metrics Page"""
import streamlit as st

# Import components and utilities
from utils.database import get_database_connection
from components.sidebar import render_sidebar
from components.metrics.pull_requests import render_pr_metrics

# Page configuration
st.set_page_config(
    page_title="DevEx Dashboard - PR Metrics",
    page_icon="🔄",
    layout="wide"
)

# Connect to database
conn = get_database_connection()

# Header
st.title("🔄 Pull Request Metrics")
st.markdown("""
Analyze pull request throughput, lead times, and code review processes to optimize your development workflow.

Use the filters in the sidebar to customize the view for specific repositories and time periods.
""")

# Render sidebar and get filter values
selected_repos, selected_projects, start_date, end_date = render_sidebar()

# Render PR metrics with selected filters
render_pr_metrics(selected_repos, start_date, end_date)

# Footer
st.markdown("---")
st.caption("DevEx Dashboard - Data refreshed on demand")