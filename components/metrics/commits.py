"""
Commit metrics component
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models import Commit
from utils.data_processing import queryset_to_dataframe, create_time_series_chart, add_trendline

@st.cache_data(ttl=600)
def get_commit_data(selected_repos, start_date, end_date):
    """Get commit data with caching"""
    if selected_repos:
        query = Commit.objects(
            repo__in=selected_repos,
            committed_at__gte=start_date,
            committed_at__lte=end_date
        )
    else:
        query = Commit.objects(
            committed_at__gte=start_date,
            committed_at__lte=end_date
        )
    
    return queryset_to_dataframe(query)

def render_commit_metrics(selected_repos, start_date, end_date):
    """
    Render commit metrics
    
    Args:
        selected_repos: List of selected repository names
        start_date: Start date for data filtering
        end_date: End date for data filtering
    """
    st.header("Commit Activity")
    
    # Get commit data
    commit_df = get_commit_data(selected_repos, start_date, end_date)
    
    if not commit_df.empty:
        # Commit Overview Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_commits = len(commit_df)
            st.metric("Total Commits", total_commits)
            
        with col2:
            total_additions = commit_df['additions'].sum()
            st.metric("Lines Added", f"{total_additions:,}")
            
        with col3:
            total_deletions = commit_df['deletions'].sum()
            st.metric("Lines Deleted", f"{total_deletions:,}")
        
        with col4:
            net_lines = total_additions - total_deletions
            st.metric("Net Line Changes", f"{net_lines:,}")
        
        # Commit Activity Analysis
        st.subheader("Commit Activity Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Extract dates
            commit_df['commit_date'] = pd.to_datetime(commit_df['committed_at']).dt.date
            commits_by_date = commit_df.groupby('commit_date').size().reset_index(name='commit_count')
            commits_by_date['commit_date'] = pd.to_datetime(commits_by_date['commit_date'])
            
            # Fill in missing dates with zero counts
            date_range_df = pd.DataFrame({
                'commit_date': pd.date_range(start=start_date, end=end_date)
            })
            complete_df = pd.merge(date_range_df, commits_by_date, on='commit_date', how='left').fillna(0)
            
            # Commit Volume Over Time with trendline
            fig = create_time_series_chart(
                complete_df, 
                'commit_date', 
                'commit_count',
                'Commit Volume Over Time',
                'Commits'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Group by date and sum additions/deletions
            code_churn_df = commit_df.groupby('commit_date').agg({
                'additions': 'sum',
                'deletions': 'sum'
            }).reset_index()
            code_churn_df['commit_date'] = pd.to_datetime(code_churn_df['commit_date'])
            
            # Fill in missing dates
            complete_df = pd.merge(date_range_df, code_churn_df, on='commit_date', how='left').fillna(0)
            
            # Code Churn Over Time
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=complete_df['commit_date'],
                y=complete_df['additions'],
                name='Additions',
                marker_color='green'
            ))
            fig.add_trace(go.Bar(
                x=complete_df['commit_date'],
                y=-complete_df['deletions'],
                name='Deletions',
                marker_color='red'
            ))
            
            # Add net change line with trendline
            complete_df['net_change'] = complete_df['additions'] - complete_df['deletions']
            fig.add_trace(go.Scatter(
                x=complete_df['commit_date'],
                y=complete_df['net_change'],
                mode='lines',
                name='Net Change',
                line=dict(color='blue', width=2)
            ))
            
            # Add trendline for net change
            add_trendline(fig, complete_df, 'commit_date', 'net_change', 
                        line_name="Net Change Trend", color="rgba(0,0,255,0.5)")
            
            fig.update_layout(
                title='Code Churn Over Time',
                barmode='relative',
                xaxis_title='Date',
                yaxis_title='Lines of Code'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Commit Activity by Author
        st.subheader("Commit Activity by Author")
        
        # Top authors by commit count
        top_authors_df = commit_df['author'].value_counts().head(10).reset_index()
        top_authors_df.columns = ['author', 'commit_count']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top authors chart
            fig = px.bar(
                top_authors_df,
                x='author',
                y='commit_count',
                title='Top 10 Contributors by Commit Count',
                labels={'author': 'Author', 'commit_count': 'Number of Commits'},
                color='commit_count',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top authors by code churn
            author_churn = commit_df.groupby('author').agg({
                'additions': 'sum',
                'deletions': 'sum'
            }).reset_index()
            author_churn['total_churn'] = author_churn['additions'] + author_churn['deletions']
            author_churn = author_churn.sort_values('total_churn', ascending=False).head(10)
            
            fig = px.bar(
                author_churn,
                x='author',
                y=['additions', 'deletions'],
                title='Code Churn by Top 10 Contributors',
                labels={'author': 'Author', 'value': 'Lines of Code', 'variable': 'Type'},
                barmode='group',
                color_discrete_map={'additions': 'green', 'deletions': 'red'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No commit data found for the selected repositories and date range. Try adjusting your filters.")