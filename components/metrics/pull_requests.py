"""
Pull Request metrics component
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from models import PullRequest
from utils.data_processing import queryset_to_dataframe, create_time_series_chart, calculate_trend_metrics
from config.settings import PR_SIZE_BINS, PR_SIZE_LABELS

@st.cache_data(ttl=600)
def get_pr_data(selected_repos, start_date, end_date, merged_only=False):
    """Get PR data with caching"""
    filter_args = {
        'created_at__gte': start_date,
        'created_at__lte': end_date
    }
    
    if merged_only:
        filter_args['merged_at__ne'] = None
        
    if selected_repos:
        filter_args['repo__in'] = selected_repos
        
    query = PullRequest.objects(**filter_args)
    return queryset_to_dataframe(query)

def render_pr_metrics(selected_repos, start_date, end_date):
    """
    Render pull request metrics
    
    Args:
        selected_repos: List of selected repository names
        start_date: Start date for data filtering
        end_date: End date for data filtering
    """
    st.header("Pull Request Metrics")
    
    # Get PR data
    pr_merged_df = get_pr_data(selected_repos, start_date, end_date, merged_only=True)
    pr_all_df = get_pr_data(selected_repos, start_date, end_date)
    
    # PR Overview Metrics
    if not pr_all_df.empty:
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_prs = len(pr_all_df)
            st.metric("Total PRs", total_prs)
            
        with col2:
            merged_prs = pr_all_df['merged_at'].notna().sum()
            merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0
            st.metric("Merge Rate", f"{merge_rate:.1f}%")
            
        with col3:
            if not pr_merged_df.empty:
                pr_merged_df['lead_time_days'] = (
                    pr_merged_df['merged_at'] - 
                    pr_merged_df['created_at']
                ).dt.total_seconds() / (60 * 60 * 24)
                avg_lead_time = pr_merged_df['lead_time_days'].mean()
                st.metric("Avg Lead Time (days)", f"{avg_lead_time:.2f}")
            else:
                st.metric("Avg Lead Time (days)", "N/A")
        
        with col4:
            if not pr_merged_df.empty:
                avg_reviews = pr_merged_df['review_count'].mean()
                st.metric("Avg Reviews per PR", f"{avg_reviews:.2f}")
            else:
                st.metric("Avg Reviews per PR", "N/A")
    
        # PR Lead Time Analysis
        if not pr_merged_df.empty:
            st.subheader("PR Lead Time Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # PR Lead Time by Repo
                fig = px.box(
                    pr_merged_df, 
                    x='repo', 
                    y='lead_time_days',
                    title='PR Lead Time by Repository',
                    labels={'lead_time_days': 'Days', 'repo': 'Repository'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # PR Throughput Analysis
                # Convert to datetime and extract the date
                pr_merged_df['merge_date'] = pd.to_datetime(pr_merged_df['merged_at']).dt.date
                
                # Group by merge date and count
                pr_throughput_df = pr_merged_df.groupby('merge_date').size().reset_index(name='merged_count')
                pr_throughput_df['merge_date'] = pd.to_datetime(pr_throughput_df['merge_date'])
                
                # Fill in missing dates with zero counts
                date_range_df = pd.DataFrame({
                    'merge_date': pd.date_range(start=start_date, end=end_date)
                })
                complete_df = pd.merge(date_range_df, pr_throughput_df, on='merge_date', how='left').fillna(0)
                
                # PR Throughput Over Time with trendline
                fig = create_time_series_chart(
                    complete_df, 
                    'merge_date', 
                    'merged_count',
                    'PR Throughput Over Time',
                    'PRs Merged'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Add trend analysis
                direction, percent_change = calculate_trend_metrics(
                    complete_df, 'merge_date', 'merged_count')
                
                if direction != "Not enough data":
                    if direction == "Increasing":
                        st.success(f"**Trend Analysis:** PR throughput is {direction.lower()}. " 
                                f"Increased by {abs(percent_change):.1f}% over the selected time period.")
                    elif direction == "Decreasing":
                        st.warning(f"**Trend Analysis:** PR throughput is {direction.lower()}. " 
                                f"Decreased by {abs(percent_change):.1f}% over the selected time period.")
                    else:
                        st.info(f"**Trend Analysis:** PR throughput is stable.")
        else:
            st.info("No merged PRs found in the selected date range. Lead time analysis is not available.")
        
        # PR Size and Review Analysis
        st.subheader("PR Size and Review Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Categorize PR sizes
            pr_all_df['total_changes'] = pr_all_df['additions'] + pr_all_df['deletions']
            pr_all_df['size_category'] = pd.cut(
                pr_all_df['total_changes'],
                bins=PR_SIZE_BINS,
                labels=PR_SIZE_LABELS
            )
            
            size_counts = pr_all_df['size_category'].value_counts().reset_index()
            size_counts.columns = ['size_category', 'pr_count']
            
            # Reorder categories for proper display
            size_counts['size_category'] = pd.Categorical(
                size_counts['size_category'], 
                categories=PR_SIZE_LABELS, 
                ordered=True
            )
            size_counts = size_counts.sort_values('size_category')
            
            # PR Size Distribution
            fig = px.pie(
                size_counts, 
                values='pr_count', 
                names='size_category',
                title='PR Size Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not pr_merged_df.empty:
                # Group by review count
                review_counts = pr_merged_df['review_count'].value_counts().reset_index()
                review_counts.columns = ['review_count', 'pr_count']
                review_counts = review_counts.sort_values('review_count')
                
                # PR Review Count Distribution
                fig = px.bar(
                    review_counts, 
                    x='review_count', 
                    y='pr_count',
                    title='PR Review Count Distribution',
                    labels={'review_count': 'Number of Reviews', 'pr_count': 'Count of PRs'},
                    color_discrete_sequence=['#3366CC']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No merged PRs found. Review count distribution is not available.")
    else:
        st.warning("No pull request data found for the selected repositories and date range. Try adjusting your filters.")