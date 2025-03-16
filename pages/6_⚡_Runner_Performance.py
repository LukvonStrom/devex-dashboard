"""GitHub Actions Runner Performance Dashboard"""
import streamlit as st

# Import components and utilities
from utils.database import get_database_connection
from components.sidebar import render_sidebar
from components.runners import render_runner_performance

# Page configuration
st.set_page_config(
    page_title="GitHub Runner Performance Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Connect to database
conn = get_database_connection()

# Application Layout
# ----------------------------------------------------------------------

# Header
st.title("⚡ GitHub Actions Runner Performance")
st.markdown("""
### Optimize your CI/CD pipelines with comprehensive GitHub Actions analytics

This dashboard provides detailed insights into runner performance, pickup times, execution speeds, 
and success rates to help you identify performance bottlenecks and improve build reliability.

* **Compare runner types** to determine the best fit for your workflows
* **Track pickup time trends** to ensure optimal queue times
* **Analyze success rates by branch** to identify problem areas
* **Monitor execution times** to optimize long-running workflows
""")

# Render sidebar and get filter values
selected_repos, selected_projects, start_date, end_date = render_sidebar()


# Runner Performance Tab
# ----------------------------------------------------------------------
render_runner_performance(selected_repos, start_date, end_date)

# Footer
st.markdown("---")
st.caption("DevEx Dashboard - Data refreshed on demand")