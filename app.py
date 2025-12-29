# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from database import get_db

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

# Function Definitions
def show_dashboard():
    st.title("📊 Dashboard")
    
    db = get_db()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Total tasks
        total_tasks = db.execute_query("""
            SELECT COUNT(*) as count FROM tasks WHERE status != 'Closed'
        """)
        total_count = total_tasks.iloc[0]['count'] if not total_tasks.empty else 0
        
        # This week's tasks
        week_tasks = db.execute_query("""
            SELECT COUNT(*) as count 
            FROM tasks 
            WHERE YEARWEEK(due_date) = YEARWEEK(NOW())
            AND status != 'Closed'
        """)
        week_count = week_tasks.iloc[0]['count'] if not week_tasks.empty else 0
        
        # High priority
        high_priority = db.execute_query("""
            SELECT COUNT(*) as count 
            FROM tasks 
            WHERE importance >= 4 AND urgency >= 4
            AND status NOT IN ('Closed', 'Deferred')
        """)
        high_count = high_priority.iloc[0]['count'] if not high_priority.empty else 0
        
        # Completion rate
        completion_rate = db.execute_query("""
            SELECT 
                CASE 
                    WHEN COUNT(*) = 0 THEN 0 
                    ELSE COUNT(CASE WHEN status = 'Closed' THEN 1 END) * 100.0 / COUNT(*) 
                END as rate
            FROM tasks 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        rate = completion_rate.iloc[0]['rate'] if not completion_rate.empty else 0
        
        col1.metric("Active Tasks", total_count)
        col2.metric("This Week", week_count)
        col3.metric("High Priority", high_count)
        col4.metric("Completion Rate", f"{rate:.1f}%")
        
    except Exception as e:
        st.error(f"Error loading dashboard metrics: {e}")
    
    st.divider()
    
    # Recent tasks
    st.subheader("📅 Recent Tasks")
    recent_tasks = db.execute_query("""
        SELECT 
            t.task_id,
            t.subject,
            t.status,
            c.category_name,
            t.created_at
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.category_id
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    
    if not recent_tasks.empty:
        st.dataframe(recent_tasks, use_container_width=True, hide_index=True)
    else:
        st.info("No recent tasks found")

def show_tasks():
    st.title("📝 Task List")
    
    db = get_db()
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Idea", "Open", "In Progress", "Blocked", "Closed", "Deferred"],
            default=["Open", "In Progress", "Idea"]
        )
    
    with col2:
        try:
            categories = db.execute_query("""
                SELECT DISTINCT category_id, category_name 
                FROM categories 
                WHERE category_name IS NOT NULL
                ORDER BY category_name
            """)
            category_options = ["All"] + categories['category_name'].tolist() if not categories.empty else ["All"]
        except:
            category_options = ["All"]
            
        category_filter = st.selectbox("Category", category_options)
    
    with col3:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "High (4-5)", "Medium (2-3)", "Low (1)"]
        )
    
    with col4:
        search_query = st.text_input("🔍 Search", placeholder="Search tasks...")
    
    # Build query
    query = """
        SELECT 
            t.task_id,
            t.subject,
            t.status,
            c.category_name,
            t.importance,
            t.urgency,
            t.due_date,
            t.created_at
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.category_id
        WHERE 1=1
    """
    
    params = []
    
    if status_filter:
        placeholders = ','.join(['%s'] * len(status_filter))
        query += f" AND t.status IN ({placeholders})"
        params.extend(status_filter)
    
    if category_filter != "All":
        query += " AND c.category_name = %s"
        params.append(category_filter)
    
    if priority_filter == "High (4-5)":
        query += " AND (t.importance >= 4 OR t.urgency >= 4)"
    elif priority_filter == "Medium (2-3)":
        query += " AND ((t.importance BETWEEN 2 AND 3) OR (t.urgency BETWEEN 2 AND 3))"
    elif priority_filter == "Low (1)":
        query += " AND (t.importance = 1 OR t.urgency = 1)"
    
    if search_query:
        query += " AND t.subject LIKE %s"
        params.append(f"%{search_query}%")
    
    query += " ORDER BY t.created_at DESC"
    
    # Get tasks
    try:
        tasks = db.execute_query(query, params if params else None)
        
        if not tasks.empty:
            st.write(f"Found {len(tasks)} tasks")
            
            # Display as dataframe with actions
            for _, task in tasks.iterrows():
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        status_emoji = {
                            'Open': '🔵',
                            'In Progress': '🟡',
                            'Closed': '✅',
                            'Idea': '💡',
                            'Blocked': '🔴',
                            'Deferred': '⏸️'
                        }.get(task['status'], '⚪')
                        
                        st.write(f"{status_emoji} **{task['subject'][:100]}**")
                        st.caption(f"Category: {task['category_name'] or 'None'} | Created: {task['created_at'].strftime('%Y-%m-%d')}")
                    
                    with col2:
                        if st.button("View", key=f"view_{task['task_id']}"):
                            st.session_state.selected_task = task['task_id']
                            
                    st.divider()
        else:
            st.info("No tasks found matching your filters")
            
    except Exception as e:
        st.error(f"Error loading tasks: {e}")

