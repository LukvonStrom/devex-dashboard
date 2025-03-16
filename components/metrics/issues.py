"""
Issue metrics component
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models import Issue
from utils.data_processing import (
    queryset_to_dataframe, 
    create_time_series_chart, 
    calculate_trend_metrics,
    add_trendline
)
from config.settings import PRIORITY_ORDER

@st.cache_data(ttl=600)
def get_issue_data(selected_repos, selected_projects, start_date, end_date, closed_only=False):
    """Get issue data with caching"""
    filter_args = {
        'created_at__gte': start_date,
        'created_at__lte': end_date
    }
    
    if closed_only:
        filter_args['closed_at__ne'] = None
        
    # Apply repo filter if available
    if selected_repos:
        filter_args['repo__in'] = selected_repos
        
    # Apply project filter if available (Jira-specific)
    if selected_projects:
        filter_args['project_key__in'] = selected_projects
    
    query = Issue.objects(**filter_args)
    return queryset_to_dataframe(query)

@st.cache_data(ttl=600)
def get_closed_issues(selected_repos, selected_projects, start_date, end_date):
    """Get issues closed in the period"""
    filter_args = {
        'closed_at__ne': None,
        'closed_at__gte': start_date,
        'closed_at__lte': end_date
    }
    
    # Apply repo filter if available
    if selected_repos:
        filter_args['repo__in'] = selected_repos
        
    # Apply project filter if available (Jira-specific)
    if selected_projects:
        filter_args['project_key__in'] = selected_projects
        
    query = Issue.objects(**filter_args)
    return queryset_to_dataframe(query)

def render_issue_metrics(selected_repos, selected_projects, start_date, end_date):
    """
    Render issue metrics
    
    Args:
        selected_repos: List of selected repository names
        selected_projects: List of selected Jira project keys
        start_date: Start date for data filtering
        end_date: End date for data filtering
    """
    st.header("Issue Metrics")
    
    # Get issue data
    issue_all_df = get_issue_data(selected_repos, selected_projects, start_date, end_date)
    issue_closed_df = get_issue_data(selected_repos, selected_projects, start_date, end_date, closed_only=True)
    closed_in_period_df = get_closed_issues(selected_repos, selected_projects, start_date, end_date)
    
    # Issue Overview Metrics
    if not issue_all_df.empty:
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_issues = len(issue_all_df)
            st.metric("Total Issues", total_issues)
            
        with col2:
            open_issues = issue_all_df['closed_at'].isna().sum()
            open_rate = (open_issues / total_issues * 100) if total_issues > 0 else 0
            st.metric("Open Issues", f"{open_issues} ({open_rate:.1f}%)")
            
        with col3:
            if not issue_closed_df.empty:
                issue_closed_df['resolution_days'] = (
                    issue_closed_df['closed_at'] - 
                    issue_closed_df['created_at']
                ).dt.total_seconds() / (60 * 60 * 24)
                avg_resolution = issue_closed_df['resolution_days'].mean()
                st.metric("Avg Resolution Time (days)", f"{avg_resolution:.2f}")
            else:
                st.metric("Avg Resolution Time (days)", "N/A")
        
        with col4:
            if not closed_in_period_df.empty:
                closed_count = len(closed_in_period_df)
                st.metric("Issues Closed", closed_count)
            else:
                st.metric("Issues Closed", "0")
                
        # Jira-specific metrics
        st.subheader("Jira Issue Analysis")
        
        # Create tabs for different Jira metrics
        jira_tabs = st.tabs(["Issue Types", "Priority", "Status", "Story Points", "Resolution Time"])
        
        # Tab 1: Issue Types
        with jira_tabs[0]:
            if 'issue_type' in issue_all_df.columns and not issue_all_df['issue_type'].isna().all():
                # Create issue type distribution
                issue_types_count = issue_all_df['issue_type'].value_counts().reset_index()
                issue_types_count.columns = ['issue_type', 'count']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Issue Types Pie Chart
                    fig = px.pie(
                        issue_types_count, 
                        values='count', 
                        names='issue_type',
                        title='Issue Types Distribution',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Issue Types by Project
                    if 'project_key' in issue_all_df.columns and not issue_all_df['project_key'].isna().all():
                        project_issue_types = issue_all_df.groupby(['project_key', 'issue_type']).size().reset_index(name='count')
                        
                        fig = px.bar(
                            project_issue_types,
                            x='project_key',
                            y='count',
                            color='issue_type',
                            title='Issue Types by Project',
                            labels={'project_key': 'Project', 'count': 'Number of Issues', 'issue_type': 'Issue Type'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No project key data available for the selected issues.")
            else:
                st.info("No issue type data available for the selected issues.")
        
        # Tab 2: Priority
        with jira_tabs[1]:
            if 'priority' in issue_all_df.columns and not issue_all_df['priority'].isna().all():
                # Convert priority to category with custom order
                # Create a copy to avoid SettingWithCopyWarning
                priority_df = issue_all_df.copy()
                
                # Add priority order column for sorting
                priority_df['priority_order'] = priority_df['priority'].map(
                    lambda x: PRIORITY_ORDER.get(x, 99)  # Default to high number for unknown priorities
                )
                
                # Sort by the order
                priority_df = priority_df.sort_values('priority_order')
                
                # Create priority distribution
                priority_counts = priority_df['priority'].value_counts().reset_index()
                priority_counts.columns = ['priority', 'count']
                
                # Add order for sorting
                priority_counts['priority_order'] = priority_counts['priority'].map(
                    lambda x: PRIORITY_ORDER.get(x, 99)
                )
                priority_counts = priority_counts.sort_values('priority_order')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Priority Distribution
                    fig = px.bar(
                        priority_counts,
                        x='priority',
                        y='count',
                        title='Issue Priority Distribution',
                        labels={'priority': 'Priority', 'count': 'Number of Issues'},
                        color='priority',
                        color_discrete_sequence=px.colors.sequential.Reds_r
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Resolution time by priority
                    if not issue_closed_df.empty and 'priority' in issue_closed_df.columns:
                        resolution_by_priority = issue_closed_df.copy()
                        if 'resolution_days' not in resolution_by_priority.columns:
                            resolution_by_priority['resolution_days'] = (
                                resolution_by_priority['closed_at'] - 
                                resolution_by_priority['created_at']
                            ).dt.total_seconds() / (60 * 60 * 24)
                            
                        resolution_by_priority['priority_order'] = resolution_by_priority['priority'].map(
                            lambda x: PRIORITY_ORDER.get(x, 99)
                        )
                        
                        # Calculate average resolution time by priority
                        avg_resolution = resolution_by_priority.groupby('priority')['resolution_days'].mean().reset_index()
                        if not avg_resolution.empty:
                            avg_resolution['priority_order'] = avg_resolution['priority'].map(
                                lambda x: PRIORITY_ORDER.get(x, 99)
                            )
                            avg_resolution = avg_resolution.sort_values('priority_order')
                            
                            # Resolution Time by Priority
                            fig = px.bar(
                                avg_resolution,
                                x='priority',
                                y='resolution_days',
                                title='Average Resolution Time by Priority',
                                labels={'priority': 'Priority', 'resolution_days': 'Days to Resolve'},
                                color='resolution_days',
                                color_continuous_scale='Reds_r'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Insufficient data to calculate resolution time by priority.")
                    else:
                        st.info("No closed issues available for resolution time analysis.")
            else:
                st.info("No priority data available for the selected issues.")
        
        # Tab 3: Status
        with jira_tabs[2]:
            if 'status' in issue_all_df.columns and not issue_all_df['status'].isna().all():
                # Create status distribution
                status_counts = issue_all_df['status'].value_counts().reset_index()
                status_counts.columns = ['status', 'count']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Status Distribution
                    fig = px.pie(
                        status_counts, 
                        values='count', 
                        names='status',
                        title='Issue Status Distribution',
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Status Distribution by Project
                    if 'project_key' in issue_all_df.columns:
                        project_status = issue_all_df.groupby(['project_key', 'status']).size().reset_index(name='count')
                        
                        fig = px.bar(
                            project_status,
                            x='project_key',
                            y='count',
                            color='status',
                            title='Status Distribution by Project',
                            labels={'project_key': 'Project', 'count': 'Number of Issues', 'status': 'Status'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # Tab 4: Story Points
        with jira_tabs[3]:
            # Check if story_points column exists and has data
            if 'story_points' in issue_all_df.columns and issue_all_df['story_points'].notna().any():
                sp_df = issue_all_df.dropna(subset=['story_points'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Story Points Distribution
                    fig = px.histogram(
                        sp_df,
                        x='story_points',
                        nbins=10,
                        title='Story Points Distribution',
                        labels={'story_points': 'Story Points', 'count': 'Number of Issues'},
                        color_discrete_sequence=['#3366CC'],
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Story Points by Issue Type
                    if 'issue_type' in sp_df.columns:
                        sp_by_type = sp_df.groupby('issue_type')['story_points'].mean().reset_index()
                        
                        fig = px.bar(
                            sp_by_type,
                            x='issue_type',
                            y='story_points',
                            title='Average Story Points by Issue Type',
                            labels={'issue_type': 'Issue Type', 'story_points': 'Avg Story Points'},
                            color='story_points',
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Total Story Points by Project/Status
                if 'project_key' in sp_df.columns and 'status' in sp_df.columns:
                    # Pivot table of total story points by project and status
                    pivot_sp = sp_df.pivot_table(
                        values='story_points', 
                        index='project_key', 
                        columns='status', 
                        aggfunc='sum',
                        fill_value=0
                    ).reset_index()
                    
                    st.subheader('Story Points by Project and Status')
                    st.dataframe(pivot_sp, use_container_width=True)
            else:
                st.info("No story points data available in the selected issues.")

        with jira_tabs[4]:
            # Issue Resolution Time Analysis
            if not issue_closed_df.empty:
                st.subheader("Issue Resolution Time Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Issue Resolution Time by Repo
                    fig = px.box(
                        issue_closed_df, 
                        x='repo', 
                        y='resolution_days',
                        title='Issue Resolution Time by Repository',
                        labels={'resolution_days': 'Days', 'repo': 'Repository'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Issue Open/Close Rate
                    if not issue_all_df.empty or not closed_in_period_df.empty:
                        # Extract dates for opened issues
                        if not issue_all_df.empty:
                            issue_all_df['date'] = pd.to_datetime(issue_all_df['created_at']).dt.date
                            opened_by_date = issue_all_df.groupby('date').size().reset_index(name='opened')
                            opened_by_date['date'] = pd.to_datetime(opened_by_date['date'])
                        else:
                            opened_by_date = pd.DataFrame(columns=['date', 'opened'])
                        
                        # Extract dates for closed issues
                        if not closed_in_period_df.empty:
                            closed_in_period_df['date'] = pd.to_datetime(closed_in_period_df['closed_at']).dt.date
                            closed_by_date = closed_in_period_df.groupby('date').size().reset_index(name='closed')
                            closed_by_date['date'] = pd.to_datetime(closed_by_date['date'])
                        else:
                            closed_by_date = pd.DataFrame(columns=['date', 'closed'])
                        
                        # Create a date range and merge both dataframes
                        date_range_df = pd.DataFrame({
                            'date': pd.date_range(start=start_date, end=end_date)
                        })
                        
                        # Merge with date range and fill missing values
                        open_df = pd.merge(date_range_df, opened_by_date, on='date', how='left').fillna(0)
                        close_df = pd.merge(date_range_df, closed_by_date, on='date', how='left').fillna(0)
                        
                        # Create a combined dataframe
                        combined_df = open_df.copy()
                        combined_df['closed'] = close_df['closed']
                        
                        # Calculate cumulative sum
                        combined_df['cumulative_opened'] = combined_df['opened'].cumsum()
                        combined_df['cumulative_closed'] = combined_df['closed'].cumsum()
                        
                        # Issue Open vs Closed Over Time
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=combined_df['date'], 
                            y=combined_df['cumulative_opened'],
                            mode='lines',
                            name='Opened'
                        ))
                        fig.add_trace(go.Scatter(
                            x=combined_df['date'], 
                            y=combined_df['cumulative_closed'],
                            mode='lines',
                            name='Closed'
                        ))
                        
                        # Add trendlines
                        add_trendline(fig, combined_df, 'date', 'cumulative_opened', 
                                    line_name="Open Trend", color="#FF5733")
                        add_trendline(fig, combined_df, 'date', 'cumulative_closed', 
                                    line_name="Close Trend", color="#33FF57")
                        
                        fig.update_layout(
                            title='Cumulative Issues Opened vs Closed',
                            xaxis_title='Date',
                            yaxis_title='Count'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add backlog trend analysis
                        open_direction, open_percent = calculate_trend_metrics(
                            combined_df, 'date', 'cumulative_opened')
                        close_direction, close_percent = calculate_trend_metrics(
                            combined_df, 'date', 'cumulative_closed')
                        
                        if open_direction != "Not enough data" and close_direction != "Not enough data":
                            if open_percent > close_percent:
                                st.warning("**Backlog Trend:** Issues are being opened faster than they're being closed. "
                                        f"The backlog is growing at a rate of {open_percent-close_percent:.1f}%.")
                            elif close_percent > open_percent:
                                st.success("**Backlog Trend:** Issues are being closed faster than they're being opened. "
                                        f"The backlog is shrinking at a rate of {close_percent-open_percent:.1f}%.")
                            else:
                                st.info("**Backlog Trend:** The issue backlog is stable.")
            else:
                st.warning("No issue data found for the selected repositories and date range. Try adjusting your filters.")