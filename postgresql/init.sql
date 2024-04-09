-- Создание таблицы
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    full_name VARCHAR(100),
    email VARCHAR(100),
    hashed_password VARCHAR(100),
    disabled BOOLEAN
);

-- Вставка данных
INSERT INTO users (username, full_name, email, hashed_password, disabled) VALUES 
('admin@creep.com', 'Admin', 'admin@creep.com', '$2b$12$6zN3HJIxgg6Xe1jpjTzQj.0Pc431KF2XIflxNSfU6ByLM9OIQ9kBi', 'FALSE'),
('creep@creep.com', 'Creep', 'Creep@creep.com', '$2b$12$6zN3HJIxgg6Xe1jpjTzQj.0Pc431KF2XIflxNSfU6ByLM9OIQ9kBi', 'FALSE'),
('oldsysadmin@creep.com', 'oldsysadmin', 'oldsysadmin@creep.com', '$2b$12$6zN3HJIxgg6Xe1jpjTzQj.0Pc431KF2XIflxNSfU6ByLM9OIQ9kBi', 'TRUE');