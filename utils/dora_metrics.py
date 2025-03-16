"""
DevOps Research and Assessment (DORA) metrics utilities.

DORA metrics measure software delivery performance using four key metrics:
1. Deployment Frequency
2. Lead Time for Changes 
3. Change Failure Rate
4. Time to Restore Service
"""
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

def calculate_lead_time(pr_df):
    """
    Calculate lead time for changes (time from PR creation to merge)
    
    Args:
        pr_df: DataFrame containing PR data with 'created_at' and 'merged_at' columns
        
    Returns:
        DataFrame with lead_time_days column added
    """
    if pr_df.empty or 'merged_at' not in pr_df.columns or 'created_at' not in pr_df.columns:
        return pr_df
        
    # Create a copy to avoid modifying the original
    result_df = pr_df.copy()
    
    # Calculate lead time in days
    result_df['lead_time_days'] = (
        result_df['merged_at'] - result_df['created_at']
    ).dt.total_seconds() / (3600 * 24)
    
    return result_df

def calculate_deployment_frequency(workflow_df, start_date, end_date, period='W'):
    """
    Calculate deployment frequency using workflow data
    
    Args:
        workflow_df: DataFrame containing workflow data
        start_date: Starting date for analysis
        end_date: Ending date for analysis
        period: Time period for grouping ('D' for daily, 'W' for weekly, 'M' for monthly)
        
    Returns:
        DataFrame with deployment frequency by repo and time period
    """
    if workflow_df.empty:
        return pd.DataFrame()
        
    # Filter for deployment/release workflows
    deploy_keywords = ['deploy', 'release', 'publish']
    
    # Check if necessary columns exist
    if 'workflow_name' not in workflow_df.columns or 'conclusion' not in workflow_df.columns:
        return pd.DataFrame()
        
    # Filter successful deployments
    deployment_runs = workflow_df[
        (workflow_df['workflow_name'].str.lower().str.contains('|'.join(deploy_keywords)))
        & (workflow_df['conclusion'] == 'success')
    ]
    
    if deployment_runs.empty:
        return pd.DataFrame()
        
    # Extract time period
    period_col = f"{period.lower()}_period"
    deployment_runs[period_col] = pd.to_datetime(deployment_runs['created_at']).dt.to_period(period).dt.start_time
    
    # Group by period and repo
    deploy_freq = deployment_runs.groupby([period_col, 'repo']).size().reset_index(name='deploy_count')
    
    return deploy_freq

def render_lead_time_chart(lead_time_df, group_by='team', title_prefix='Team'):
    """
    Render lead time chart grouped by team or repo
    
    Args:
        lead_time_df: DataFrame with lead_time_days and group_by column
        group_by: Column to group by ('team' or 'repo')
        title_prefix: Prefix for chart title
    
    Returns:
        Plotly figure object
    """
    if lead_time_df.empty or 'lead_time_days' not in lead_time_df.columns:
        return None
        
    # Calculate average lead time by group
    lead_time_grouped = lead_time_df.groupby(group_by)['lead_time_days'].mean().reset_index()
    lead_time_grouped['lead_time_days'] = lead_time_grouped['lead_time_days'].round(2)
    
    # Create the chart
    fig = px.bar(
        lead_time_grouped,
        x=group_by,
        y='lead_time_days',
        title=f'Average Lead Time by {title_prefix} (DORA)',
        labels={group_by: title_prefix, 'lead_time_days': 'Avg Days to Merge'},
        color='lead_time_days',
        color_continuous_scale='YlOrRd_r'  # Reversed so lower (better) is green
    )
    
    return fig

def render_deployment_frequency_chart(deploy_freq_df, period_col, title=None):
    """
    Render deployment frequency chart
    
    Args:
        deploy_freq_df: DataFrame with deployment frequency data
        period_col: Column containing time period
        title: Chart title (optional)
    
    Returns:
        Plotly figure object
    """
    if deploy_freq_df.empty:
        return None
        
    if title is None:
        title = 'Deployment Frequency by Repository'
        
    # Create the chart
    fig = px.line(
        deploy_freq_df,
        x=period_col,
        y='deploy_count',
        color='repo',
        title=title,
        labels={'deploy_count': 'Deployments', period_col: 'Time Period', 'repo': 'Repository'}
    )
    
    return fig

def render_pr_frequency_chart(pr_df, group_by='team', period='W', title=None):
    """
    Render PR frequency chart as a proxy for deployment frequency
    
    Args:
        pr_df: DataFrame with PR data
        group_by: Column to group by ('team' or 'repo')
        period: Time period for grouping ('D' for daily, 'W' for weekly, 'M' for monthly)
        title: Chart title (optional)
    
    Returns:
        Plotly figure object
    """
    if pr_df.empty or 'merged_at' not in pr_df.columns:
        return None
    
    # Create a copy to avoid modifying the original
    result_df = pr_df.copy()
    
    # Extract time period
    period_col = 'week' if period == 'W' else 'period'
    result_df[period_col] = pd.to_datetime(result_df['merged_at']).dt.to_period(period).dt.start_time
    
    # Group by period and team/repo
    freq_df = result_df.groupby([period_col, group_by]).size().reset_index(name='merge_count')
    
    # Set default title if none provided
    if title is None:
        title = f'PR Merge Frequency by {group_by.capitalize()}'
    
    # Create the chart
    fig = px.line(
        freq_df,
        x=period_col,
        y='merge_count',
        color=group_by,
        title=title,
        labels={'merge_count': 'PRs Merged', period_col: 'Time Period', group_by: group_by.capitalize()}
    )
    
    return fig