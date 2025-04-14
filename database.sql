-- Check if table exists and create if it doesn't
CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rating DECIMAL(2,1),
    reviews INT,
    photo VARCHAR(255),
    site VARCHAR(255),
    full_address TEXT,
    phone VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    formatted_hours TEXT,
    price INT,
    cuisine VARCHAR(100),
    wheelchair_accessible BOOLEAN DEFAULT FALSE,
    good_for_kids BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_cuisine ON restaurants(cuisine);
CREATE INDEX IF NOT EXISTS idx_price ON restaurants(price);
CREATE INDEX IF NOT EXISTS idx_wheelchair ON restaurants(wheelchair_accessible);
CREATE INDEX IF NOT EXISTS idx_good_for_kids ON restaurants(good_for_kids); 