def show_add_task():
    st.title("➕ Add New Task")
    
    db = get_db()
    
    with st.form("add_task_form"):
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Task Subject*", max_chars=500)
            
            # Get categories for dropdown
            try:
                categories = db.execute_query("""
                    SELECT category_id, category_name 
                    FROM categories 
                    ORDER BY category_name
                """)
                category_options = categories.set_index('category_id')['category_name'].to_dict() if not categories.empty else {}
            except:
                category_options = {}
            
            category_id = st.selectbox(
                "Category",
                options=[None] + list(category_options.keys()),
                format_func=lambda x: "No Category" if x is None else category_options.get(x, "Unknown")
            )
        
        with col2:
            status = st.selectbox(
                "Status",
                ["Idea", "Open", "In Progress", "Blocked", "Deferred"],
                index=1  # Default to "Open"
            )
            
            due_date = st.date_input("Due Date", value=None)
        
        # Priority
        col3, col4 = st.columns(2)
        
        with col3:
            importance = st.slider("Importance", 1, 5, 3)
        
        with col4:
            urgency = st.slider("Urgency", 1, 5, 3)
        
        # Description
        description = st.text_area("Description", height=100)
        
        # Submit button
        submitted = st.form_submit_button("Add Task", type="primary", use_container_width=True)
        
        if submitted:
            if not subject:
                st.error("Please enter a task subject")
            else:
                try:
                    # Insert the task
                    query = """
                    INSERT INTO tasks 
                    (subject, description, category_id, status, importance, urgency, 
                     created_by, due_date, assigned_to) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    task_id = db.execute_update(
                        query,
                        (subject, description, category_id, status, importance, urgency,
                         st.session_state.user_id, due_date, st.session_state.user_id)
                    )
                    
                    st.success(f"Task added successfully! (ID: {task_id})")
                    
                    # Clear form
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error adding task: {e}")

def show_categories():
    st.title("📁 Categories")
    
    db = get_db()
    
    # Display categories
    try:
        categories = db.execute_query("""
            SELECT 
                c.category_id,
                c.category_name,
                c.category_code,
                c.full_path,
                COUNT(t.task_id) as task_count
            FROM categories c
            LEFT JOIN tasks t ON c.category_id = t.category_id
            GROUP BY c.category_id
            ORDER BY c.full_path
        """)
        
        if not categories.empty:
            st.dataframe(
                categories[['category_name', 'category_code', 'task_count']], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No categories found")
            
    except Exception as e:
        st.error(f"Error loading categories: {e}")
    
    # Add new category
    st.divider()
    st.subheader("Add New Category")
    
    with st.form("add_category_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_category_name = st.text_input("Category Name*")
        
        with col2:
            new_category_code = st.text_input("Category Code (optional)")
        
        if st.form_submit_button("Add Category"):
            if new_category_name:
                try:
                    query = """
                    INSERT INTO categories (category_name, category_code, user_id) 
                    VALUES (%s, %s, %s)
                    """
                    db.execute_update(query, (new_category_name, new_category_code, st.session_state.user_id))
                    st.success("Category added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding category: {e}")
            else:
                st.error("Please enter a category name")

def show_analytics():
    st.title("📈 Analytics")
    
    db = get_db()
    
    # Task distribution by status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Task Status Distribution")
        status_data = db.execute_query("""
            SELECT status, COUNT(*) as count 
            FROM tasks 
            GROUP BY status
        """)
        
        if not status_data.empty:
            fig = px.pie(status_data, values='count', names='status')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Tasks by Category")
        category_data = db.execute_query("""
            SELECT c.category_name, COUNT(t.task_id) as count 
            FROM categories c
            LEFT JOIN tasks t ON c.category_id = t.category_id
            GROUP BY c.category_id
            HAVING count > 0
            ORDER BY count DESC
            LIMIT 10
        """)
        
        if not category_data.empty:
            fig = px.bar(category_data, x='count', y='category_name', orientation='h')
            st.plotly_chart(fig, use_container_width=True)

def show_settings():
    st.title("⚙️ Settings")
    
    st.info("Settings page - Coming soon!")
    
    # You can add user preferences, theme settings, etc. here

# Sidebar
with st.sidebar:
    st.title("📋 Task Manager")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Tasks", "Add Task", "Categories", "Analytics", "Settings"],
        icons=["speedometer2", "list-task", "plus-circle", "folder", "graph-up", "gear"],
        default_index=0,
    )

# Main content router
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
