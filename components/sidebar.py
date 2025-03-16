"""
Sidebar component for the Streamlit dashboard
"""
import streamlit as st
from datetime import datetime, timedelta
from models import Issue, Repository
from config.settings import TIMEFRAMES, DEFAULT_TIMEFRAME

def render_sidebar():
    """
    Render sidebar with filters and return selected values
    
    Returns:
        tuple: (selected_repos, selected_projects, start_date, end_date)
    """
    st.sidebar.header("Filters")

    # Get list of repositories and projects
    repos = []
    for repo in Repository.objects:
        if repo.owner and repo.name:
            repos.append(f"{repo.owner}/{repo.name}")
    
    # Sort repositories for better UX
    repos = sorted(repos)
    
    projects = Issue.objects.distinct('project_key')

    # Repository selection
    selected_repos = st.sidebar.multiselect("Select Repositories", repos, default=repos)

    # Project selection (new for Jira issues)
    selected_projects = st.sidebar.multiselect("Select Jira Projects", projects, default=projects)

    # Date range selection
    st.sidebar.subheader("Time Period")

    # Initialize session state for date range if not present
    if 'date_range' not in st.session_state:
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=TIMEFRAMES[DEFAULT_TIMEFRAME]["days"])).date()
        st.session_state.date_range = (start_date, end_date)
        st.session_state.active_timeframe = DEFAULT_TIMEFRAME

    # Create button layout
    cols = st.sidebar.columns(4)

    # Create buttons with active state highlight
    for i, (key, tf) in enumerate(TIMEFRAMES.items()):
        with cols[i]:
            # Get current button style based on active state
            is_active = st.session_state.get('active_timeframe') == key
            button_style = "primary" if is_active else "secondary"
            
            # Create button with styling
            if st.button(tf["label"], key=f"btn_{key}", type=button_style):
                end_date = datetime.now().date()
                start_date = (datetime.now() - timedelta(days=tf["days"])).date()
                st.session_state.date_range = (start_date, end_date)
                st.session_state.active_timeframe = key

    # Display the date range picker with current value from session state
    date_range = st.sidebar.date_input(
        "Custom Date Range",
        value=st.session_state.date_range,
        key='date_range_picker'
    )

    # If user manually changes date input, update session state and clear active button
    if date_range != st.session_state.date_range:
        st.session_state.date_range = date_range
        st.session_state.active_timeframe = None  # No button is active when custom range selected

    # Process the selected date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Add one day to end_date to include the whole day
        end_date = datetime.combine(end_date, datetime.max.time())
    else:
        start_date = date_range[0]
        end_date = datetime.now()

    # Add refresh button
    if st.sidebar.button("Refresh Data"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

    return selected_repos, selected_projects, start_date, end_date