-- 1. Users table (foundation for multi-user support)
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'America/Boise'
);

-- 2. Categories table (hierarchical structure for your categories)
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    parent_category_id INT,
    category_code VARCHAR(20),  -- e.g., "5.403"
    category_name VARCHAR(100) NOT NULL,  -- e.g., "SCM 478"
    full_path VARCHAR(255),  -- e.g., "Work/BYUI/SCM 478"
    color_hex VARCHAR(7),
    icon VARCHAR(50),
    user_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_category_path (full_path)
);

-- 3. Tasks table (your main entity)
CREATE TABLE tasks (
    task_id INT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    category_id INT,
    status ENUM('Idea', 'Open', 'Closed', 'In Progress', 'Blocked', 'Deferred') DEFAULT 'Idea',
    importance TINYINT CHECK (importance BETWEEN 1 AND 5),
    urgency TINYINT CHECK (urgency BETWEEN 1 AND 5),
    eisenhower_quadrant VARCHAR(2) GENERATED ALWAYS AS (
        CASE 
            WHEN importance >= 3 AND urgency >= 3 THEN 'Q1'
            WHEN importance >= 3 AND urgency < 3 THEN 'Q2'
            WHEN importance < 3 AND urgency >= 3 THEN 'Q3'
            ELSE 'Q4'
        END
    ) STORED,
    created_by INT NOT NULL,
    assigned_to INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    due_date DATETIME,
    completed_at DATETIME,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id),
    INDEX idx_status_user (status, assigned_to),
    INDEX idx_due_date (due_date),
    FULLTEXT idx_search (subject, description)
);

-- 4. Calendar Integration table
CREATE TABLE calendar_events (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT,
    event_type ENUM('deadline', 'milestone', 'meeting', 'reminder', 'recurring') DEFAULT 'deadline',
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME,
    all_day BOOLEAN DEFAULT FALSE,
    location VARCHAR(255),
    recurrence_rule VARCHAR(255),  -- RFC 5545 RRULE format
    external_calendar_id VARCHAR(255),  -- Google/Outlook event ID
    external_calendar_type VARCHAR(50),  -- 'google', 'outlook', 'ical'
    reminder_minutes INT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    INDEX idx_datetime (start_datetime, end_datetime)
);

-- 5. Task History/Audit table
CREATE TABLE task_history (
    history_id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'status_changed', 'completed'
    field_changed VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_task_history (task_id, timestamp)
);

-- 6. Tags table (flexible labeling system)
CREATE TABLE tags (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    tag_name VARCHAR(50) NOT NULL,
    tag_type VARCHAR(50),  -- 'context', 'project', 'skill', etc.
    user_id INT,
    UNIQUE KEY unique_tag_user (tag_name, user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 7. Task-Tags junction table
CREATE TABLE task_tags (
    task_id INT,
    tag_id INT,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

-- 8. Task Dependencies (for project management)
CREATE TABLE task_dependencies (
    dependency_id INT PRIMARY KEY AUTO_INCREMENT,
    predecessor_task_id INT NOT NULL,
    successor_task_id INT NOT NULL,
    dependency_type ENUM('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish') DEFAULT 'finish_to_start',
    lag_days INT DEFAULT 0,
    FOREIGN KEY (predecessor_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (successor_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    UNIQUE KEY unique_dependency (predecessor_task_id, successor_task_id)
);

-- 9. Attachments table
CREATE TABLE attachments (
    attachment_id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    uploaded_by INT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

-- 10. User Preferences (for future customization)
CREATE TABLE user_preferences (
    user_id INT PRIMARY KEY,
    default_view ENUM('list', 'kanban', 'calendar', 'eisenhower') DEFAULT 'list',
    items_per_page INT DEFAULT 50,
    email_notifications BOOLEAN DEFAULT TRUE,
    reminder_defaults JSON,
    theme VARCHAR(50) DEFAULT 'light',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
