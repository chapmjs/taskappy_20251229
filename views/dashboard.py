# views/dashboard.py
def show_dashboard():
    st.title("📊 Dashboard")
    
    db = get_db()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total tasks
    total_tasks = db.execute_query("""
        SELECT COUNT(*) as count FROM tasks WHERE status != 'Closed'
    """).iloc[0]['count']
    
    # This week's tasks
    week_tasks = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE YEARWEEK(due_date) = YEARWEEK(NOW())
        AND status != 'Closed'
    """).iloc[0]['count']
    
    # High priority
    high_priority = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE importance >= 4 AND urgency >= 4
        AND status NOT IN ('Closed', 'Deferred')
    """).iloc[0]['count']
    
    # Completion rate
    completion_rate = db.execute_query("""
        SELECT 
            COUNT(CASE WHEN status = 'Closed' THEN 1 END) * 100.0 / COUNT(*) as rate
        FROM tasks 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """).iloc[0]['rate']
    
    col1.metric("Active Tasks", total_tasks)
    col2.metric("This Week", week_tasks)
    col3.metric("High Priority", high_priority)
    col4.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    st.divider()
    
    # Eisenhower Matrix
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Eisenhower Matrix")
        
        matrix_data = db.execute_query("""
            SELECT 
                CASE 
                    WHEN importance >= 3 AND urgency >= 3 THEN 'Do First (Important & Urgent)'
                    WHEN importance >= 3 AND urgency < 3 THEN 'Schedule (Important, Not Urgent)'
                    WHEN importance < 3 AND urgency >= 3 THEN 'Delegate (Urgent, Not Important)'
                    ELSE 'Eliminate (Not Important or Urgent)'
                END as quadrant,
                COUNT(*) as count,
                GROUP_CONCAT(subject SEPARATOR '|||') as tasks
            FROM tasks
            WHERE status NOT IN ('Closed', 'Deferred')
            AND importance IS NOT NULL 
            AND urgency IS NOT NULL
            GROUP BY quadrant
        """)
        
        # Create matrix visualization
        fig = go.Figure()
        
        # Define quadrant positions and colors
        quadrants = {
            'Do First (Important & Urgent)': {'x': 1, 'y': 1, 'color': '#FF6B6B', 'size': 40},
            'Schedule (Important, Not Urgent)': {'x': 0, 'y': 1, 'color': '#4ECDC4', 'size': 35},
            'Delegate (Urgent, Not Important)': {'x': 1, 'y': 0, 'color': '#FFD93D', 'size': 30},
            'Eliminate (Not Important or Urgent)': {'x': 0, 'y': 0, 'color': '#95A5A6', 'size': 25}
        }
        
        for _, row in matrix_data.iterrows():
            quad = quadrants.get(row['quadrant'], {'x': 0, 'y': 0, 'color': 'gray', 'size': 20})
            
            # Get first 3 tasks for hover text
            tasks = row['tasks'].split('|||')[:3] if pd.notna(row['tasks']) else []
            hover_text = f"{row['quadrant']}<br>Count: {row['count']}<br><br>"
            hover_text += "<br>".join([f"• {t[:50]}..." if len(t) > 50 else f"• {t}" for t in tasks])
            
            fig.add_trace(go.Scatter(
                x=[quad['x']], 
                y=[quad['y']],
                mode='markers+text',
                marker=dict(size=quad['size'] * row['count']**0.5, color=quad['color'], opacity=0.6),
                text=row['count'],
                textposition='middle center',
                textfont=dict(size=14, color='white', family='Arial Black'),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
        
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 1.5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 1.5]),
            height=400,
            hovermode='closest',
            annotations=[
                dict(x=0.5, y=1.5, text="<b>IMPORTANT</b>", showarrow=False, font=dict(size=12)),
                dict(x=0.5, y=-0.5, text="<b>NOT IMPORTANT</b>", showarrow=False, font=dict(size=12)),
                dict(x=-0.5, y=0.5, text="<b>NOT<br>URGENT</b>", showarrow=False, font=dict(size=10)),
                dict(x=1.5, y=0.5, text="<b>URGENT</b>", showarrow=False, font=dict(size=10)),
            ]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Recent Activity")
        recent_activity = db.execute_query("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as created,
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        for _, row in recent_activity.iterrows():
            st.write(f"**{row['date']}**")
            st.caption(f"Created: {row['created']} | Completed: {row['completed']}")
            st.divider()
