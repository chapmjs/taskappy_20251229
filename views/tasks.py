# views/tasks.py
def show_tasks():
    st.title("📝 Task List")
    
    db = get_db()
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Idea", "Open", "In Progress", "Blocked", "Closed", "Deferred"],
            default=["Open", "In Progress"]
        )
    
    with col2:
        categories = db.execute_query("""
            SELECT category_id, category_name 
            FROM categories 
            ORDER BY category_name
        """)
        category_filter = st.selectbox(
            "Category",
            ["All"] + categories['category_name'].tolist()
        )
    
    with col3:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "High (Q1)", "Medium (Q2)", "Low (Q3/Q4)"]
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
            t.created_at,
            CASE 
                WHEN t.importance >= 3 AND t.urgency >= 3 THEN '🔴 High'
                WHEN t.importance >= 3 OR t.urgency >= 3 THEN '🟡 Medium'
                ELSE '🟢 Low'
            END as priority
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.category_id
        WHERE 1=1
    """
    
    params = []
    
    if status_filter:
        query += f" AND t.status IN ({','.join(['%s']*len(status_filter))})"
        params.extend(status_filter)
    
    if category_filter != "All":
        query += " AND c.category_name = %s"
        params.append(category_filter)
    
    if search_query:
        query += " AND (t.subject LIKE %s OR t.description LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    query += " ORDER BY t.due_date, t.importance DESC, t.urgency DESC"
    
    # Get tasks
    tasks = db.execute_query(query, params)
    
    # Display tasks
    if not tasks.empty:
        st.write(f"Found {len(tasks)} tasks")
        
        for _, task in tasks.iterrows():
            with st.expander(f"{task['priority']} {task['subject'][:100]}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {task['status']}")
                    st.write(f"**Category:** {task['category_name'] or 'None'}")
                
                with col2:
                    st.write(f"**Due Date:** {task['due_date'] or 'No due date'}")
                    st.write(f"**Created:** {task['created_at'].strftime('%Y-%m-%d')}")
                
                with col3:
                    if st.button("Edit", key=f"edit_{task['task_id']}"):
                        st.session_state.editing_task = task['task_id']
                        st.rerun()
                    
                    if st.button("Complete", key=f"complete_{task['task_id']}"):
                        complete_task(task['task_id'])
                        st.rerun()
    else:
        st.info("No tasks found matching your filters")
