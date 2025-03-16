"""DevEx Dashboard - Issue Metrics Page"""
import streamlit as st

# Import components and utilities
from utils.database import get_database_connection
from components.sidebar import render_sidebar
from components.metrics.issues import render_issue_metrics

# Page configuration
st.set_page_config(
    page_title="DevEx Dashboard - Issue Metrics",
    page_icon="📊",
    layout="wide"
)

# Connect to database
conn = get_database_connection()

# Header
st.title("📊 Issue Metrics")
st.markdown("""
Track issue resolution times, analyze backlog health, and monitor project progress.

Use the filters in the sidebar to customize the view for specific repositories, projects, and time periods.
""")

# Render sidebar and get filter values
selected_repos, selected_projects, start_date, end_date = render_sidebar()

# Render Issue metrics with selected filters
render_issue_metrics(selected_repos, selected_projects, start_date, end_date)

# Footer
st.markdown("---")
st.caption("DevEx Dashboard - Data refreshed on demand")