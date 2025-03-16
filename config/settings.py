"""
Configuration settings for the dashboard
"""

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017/github_metrics"

# Dashboard settings
DEFAULT_TIMEFRAME = "30d"
TIMEFRAMES = {
    "2w": {"days": 14, "label": "2 Weeks"},
    "4w": {"days": 28, "label": "4 Weeks"},
    "30d": {"days": 30, "label": "30 Days"},
    "90d": {"days": 90, "label": "90 Days"}
}

# Chart colors
CHART_COLORS = {
    "success": "#33CC33",
    "warning": "#FF9933",
    "danger": "#CC3333",
    "info": "#3366CC",
    "primary": "#9966CC"
}

# PR Size categories
PR_SIZE_BINS = [0, 50, 200, 500, 1000, float('inf')]
PR_SIZE_LABELS = ['XS (< 50)', 'S (50-199)', 'M (200-499)', 'L (500-999)', 'XL (1000+)']

# Jira Priority order
PRIORITY_ORDER = {
    'Highest': 1,
    'High': 2,
    'Medium': 3,
    'Low': 4,
    'Lowest': 5
}