# DevEx Dashboard

![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![MongoDB](https://img.shields.io/badge/database-MongoDB-green.svg)

A comprehensive Streamlit-based dashboard for engineering teams to track, analyze, and visualize developer experience metrics across GitHub repositories and Jira projects.


## 🌟 Features

- **Pull Request Analytics**: Track lead time, review cycles, size distribution, and merge rates
- **Issue Management**: Monitor issue velocity, backlog health, and completion rates
- **Code Metrics**: Analyze commit patterns, code churn, and repository activity
- **Team Insights**: Visualize contribution patterns, review distributions, and collaboration networks
- **CI/CD Performance**: Monitor GitHub Actions workflow execution times and resource utilization
- **Customizable Views**: Filter by date ranges, repositories, teams, and more

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- GitHub API token (for repository data collection)
- Jira API credentials (for issue tracking data)

## 🚀 Quick Start with Docker

The easiest way to get started is using Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/LukvonStrom/devex-dashboard.git
   cd devex-dashboard
   ```

2. Create a `.env` file with your credentials:
   ```
   GITHUB_TOKEN=your_github_token
   JIRA_URL=your_jira_instance_url
   JIRA_USERNAME=your_jira_email
   JIRA_API_TOKEN=your_jira_api_token
   MONGO_URI=mongodb://admin:password@mongodb:27017/github_metrics?authSource=admin
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the dashboard at [http://localhost:8501](http://localhost:8501) or if you are running colima like me [http://0.0.0.0:8501](http://0.0.0.0:8501)

## 💻 Manual Installation

For local development:

1. Clone the repository:
   ```bash
   git clone https://github.com/LukvonStrom/devex-dashboard.git
   cd devex-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start MongoDB (either locally or with Docker):
   ```bash
   docker run -d --name mongodb -p 27017:27017 \
     -e MONGO_INITDB_ROOT_USERNAME=admin \
     -e MONGO_INITDB_ROOT_PASSWORD=password \
     -v mongodb_data:/data/db \
     mongo:latest
   ```

5. Set up environment variables:
   ```bash
   export GITHUB_TOKEN=your_github_token
   export JIRA_URL=your_jira_url
   export JIRA_USERNAME=your_jira_username
   export JIRA_API_TOKEN=your_jira_api_token
   export MONGO_URI=mongodb://admin:password@localhost:27017/github_metrics?authSource=admin
   ```

## 🔄 Usage

### Data Collection

Populate your database with GitHub and Jira data:

```bash
python data_collector.py
```

### Running the Dashboard

Launch the Streamlit application:

```bash
streamlit run Developer_Experience_Dashboard.py
```

### Mock Data Generation

For development or demo purposes:

```bash
python mock_data.py
```

Using Docker:

```bash
docker-compose -f docker-compose.yml -f docker-compose.mock.yml up -d
```

## 🏗️ Project Architecture

```
.
├── Developer_Experience_Dashboard.py
├── Dockerfile
├── MOCK_DATA.Dockerfile
├── README.md
├── components
│   ├── __init__.py
│   ├── __pycache__
│   ├── metrics
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   ├── commits.py
│   │   ├── issues.py
│   │   ├── pull_requests.py
│   │   └── team.py
│   ├── runners.py
│   └── sidebar.py
├── config
│   ├── __init__.py
│   ├── __pycache__
│   └── settings.py
├── data_collector.py
├── docker-compose.yml
├── mock-entrypoint.sh
├── mock_data.py
├── models.py
├── pages
│   ├── 1_🔄_PullRequest_Metrics.py
│   ├── 2_📊_Issue_Metrics.py
│   ├── 3_📝_Commit_Metrics.py
│   ├── 4_👥_Team_Insights.py
│   ├── 6_\23241_Runner_Performance.py
│   └── 9_🔍_Analytics.py
├── requirements.txt
└── utils
    ├── __init__.py
    ├── __pycache__
    ├── data_processing.py
    ├── database.py
    ├── dora_metrics.py
    └── team_utils.py
```

## 🛠️ Configuration

### GitHub Configuration

Create a [GitHub personal access token](https://github.com/settings/tokens) with the following scopes:
- `repo`
- `read:org`
- `read:user`

### Jira Configuration

Create a [Jira API token](https://id.atlassian.com/manage-profile/security/api-tokens) for your account.

### MongoDB Configuration

The default configuration works with the provided Docker setup. For production deployments, use proper authentication and security measures.

## 🧩 Extending the Dashboard

The dashboard is designed to be modular and extensible:

1. **Add new components** in the components directory
2. **Add new utility functions** in the utils directory 
3. **Configure shared settings** in settings.py
4. **Add new pages** in the pages directory for multi-page Streamlit apps

## ❓ Troubleshooting

### Common Issues

- **MongoDB Connection Failures**: Verify credentials and network connectivity
- **Data Collection Timeouts**: GitHub API rate limits may require pagination or throttling
- **Streamlit Caching Issues**: Clear cache with `st.cache_resource.clear()`

## 👥 Contributing

We welcome contributions to DevEx Dashboard!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows our style guidelines and includes appropriate tests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions, suggestions, or support, please open an issue on GitHub or contact the project maintainers.

---

*DevEx Dashboard - Empowering engineering teams with data-driven insights*

