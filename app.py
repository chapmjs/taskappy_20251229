# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime, timedelta
from database import get_db
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Task Management System",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1  # Default user for now

# Sidebar navigation
with st.sidebar:
    st.title("📋 Task Manager")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Tasks", "Add Task", "Categories", "Analytics", "Settings"],
        icons=["speedometer2", "list-task", "plus-circle", "folder", "graph-up", "gear"],
        default_index=0,
    )
    
    # Quick stats
    st.divider()
    db = get_db()
    
    # Today's tasks
    today_tasks = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE DATE(due_date) = CURDATE() 
        AND status NOT IN ('Closed', 'Deferred')
    """)
    
    # Overdue tasks
    overdue_tasks = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE due_date < NOW() 
        AND status NOT IN ('Closed', 'Deferred')
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Today", today_tasks.iloc[0]['count'])
    with col2:
        st.metric("Overdue", overdue_tasks.iloc[0]['count'])

# Main content area
if selected == "Dashboard":
    show_dashboard()
elif selected == "Tasks":
    show_tasks()
elif selected == "Add Task":
    show_add_task()
elif selected == "Categories":
    show_categories()
elif selected == "Analytics":
    show_analytics()
elif selected == "Settings":
    show_settings()
