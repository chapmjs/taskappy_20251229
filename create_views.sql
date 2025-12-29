-- Active tasks with full details
CREATE VIEW v_active_tasks AS
SELECT 
    t.*,
    c.category_name,
    c.full_path as category_path,
    u1.full_name as creator_name,
    u2.full_name as assignee_name,
    GROUP_CONCAT(DISTINCT tags.tag_name) as tags
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.category_id
LEFT JOIN users u1 ON t.created_by = u1.user_id
LEFT JOIN users u2 ON t.assigned_to = u2.user_id
LEFT JOIN task_tags tt ON t.task_id = tt.task_id
LEFT JOIN tags ON tt.tag_id = tags.tag_id
WHERE t.status NOT IN ('Closed', 'Deferred')
GROUP BY t.task_id;

-- Task metrics by category
CREATE VIEW v_category_metrics AS
SELECT 
    c.category_name,
    c.full_path,
    COUNT(t.task_id) as total_tasks,
    SUM(CASE WHEN t.status = 'Closed' THEN 1 ELSE 0 END) as completed_tasks,
    AVG(DATEDIFF(t.completed_at, t.created_at)) as avg_completion_days,
    SUM(t.actual_hours) as total_hours
FROM categories c
LEFT JOIN tasks t ON c.category_id = t.category_id
GROUP BY c.category_id;
