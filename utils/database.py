import os
import streamlit as st
import mongoengine as me

@st.cache_resource
def get_database_connection():
    """Connect to MongoDB and cache the connection"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:password@0.0.0.0:27017/github_metrics?authSource=admin")
    print(f"Connecting to MongoDB")
    
    # Check if we already have a connection and disconnect if needed
    try:
        me.disconnect()  # Disconnect any existing connections
    except:
        pass
        
    # Create a new connection with a unique alias
    return me.connect(host=mongo_uri)
