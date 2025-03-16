"""
GitHub Actions runner performance component with CI/CD metrics

This component includes:
1. Runner performance metrics (pickup time, execution time)
2. Success rates by runner type and branch
3. Deployment frequency metrics (DORA)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models import WorkflowRun
from utils.data_processing import queryset_to_dataframe, create_time_series_chart, calculate_trend_metrics
from utils.dora_metrics import calculate_deployment_frequency, render_deployment_frequency_chart

@st.cache_data(ttl=600)
def get_workflow_data(selected_repos, start_date, end_date):
    """Get workflow run data with caching"""
    if selected_repos:
        query = WorkflowRun.objects(
            repo__in=selected_repos,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
    else:
        query = WorkflowRun.objects(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
    
    return queryset_to_dataframe(query)

def render_runner_performance(selected_repos, start_date, end_date):
    """
    Render GitHub Actions runner performance metrics
    
    Args:
        selected_repos: List of selected repository names
        start_date: Start date for data filtering
        end_date: End date for data filtering
    """
    st.header("GitHub Actions Runner Performance")
    
    # Get workflow data
    workflow_df = get_workflow_data(selected_repos, start_date, end_date)
    
    if not workflow_df.empty:
        # Runner Overview Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_runs = len(workflow_df)
            st.metric("Total Workflow Runs", total_runs)
            
        with col2:
            success_rate = (workflow_df['conclusion'] == 'success').mean() * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
        with col3:
            avg_pickup = workflow_df['pickup_time_seconds'].mean()
            st.metric("Avg Pickup Time (s)", f"{avg_pickup:.2f}")
        
        with col4:
            avg_exec = workflow_df['execution_time_seconds'].mean()
            st.metric("Avg Execution Time (s)", f"{avg_exec:.2f}")
        
        # Runner Pickup Time Analysis
        st.subheader("Runner Pickup Time Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pickup time by runner type
            if 'runner_type' in workflow_df.columns:
                pickup_by_runner = workflow_df.groupby('runner_type')['pickup_time_seconds'].mean().reset_index()
                
                fig = px.bar(
                    pickup_by_runner,
                    x='runner_type',
                    y='pickup_time_seconds',
                    title='Average Pickup Time by Runner Type',
                    labels={'runner_type': 'Runner Type', 'pickup_time_seconds': 'Seconds'},
                    color='pickup_time_seconds',
                    color_continuous_scale='Reds_r'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pickup Time Trend
            workflow_df['date'] = pd.to_datetime(workflow_df['created_at']).dt.date
            pickup_trend = workflow_df.groupby('date')['pickup_time_seconds'].mean().reset_index()
            pickup_trend['date'] = pd.to_datetime(pickup_trend['date'])
            
            # Create time series with trendline
            fig = create_time_series_chart(
                pickup_trend,
                'date',
                'pickup_time_seconds',
                'Runner Pickup Time Trend',
                'Seconds'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add trend analysis
            direction, percent_change = calculate_trend_metrics(
                pickup_trend, 'date', 'pickup_time_seconds')
            
            if direction != "Not enough data":
                if direction == "Increasing":
                    st.warning(f"**Trend Alert:** Runner pickup time is increasing by "
                             f"{abs(percent_change):.1f}% over the period, indicating worsening queue times.")
                elif direction == "Decreasing":
                    st.success(f"**Trend Improvement:** Runner pickup time is decreasing by "
                             f"{abs(percent_change):.1f}% over the period, indicating improving queue times.")
                else:
                    st.info("**Trend Analysis:** Runner pickup time is stable.")
        
        # Pickup Time Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Create histogram of pickup times
            fig = px.histogram(
                workflow_df,
                x='pickup_time_seconds',
                nbins=30,
                title='Distribution of Runner Pickup Times',
                labels={'pickup_time_seconds': 'Seconds'},
                color_discrete_sequence=['#3366CC'],
                marginal='box'  # Add box plot on the marginal
            )
            fig.update_layout(bargap=0.1)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'workflow_name' in workflow_df.columns:
                # Execution time by workflow type
                exec_by_workflow = workflow_df.groupby('workflow_name')['execution_time_seconds'].mean().reset_index()
                exec_by_workflow = exec_by_workflow.sort_values('execution_time_seconds', ascending=False)
                
                fig = px.bar(
                    exec_by_workflow.head(10),  # Just show top 10 for readability
                    x='workflow_name',
                    y='execution_time_seconds',
                    title='Average Execution Time by Workflow Type',
                    labels={'workflow_name': 'Workflow', 'execution_time_seconds': 'Seconds'},
                    color='execution_time_seconds',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Runner Success Rate Analysis
        st.subheader("Workflow Success Rate Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate by runner type
            if 'runner_type' in workflow_df.columns and 'conclusion' in workflow_df.columns:
                # Calculate success rate
                success_rate = workflow_df.groupby('runner_type')['conclusion'].apply(
                    lambda x: (x == 'success').mean() * 100
                ).reset_index()
                success_rate.columns = ['runner_type', 'success_rate']
                
                fig = px.bar(
                    success_rate,
                    x='runner_type',
                    y='success_rate',
                    title='Workflow Success Rate by Runner Type',
                    labels={'runner_type': 'Runner Type', 'success_rate': 'Success Rate (%)'},
                    color='success_rate',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Branch success rate for main branches
            if 'branch' in workflow_df.columns and 'conclusion' in workflow_df.columns:
                # Calculate success rate by branch
                branch_success = workflow_df.groupby('branch')['conclusion'].apply(
                    lambda x: (x == 'success').mean() * 100
                ).reset_index()
                branch_success.columns = ['branch', 'success_rate']
                
                # Count occurrences
                branch_counts = workflow_df['branch'].value_counts().reset_index()
                branch_counts.columns = ['branch', 'count']
                
                # Merge to get both success rate and count
                branch_stats = pd.merge(branch_success, branch_counts, on='branch')
                
                # Sort by count and take top branches
                branch_stats = branch_stats.sort_values('count', ascending=False).head(10)
                
                fig = px.bar(
                    branch_stats,
                    x='branch',
                    y='success_rate',
                    title='Workflow Success Rate by Branch',
                    labels={'branch': 'Branch', 'success_rate': 'Success Rate (%)'},
                    color='success_rate',
                    color_continuous_scale='RdYlGn',
                    hover_data=['count']
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
        
        # Branch Performance
        # if 'branch' in workflow_df.columns:
        #     # Top 5 branches by volume
        #     branch_counts = workflow_df['branch'].value_counts().head(5).reset_index()
        #     branch_counts.columns = ['branch', 'count']
            
        #     st.subheader(f"Runner Performance for Top {len(branch_counts)} Branches")
            
        #     # Runner pickup time by branch
        #     branch_pickup = workflow_df[workflow_df['branch'].isin(branch_counts['branch'])]
        #     branch_metrics = branch_pickup.groupby('branch').agg({
        #         'pickup_time_seconds': 'mean',
        #         'execution_time_seconds': 'mean'
        #     }).reset_index()
            
        #     col1, col2 = st.columns(2)
            
        #     with col1:
        #         # Branch pickup time
        #         fig = px.bar(
        #             branch_metrics,
        #             x='branch',
        #             y='pickup_time_seconds',
        #             title='Average Pickup Time by Branch',
        #             labels={'branch': 'Branch', 'pickup_time_seconds': 'Seconds'},
        #             color='pickup_time_seconds',
        #             color_continuous_scale='Reds'
        #         )
        #         st.plotly_chart(fig, use_container_width=True)
            
        #     with col2:
        #         # Branch execution time
        #         fig = px.bar(
        #             branch_metrics,
        #             x='branch',
        #             y='execution_time_seconds',
        #             title='Average Execution Time by Branch',
        #             labels={'branch': 'Branch', 'execution_time_seconds': 'Seconds'},
        #             color='execution_time_seconds',
        #             color_continuous_scale='Greens'
        #         )
        #         st.plotly_chart(fig, use_container_width=True)
            
        #     # Add trend comparison across branches
        #     st.subheader("Compare Branch Pickup Time Trends")
            
        #     # Get daily pickup times by branch
        #     branch_daily = workflow_df[workflow_df['branch'].isin(branch_counts['branch'])]
        #     branch_daily = branch_daily.groupby(['date', 'branch'])['pickup_time_seconds'].mean().reset_index()
            
        #     # Plot comparative trends
        #     fig = px.line(
        #         branch_daily,
        #         x='date',
        #         y='pickup_time_seconds',
        #         color='branch',
        #         title='Pickup Time Trends by Branch',
        #         labels={'date': 'Date', 'pickup_time_seconds': 'Seconds', 'branch': 'Branch'}
        #     )
        #     st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.warning("No workflow run data found for the selected repositories and date range. Try adjusting your filters.")