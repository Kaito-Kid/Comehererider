-- schema.sql for ComeHere Rider (CHR) database
-- Generated from SQLAlchemy models for MySQL/MariaDB

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_type VARCHAR(50),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    date_of_birth DATE,
    address TEXT,
    profile_picture VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    terms_accepted BOOLEAN DEFAULT FALSE,
    privacy_accepted BOOLEAN DEFAULT FALSE,
    terms_accepted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE TABLE admins (
    id INT PRIMARY KEY,
    admin_level VARCHAR(50) DEFAULT 'super_admin',
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE managers (
    id INT PRIMARY KEY,
    manager_type VARCHAR(50) NOT NULL,
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE riders (
    id INT PRIMARY KEY,
    manager_id INT,
    is_available BOOLEAN DEFAULT TRUE,
    current_latitude FLOAT,
    current_longitude FLOAT,
    last_location_update DATETIME,
    total_orders_completed INT DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,
    total_earnings FLOAT DEFAULT 0.0,
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE SET NULL
);

CREATE TABLE consumers (
    id INT PRIMARY KEY,
    manager_id INT,
    default_address TEXT,
    total_orders_placed INT DEFAULT 0,
    FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE SET NULL
);

CREATE TABLE consumer_favorites (
    consumer_id INT,
    rider_id INT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (consumer_id, rider_id),
    FOREIGN KEY (consumer_id) REFERENCES consumers(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE
);

CREATE TABLE account_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    reason TEXT,
    performed_by_id INT NOT NULL,
    suspension_until DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by_id) REFERENCES users(id)
);

CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    verified_by INT,
    verification_notes TEXT,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consumer_id INT NOT NULL,
    rider_id INT,
    store_name VARCHAR(200) NOT NULL,
    destination_address TEXT NOT NULL,
    instructions TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    rider_selection_method VARCHAR(50),
    base_commission FLOAT DEFAULT 40.0,
    extra_commission FLOAT DEFAULT 0.0,
    total_commission FLOAT,
    rider_earnings FLOAT,
    manager_earnings FLOAT,
    consumer_rating INT,
    rider_rating INT,
    consumer_feedback TEXT,
    rider_feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME,
    completed_at DATETIME,
    cancelled_at DATETIME,
    FOREIGN KEY (consumer_id) REFERENCES consumers(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE SET NULL
);

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    estimated_price FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reporter_id INT NOT NULL,
    reported_user_id INT,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),
    related_order_id INT,
    handler_id INT,
    resolution_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (related_order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (handler_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rider_id INT NOT NULL UNIQUE,
    vehicle_name VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    plate_number VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(50),
    model VARCHAR(100),
    year INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE
);
