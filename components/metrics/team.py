"""
Team insights metrics component

This component focuses on team performance metrics rather than individual metrics,
following DevOps Research and Assessment (DORA) framework principles.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from components.runners import get_workflow_data
from models import Issue, PullRequest
from utils.data_processing import queryset_to_dataframe
from utils.team_utils import get_team_data, augment_dataframe_with_team_info
from utils.dora_metrics import calculate_deployment_frequency, calculate_lead_time, render_deployment_frequency_chart, render_lead_time_chart, render_pr_frequency_chart
from components.metrics.pull_requests import get_pr_data

@st.cache_data(ttl=600)
def get_issue_data(selected_repos, selected_projects, start_date, end_date, closed_only=True):
    """
    Get issue data from database
    
    Args:
        selected_repos: List of selected repository names
        selected_projects: List of selected project keys
        start_date: Start date for data filtering
        end_date: End date for data filtering
        closed_only: If True, only get closed issues
        
    Returns:
        DataFrame with issue data
    """
    filter_args = {
        'closed_at__gte': start_date,
        'closed_at__lte': end_date
    } if closed_only else {
        'created_at__gte': start_date,
        'created_at__lte': end_date
    }
        
    # Apply repo filter if available
    if selected_repos:
        filter_args['repo__in'] = selected_repos
        
    # Apply project filter if available
    if selected_projects:
        filter_args['project_key__in'] = selected_projects
    
    query = Issue.objects(**filter_args)
    return queryset_to_dataframe(query)

@st.cache_data(ttl=600)
def get_pr_review_data(selected_repos, start_date, end_date):
    """
    Get PR review data including reviewer information
    
    Args:
        selected_repos: List of selected repository names
        start_date: Start date for data filtering
        end_date: End date for data filtering
        
    Returns:
        DataFrame with PR review data
    """
    # In a real implementation, you would fetch reviews with reviewer information
    # This is a placeholder that would need to be implemented based on your data model
    
    # For MongoDB, you might need to use aggregation to get this data
    filter_args = {
        'created_at__gte': start_date,
        'created_at__lte': end_date,
    }
    
    if selected_repos:
        filter_args['repo__in'] = selected_repos
    
    # Get PRs with reviews
    prs = PullRequest.objects(**filter_args)
    return queryset_to_dataframe(prs)

def render_pr_throughput(pr_df, group_by='team', title_prefix='Team'):
    """
    Render pull request throughput by team or repository
    
    Args:
        pr_df: DataFrame with PR data
        group_by: Column to group by ('team' or 'repo')
        title_prefix: Prefix for title (e.g., 'Team' or 'Repository')
        
    Returns:
        Plotly figure object
    """
    if pr_df.empty:
        return None
    
    # Count PRs by group
    counts = pr_df[group_by].value_counts().reset_index()
    counts.columns = [group_by, 'pr_count']
    unmapped_count = 0
    
    # Filter out unmapped/unassigned if they exist and there are other groups
    if len(counts) > 1:
        if "Unmapped" in counts[group_by].values:
            unmapped_count = counts[counts[group_by] == "Unmapped"]['pr_count'].values[0]
            counts = counts[counts[group_by] != "Unmapped"]
        
    # Show unmapped count if applicable
    if unmapped_count > 0 and group_by == 'team':
        st.caption(f"Note: {unmapped_count} PRs couldn't be mapped to teams")

    
    # Create the visualization
    fig = px.bar(
        counts,
        x=group_by,
        y='pr_count',
        title=f'Pull Requests by {title_prefix}',
        labels={group_by: title_prefix, 'pr_count': 'Number of PRs'},
        color='pr_count',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)

def render_team_insights(selected_repos, start_date, end_date):
    """
    Render team insights metrics
    
    Args:
        selected_repos: List of selected repository names
        start_date: Start date for data filtering
        end_date: End date for data filtering
    """
    
    # DORA framework explanation
    st.info("""
    **Note on Team-Based Metrics:**  
    Following DevOps Research and Assessment (DORA) best practices, metrics focus on team performance 
    rather than individuals. This approach promotes collaboration, shared ownership, and collective improvement.
    """)
    
    # Get team data
    team_df = get_team_data()
    
    # Check if team data is available
    if team_df.empty:
        st.warning("""
        No team data found. Please run the data collector with the `--teams` flag to collect team information:
        ```
        python data_collector.py --teams
        ```
        Showing repository-based metrics instead of team-based metrics.
        """)
        # If no team data, we'll show repo-level metrics as fallback
        show_repo_based_metrics = True
    else:
        show_repo_based_metrics = False
    
    # Get PR data 
    pr_all_df = get_pr_data(selected_repos, start_date, end_date)
    pr_merged_df = get_pr_data(selected_repos, start_date, end_date, merged_only=True)
    
    # Fetch issue data (only supply empty list for projects to get all projects)
    issue_df = get_issue_data(selected_repos, [], start_date, end_date)
    
    if not pr_all_df.empty:
        # Add team information to dataframes if team data is available
        if not team_df.empty:
            pr_all_df = augment_dataframe_with_team_info(pr_all_df, team_df)
            
            if not pr_merged_df.empty:
                pr_merged_df = augment_dataframe_with_team_info(pr_merged_df, team_df)
                
            if not issue_df.empty and 'assignee' in issue_df.columns:
                issue_df = augment_dataframe_with_team_info(issue_df, team_df, author_field='assignee')
            
        # PR Throughput and Lead Time (DORA) metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # PR Throughput by Team/Repo
            st.subheader("PR Throughput")
            
            # Determine whether to use team or repo grouping
            group_by = 'team' if not team_df.empty and 'team' in pr_all_df.columns else 'repo'
            title_prefix = 'Team' if group_by == 'team' else 'Repository'
            
            # Get PR counts by group
            render_pr_throughput(pr_all_df, group_by, title_prefix)
            
            
        
        with col2:
            # Lead Time by Team/Repo (DORA metric)
            st.subheader("Lead Time for Changes")
            
            if not pr_merged_df.empty:
                # Calculate lead time
                pr_merged_with_lead_time = calculate_lead_time(pr_merged_df)
                
                # Determine whether to use team or repo grouping
                group_by = 'team' if not team_df.empty and 'team' in pr_merged_with_lead_time.columns else 'repo'
                title_prefix = 'Team' if group_by == 'team' else 'Repository'
                
                # Create the lead time chart
                fig = render_lead_time_chart(pr_merged_with_lead_time, group_by, title_prefix)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add interpretation of lead times
                    avg_lead_time = pr_merged_with_lead_time['lead_time_days'].mean()
                    
                    # Performance classification based on DORA research
                    if avg_lead_time < 1:
                        st.success(f"🚀 **Elite Performance**: Lead time less than one day (avg: {avg_lead_time:.2f} days)")
                    elif avg_lead_time < 7:
                        st.info(f"🔹 **High Performance**: Lead time between one day and one week (avg: {avg_lead_time:.2f} days)")
                    elif avg_lead_time < 30:
                        st.warning(f"🔸 **Medium Performance**: Lead time between one week and one month (avg: {avg_lead_time:.2f} days)")
                    else:
                        st.error(f"🔻 **Low Performance**: Lead time more than one month (avg: {avg_lead_time:.2f} days)")
            else:
                st.info("No merged PRs found in the selected timeframe.")
        
        # Team Collaboration section
        st.subheader("Team Collaboration")
        
        # Create a second set of columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Code review metrics
            render_code_review_metrics(pr_merged_df, team_df)
        
        with col2:
            # Issue resolution metrics
            render_issue_resolution_metrics(issue_df, team_df)

        # Create a third set of columns
        st.subheader("Cross-Team Review Dependencies")
        # Cross-team review dependencies
        st.info("Coming soon"
                "\nIdentify bottlenecks and dependencies between teams for better collaboration")
            
        # DORA Deployment Frequency section
        st.subheader("Deployment Frequency (DORA)")
        st.info("""
        **Deployment Frequency** is a key DORA metric that measures how often code is deployed to production.
        Higher deployment frequency is associated with high-performing engineering organizations.
        
        We present this here with two charts - PR Merge Frequency and General Deployment Frequency.
        Ideally these should be similar, but differences may indicate inefficiencies in the deployment process.
        """)

        if not pr_merged_df.empty:
            # Determine grouping and render PR frequency chart
            group_by = 'team' if not team_df.empty and 'team' in pr_merged_df.columns else 'repo'
            
            # Create the chart
            fig = render_pr_frequency_chart(pr_merged_df, group_by)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No pull request data found for the selected repositories and date range. Try adjusting your filters.")

        workflow_df = get_workflow_data(selected_repos, start_date, end_date)
        
        # Calculate deployment frequency
        deploy_freq_df = calculate_deployment_frequency(workflow_df, start_date, end_date)
        
        if not deploy_freq_df.empty:
            # Render deployment frequency chart
            fig = render_deployment_frequency_chart(deploy_freq_df, 'w_period')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Add some insights about deployment patterns
                total_deployments = deploy_freq_df['deploy_count'].sum()
                avg_weekly = total_deployments / len(deploy_freq_df['w_period'].unique())
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Deployments", f"{total_deployments}")
                with col2:
                    st.metric("Avg Weekly Deployments", f"{avg_weekly:.1f}")
                
                # Performance classification based on DORA research
                if avg_weekly >= 7:
                    st.success("📈 **Elite Performance**: Multiple deployments per day")
                elif avg_weekly >= 1:
                    st.info("🔹 **High Performance**: Between once per day and once per week")
                elif avg_weekly >= 0.25:
                    st.warning("🔸 **Medium Performance**: Between once per week and once per month")
                else:
                    st.error("🔻 **Low Performance**: Less than once per month")
        else:
            st.info("""
            No deployment workflows detected. To track deployment frequency:
            
            1. Name your deployment workflows with terms like 'deploy', 'release', or 'publish'
            2. Ensure successful completions are captured in the workflow data
            
            Alternatively, you can use PR merge frequency as a proxy for deployment frequency.
            """)
            
        

def render_code_review_metrics(pr_df, team_df):
    """
    Render code review metrics by team or repository
    
    Args:
        pr_df: DataFrame with PR data
        team_df: DataFrame with team data
    """
    if pr_df.empty:
        st.info("No merged PRs found for review analysis.")
        return
        
    # Determine whether to use team or repo grouping
    group_by = 'team' if not team_df.empty and 'team' in pr_df.columns else 'repo'
    title_prefix = 'Team' if group_by == 'team' else 'Repository'
    
    # Calculate average review count by group
    reviews_by_group = pr_df.groupby(group_by)['review_count'].mean().reset_index()
    reviews_by_group['avg_reviews'] = reviews_by_group['review_count'].round(2)
    
    # Filter out unmapped team (optional)
    if group_by == 'team' and "Unmapped" in reviews_by_group['team'].values and len(reviews_by_group) > 1:
        reviews_by_group = reviews_by_group[reviews_by_group['team'] != "Unmapped"]
    
    # Create visualization
    fig = px.bar(
        reviews_by_group,
        x=group_by,
        y='avg_reviews',
        title=f'Average Code Reviews per PR by {title_prefix}',
        labels={group_by: title_prefix, 'avg_reviews': 'Avg Reviews per PR'},
        color='avg_reviews',
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add context about code review best practices
    if reviews_by_group['avg_reviews'].mean() < 1:
        st.warning("⚠️ **Low review count detected**: Consider implementing a minimum review policy")
    elif reviews_by_group['avg_reviews'].mean() >= 2:
        st.success("✅ **Healthy review culture**: Multiple reviews per PR indicates good peer review practices")

def render_issue_resolution_metrics(issue_df, team_df):
    """
    Render issue resolution metrics by team or project
    
    Args:
        issue_df: DataFrame with issue data
        team_df: DataFrame with team data
        pr_df: DataFrame containing PR data with 'created_at' and 'merged_at' columns
    """
    if issue_df.empty:
        st.info("No issue data found in the selected timeframe.")
        return
        
    # Team-based metrics if team data is available
    if not team_df.empty and 'team' in issue_df.columns:
        # Count resolved issues by team
        resolved_by_team = issue_df['team'].value_counts().reset_index()
        resolved_by_team.columns = ['team', 'resolved_count']
        
        # Filter out unmapped team (optional)
        if "Unmapped" in resolved_by_team['team'].values and len(resolved_by_team) > 1:
            resolved_by_team = resolved_by_team[resolved_by_team['team'] != "Unmapped"]
            
        # Filter out unassigned if it exists and there are other teams
        unassigned_count = 0
        if "Unassigned" in resolved_by_team['team'].values and len(resolved_by_team) > 1:
            unassigned_count = resolved_by_team[resolved_by_team['team'] == "Unassigned"]['resolved_count'].values[0]
            resolved_by_team = resolved_by_team[resolved_by_team['team'] != "Unassigned"]
        
        
            
        # Create visualization
        fig = px.bar(
            resolved_by_team,
            x='team',
            y='resolved_count',
            title='Issues Resolved by Team',
            labels={'team': 'Team', 'resolved_count': 'Issues Resolved'},
            color='resolved_count',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Show unassigned count if applicable
        if unassigned_count > 0:
            st.warning(f"Note: {unassigned_count} issues were unassigned")
    # Project-based metrics as fallback
    elif 'project_key' in issue_df.columns:
        resolved_by_project = issue_df['project_key'].value_counts().reset_index()
        resolved_by_project.columns = ['project_key', 'resolved_count']
        
        fig = px.bar(
            resolved_by_project,
            x='project_key',
            y='resolved_count',
            title='Issues Resolved by Project',
            labels={'project_key': 'Project', 'resolved_count': 'Issues Resolved'},
            color='resolved_count',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No project data available for issue analysis.")
        

