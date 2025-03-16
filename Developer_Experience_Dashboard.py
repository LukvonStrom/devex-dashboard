"""
DevEx Dashboard - Main Entry Point

This is a Streamlit multi-page application for engineering teams to track
and analyze developer experience metrics across GitHub repositories and Jira projects.

Usage:
    streamlit run app.py
"""
import streamlit as st
from datetime import datetime

# Configure the main page
st.set_page_config(
    page_title="DevEx Dashboard",
    page_icon="📊",
    layout="wide"
)

# Header with current data freshness
st.title("🚀 Developer Experience Analytics Hub")

# Introduction with business value proposition
st.markdown("""
## Make data-driven engineering decisions

Track key engineering metrics, identify bottlenecks, and optimize your development workflows to enhance team productivity, 
code quality, and delivery speed. This dashboard translates development activities into business insights.
""")

# Main value proposition in columns 
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown("""
    <div style="padding: 20px; border-radius: 10px; border: 1px solid #ddd; text-align: center;">
        <h3>Why DevEx Analytics Matter</h3>
        <p>Teams with strong developer experience deliver <b>2-4x faster</b>, with <b>60% fewer defects</b>, and show <b>higher retention rates</b>.</p>
    </div>
    """, unsafe_allow_html=True)

# Dashboard pages with clear business value
st.markdown("## Analytics Dashboards")

# Create card-like layout for the different pages
col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("""
        ### 🔄 [Pull Request Metrics](/PR_Metrics)
        
        **Business Impact:** Reduce code integration delays and optimize code review processes.
        
        - Track PR cycle times and approval bottlenecks
        - Monitor code review participation across teams
        - Identify opportunities to streamline code integration
        - Set realistic delivery expectations based on historical performance
        
        [View Dashboard →](/PR_Metrics)
        """)
    
    with st.container():
        st.markdown("""
        ### 📝 [Commit Activity](/Commit_Activity)
        
        **Business Impact:** Gain visibility into code development patterns and team momentum.
        
        - Track code contribution trends over time
        - Identify periods of high and low development activity
        - Monitor code churn and potential technical debt indicators
        - Ensure consistent progress toward project milestones
        
        [View Dashboard →](/Commit_Activity)
        """)

with col2:
    with st.container():
        st.markdown("""
        ### 📊 [Issue Metrics](/Issue_Metrics)
        
        **Business Impact:** Better predict delivery timelines and manage project health.
        
        - Track issue resolution times by priority and type
        - Analyze backlog growth trends and team capacity
        - Monitor support ticket resolution efficiency
        - Identify recurring issue patterns to address root causes
        
        [View Dashboard →](/Issue_Metrics)
        """)
        
    with st.container():
        st.markdown("""
        ### 👥 [Team Insights](/Team_Insights)
        
        **Business Impact:** Optimize team structures and cross-team collaboration.
        
        - Track DORA metrics aligned with industry standards
        - Analyze team dependencies and collaboration patterns
        - Identify knowledge silos and review bottlenecks
        - Support data-driven decisions about team assignments
        
        [View Dashboard →](/Team_Insights)
        """)

# DORA metrics callout
st.info("""
### 🔍 Industry Standard: DORA Metrics

This dashboard implements metrics aligned with the DevOps Research and Assessment (DORA) framework, including:

- **Deployment Frequency** - How often your organization deploys code
- **Lead Time for Changes** - How long it takes to go from code committed to code in production

These metrics are powerful predictors of both IT performance and organizational performance.
""")

# Leadership insights section
st.markdown("## Leadership Insights")

st.markdown("""
This dashboard helps engineering leaders:

- **Remove Bottlenecks:** Identify and address process inefficiencies
- **Optimize Resources:** Make data-driven decisions about team composition and tooling
- **Set Realistic Goals:** Establish baselines and improvement targets
- **Drive Improvement:** Track the impact of process changes over time
- **Benchmark Performance:** Compare against industry standards and past performance
""")

# Data sources section
with st.expander("Data Sources & Integration"):

  col1, col2, col3 = st.columns(3)

  with col1:
      st.markdown("""
      ### GitHub
      - Repositories & Teams
      - Pull Requests
      - Code Reviews
      - Commits
      - Actions Workflows
      """)

  with col2:
      st.markdown("""
      ### Jira
      - Project Management
      - Issues & Epics
      - Sprint Data
      - Story Points
      - Resolution Times
      """)

  with col3:
      st.markdown("""
      ### CI/CD
      - GitHub Actions
      - Build Performance
      - Deployment Events
      - Pipeline Health
      """)



# Footer
st.markdown("---")

# Technical details in expander (less prominent)
# with st.expander("Technical Details & Setup"):
#     st.markdown("""
#     ### Setting Up Your Own Instance
    
#     1. Configure environment variables for your data sources in `.env`
#     2. Run `python data_collector.py --teams --repos` to collect initial data
#     3. Schedule periodic data collection with cron or similar
#     4. Run `streamlit run app.py` to start the dashboard
    
#     Data is stored in MongoDB and refreshed when running the data collector.
#     For more technical details, see the [README.md](/README.md) file.
#     """)

#     # MongoDB setup instructions
#     st.code("""
#     # Example docker-compose.yml for MongoDB
#     version: '3.8'
    
#     services:
#       mongodb:
#         image: mongo:latest
#         container_name: mongodb
#         ports:
#           - "27017:27017"
#         volumes:
#           - mongodb_data:/data/db
#         environment:
#           - MONGO_INITDB_ROOT_USERNAME=admin
#           - MONGO_INITDB_ROOT_PASSWORD=password
#         restart: unless-stopped
    
#     volumes:
#       mongodb_data:
#     """, language="yaml")
    

# Final call to action and version
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("DevEx Dashboard - Version 1.0")
with col2:
    st.caption("Built with ❤️ by DevEx Team")