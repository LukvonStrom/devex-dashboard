import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from bson.json_util import dumps
import json

def queryset_to_dataframe(queryset):
    """Convert MongoEngine queryset to pandas DataFrame with proper date handling"""
    if not queryset:
        return pd.DataFrame()
        
    # Convert queryset to JSON
    json_data = json.loads(dumps(queryset.as_pymongo()))
    
    # Convert JSON to DataFrame
    df = pd.DataFrame(json_data)
    
    # Handle MongoDB date fields
    date_fields = ['created_at', 'closed_at', 'merged_at', 'committed_at', 
                  'started_at', 'completed_at', 'updated_at', 'due_date']
    
    for field in date_fields:
        if field in df.columns:
            # Extract datetime strings from potential dictionary objects
            df[field] = df[field].apply(
                lambda x: x['$date'] if isinstance(x, dict) and '$date' in x 
                else (pd.NaT if pd.isna(x) else x)
            )
            # Convert to proper datetime objects
            df[field] = pd.to_datetime(df[field], errors='coerce')
    
    return df

def add_trendline(fig, df, x_col, y_col, line_name="Trend", color="red", dash="dash"):
    """Add a trendline to a Plotly figure"""
    # Only calculate trendline if we have enough data points
    if len(df) >= 2:
        # Remove NaN values
        valid_data = df[[x_col, y_col]].dropna()
        
        if len(valid_data) >= 2:
            # For datetime x-axis, convert to numeric (days since epoch)
            if pd.api.types.is_datetime64_any_dtype(valid_data[x_col]):
                # Get numeric x values (days since epoch)
                x_numeric = valid_data[x_col].map(pd.Timestamp.timestamp) / 86400
            else:
                x_numeric = valid_data[x_col]
            
            # Calculate trend line with linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                x_numeric, valid_data[y_col]
            )
            
            # Create x values for the trendline
            x_range = np.linspace(x_numeric.min(), x_numeric.max(), 100)
            
            # Calculate y values for the trendline
            y_range = slope * x_range + intercept
            
            # If x was datetime, convert back
            if pd.api.types.is_datetime64_any_dtype(valid_data[x_col]):
                x_dates = [pd.Timestamp.fromtimestamp(x * 86400) for x in x_range]
                
                # Add trendline trace
                fig.add_trace(
                    go.Scatter(
                        x=x_dates,
                        y=y_range,
                        mode='lines',
                        name=f"{line_name} (r²={r_value**2:.2f})",
                        line=dict(color=color, dash=dash),
                    )
                )
            else:
                # Add trendline trace for non-datetime x
                fig.add_trace(
                    go.Scatter(
                        x=x_range,
                        y=y_range,
                        mode='lines',
                        name=f"{line_name} (r²={r_value**2:.2f})",
                        line=dict(color=color, dash=dash),
                    )
                )
    
    return fig

def calculate_trend_metrics(df, date_col, value_col):
    """Calculate trend direction and percentage change over time"""
    if len(df) < 2:
        return "Not enough data", 0
        
    # Remove NaN values
    valid_data = df[[date_col, value_col]].dropna()
    
    if len(valid_data) < 2:
        return "Not enough data", 0
        
    # For datetime x-axis, convert to numeric (days since epoch)
    if pd.api.types.is_datetime64_any_dtype(valid_data[date_col]):
        # Get numeric x values (days since epoch)
        x_numeric = valid_data[date_col].map(pd.Timestamp.timestamp) / 86400
    else:
        x_numeric = valid_data[date_col]
    
    # Calculate trend with linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        x_numeric, valid_data[value_col]
    )
    
    # Calculate start and end points of trend line
    y_start = slope * x_numeric.min() + intercept
    y_end = slope * x_numeric.max() + intercept
    
    # Calculate percent change (if possible)
    if y_start != 0:
        percent_change = ((y_end - y_start) / y_start) * 100
    else:
        percent_change = 0
    
    # Determine trend direction
    if slope > 0:
        direction = "Increasing"
    elif slope < 0:
        direction = "Decreasing"
    else:
        direction = "Stable"
    
    return direction, percent_change

# Function to create standardized time-series charts with trendlines
def create_time_series_chart(df, date_col, value_col, title, y_label, include_trendline=True):
    """Create a standardized time series chart with optional trendline"""
    fig = px.line(
        df, 
        x=date_col, 
        y=value_col,
        title=title,
        labels={value_col: y_label, date_col: 'Date'}
    )
    
    if include_trendline:
        fig = add_trendline(fig, df, date_col, value_col)
        
        # Add trend analysis text
        direction, percent_change = calculate_trend_metrics(df, date_col, value_col)
        if direction != "Not enough data":
            if direction == "Increasing":
                trend_color = "green" if value_col in ['merged_count', 'commit_count'] else "red"
            else:
                trend_color = "red" if value_col in ['merged_count', 'commit_count'] else "green"
                
            fig.add_annotation(
                x=0.5,
                y=0,
                xref="paper",
                yref="paper",
                text=f"Trend: {direction} ({percent_change:.1f}%)",
                showarrow=False,
                font=dict(color=trend_color),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="gray",
                borderwidth=1
            )
    
    return fig