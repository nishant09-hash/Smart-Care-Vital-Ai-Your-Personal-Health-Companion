CREATE TABLE IF NOT EXISTS user_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    goal_slug VARCHAR(40) NOT NULL,
    target_date DATE NOT NULL,
    weekly_target VARCHAR(120) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_goal_slug (goal_slug)
);
