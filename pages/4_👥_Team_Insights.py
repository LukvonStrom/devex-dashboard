"""DevEx Dashboard - Team Insights Page"""
import streamlit as st

# Import components and utilities
from utils.database import get_database_connection
from components.sidebar import render_sidebar
from components.metrics.team import render_team_insights

# Page configuration
st.set_page_config(
    page_title="DevEx Dashboard - Team Insights",
    page_icon="👥",
    layout="wide"
)

# Connect to database
conn = get_database_connection()

# Header
st.title("👥 Team Insights")
st.markdown("""
Monitor team collaboration patterns, cross-team dependencies, and DORA-aligned performance metrics.

Use the filters in the sidebar to customize the view for specific repositories and time periods.
""")

# Render sidebar and get filter values
selected_repos, selected_projects, start_date, end_date = render_sidebar()

# Render team insights with selected filters
render_team_insights(selected_repos, start_date, end_date)

# Footer
st.markdown("---")
st.caption("DevEx Dashboard - Data refreshed on demand")