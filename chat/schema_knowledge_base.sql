-- 知识库增强表结构
-- 运行此脚本以创建/更新知识库相关表

USE arc_logi_chat;

-- 知识库主表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    username VARCHAR(50) NOT NULL,
    is_public TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识条目表（增强版）
CREATE TABLE IF NOT EXISTS knowledge_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    knowledge_base_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type ENUM('text', 'qa', 'concept', 'procedure') DEFAULT 'text',
    category_id INT DEFAULT NULL,
    content_hash VARCHAR(32) DEFAULT NULL,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    INDEX idx_kb (knowledge_base_id),
    INDEX idx_type (type),
    INDEX idx_updated (updated_at),
    INDEX idx_hash (content_hash),
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识标签表
CREATE TABLE IF NOT EXISTS knowledge_tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(20) DEFAULT '#1890ff',
    usage_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识分类表
CREATE TABLE IF NOT EXISTS knowledge_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INT DEFAULT NULL,
    knowledge_base_id INT NOT NULL,
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_kb (knowledge_base_id),
    INDEX idx_parent (parent_id),
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4_unicode_ci;

-- 知识关系表
CREATE TABLE IF NOT EXISTS knowledge_relation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    knowledge_base_id INT NOT NULL,
    source_item_id INT,
    target_item_id INT NOT NULL,
    relation_type ENUM('related', 'parent', 'child', 'similar', 'tag', 'reference') DEFAULT 'related',
    weight FLOAT DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source_item_id),
    INDEX idx_target (target_item_id),
    INDEX idx_type (relation_type),
    INDEX idx_kb (knowledge_base_id),
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识版本表
CREATE TABLE IF NOT EXISTS knowledge_version (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    version_number INT NOT NULL,
    title VARCHAR(200),
    content TEXT,
    metadata JSON,
    change_summary VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    INDEX idx_item (item_id),
    INDEX idx_version (version_number),
    FOREIGN KEY (item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识历史表
CREATE TABLE IF NOT EXISTS knowledge_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    knowledge_base_id INT,
    action VARCHAR(20) NOT NULL,
    action_details JSON,
    old_data JSON,
    new_data JSON,
    username VARCHAR(50),
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item (item_id),
    INDEX idx_kb (knowledge_base_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识评论表
CREATE TABLE IF NOT EXISTS knowledge_comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    parent_id INT DEFAULT NULL,
    like_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_item (item_id),
    INDEX idx_parent (parent_id),
    FOREIGN KEY (item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识收藏表
CREATE TABLE IF NOT EXISTS knowledge_favorite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_item (username, item_id),
    FOREIGN KEY (item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识访问日志表
CREATE TABLE IF NOT EXISTS knowledge_access_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    username VARCHAR(50),
    access_type ENUM('view', 'edit', 'copy', 'share') DEFAULT 'view',
    duration_seconds INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item (item_id),
    INDEX idx_user (username),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 全文搜索索引（如果使用MySQL 5.7+）
-- ALTER TABLE knowledge_item ADD FULLTEXT INDEX ft_title_content (title, content);

-- 插入一些默认标签
INSERT IGNORE INTO knowledge_tag (name, color) VALUES 
    ('技术', '#1890ff'),
    ('产品', '#52c41a'),
    ('运营', '#faad14'),
    ('设计', '#f5222d'),
    ('管理', '#722ed1');
