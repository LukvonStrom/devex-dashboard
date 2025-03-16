"""
Team-related utilities for processing and analyzing team data
"""
import pandas as pd
import streamlit as st
import logging
from models import Team
from utils.data_processing import queryset_to_dataframe

# Global cache for team member mapping
_TEAM_MEMBER_CACHE = None

@st.cache_data(ttl=600)
def get_team_data():
    """Get team data from database"""
    return queryset_to_dataframe(Team.objects())

def get_member_team_mapping(force_refresh=False):
    """
    Get mapping of members to teams
    
    Args:
        force_refresh: If True, ignore cache and rebuild mapping
        
    Returns:
        Dictionary mapping authors to their team names
    """
    global _TEAM_MEMBER_CACHE
    
    # Return cached mapping if available and not forcing refresh
    if _TEAM_MEMBER_CACHE is not None and not force_refresh:
        return _TEAM_MEMBER_CACHE
    
    # Create new mapping
    mapping = {}
    team_df = get_team_data()
    
    if team_df.empty:
        logging.warning("No team data found in database")
        return mapping
    
    for _, team in team_df.iterrows():
        if 'members' in team and isinstance(team['members'], list):
            team_name = team['name']
            for member in team['members']:
                if member in mapping:
                    logging.info(f"Member {member} belongs to multiple teams. Using {team_name} instead of {mapping[member]}")
                mapping[member] = team_name
    
    # Cache the mapping
    _TEAM_MEMBER_CACHE = mapping
    return mapping

def augment_dataframe_with_team_info(df, team_df=None, author_field='author', default_team='Other'):
    """
    Add team column to DataFrame based on author field
    
    Args:
        df: DataFrame to augment with team info
        team_df: DataFrame with team data (optional)
        author_field: Column name containing author usernames
        default_team: Team name to use for unmapped authors (instead of "Unmapped")
        
    Returns:
        DataFrame with added 'team' column
    """
    if df.empty or author_field not in df.columns:
        return df
    
    # Copy dataframe to avoid modifying the original
    result_df = df.copy()
    
    # Get mapping and add team column
    mapping = get_member_team_mapping()
    
    # Check if we have team mapping data
    if not mapping:
        # No team data available, just use default team for everyone
        result_df['team'] = result_df[author_field].apply(
            lambda x: default_team if pd.notna(x) else "Unassigned"
        )
        return result_df
    
    # Create a set of all authors for efficient lookup
    all_authors = set(df[author_field].dropna().unique())
    mapped_authors = set(mapping.keys())
    
    # Check for unmapped authors
    unmapped_authors = all_authors - mapped_authors
    
    # Log if we have unmapped authors
    unmapped_count = len(unmapped_authors)
    if unmapped_count > 0:
        # Only log first 5 unmapped authors to avoid spam
        sample_unmapped = list(unmapped_authors)[:5]
        logging.warning(f"Found {unmapped_count} authors not mapped to any team. Examples: {sample_unmapped}")
        
        # If more than 10% of authors are unmapped, try refreshing the team cache
        if unmapped_count > len(all_authors) * 0.1:
            logging.info("Refreshing team mapping cache due to high number of unmapped authors")
            mapping = get_member_team_mapping(force_refresh=True)
    
    # Map authors to teams, using default_team instead of "Unmapped"
    result_df['team'] = result_df[author_field].map(
        lambda x: mapping.get(x, default_team) if pd.notna(x) else "Unassigned"
    )
    
    return result_df

def map_authors_to_teams(author_list, team_df=None):
    """
    Get team mapping for a list of authors (kept for backward compatibility)
    
    Args:
        author_list: List of author usernames
        team_df: DataFrame with team data (not used)
        
    Returns:
        Dictionary mapping authors to their team names with default set to "Other" instead of "Unmapped"
    """
    # Get the complete mapping
    mapping = get_member_team_mapping()
    
    # Create a new mapping with filtered authors and using "Other" as default
    return {author: mapping.get(author, "Other") for author in author_list}