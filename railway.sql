use railway;



-- HOSPITAL FINDER - DATABASE SCHEMA
-- Database: MySQL




-- TABLE 1: HOSPITALS
-- Managed by Admin (Add / Edit / Delete)
CREATE TABLE hospitals (
    hospital_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    address       TEXT NOT NULL,
    city          VARCHAR(100) NOT NULL,
    area          VARCHAR(100),
    latitude      DECIMAL(10, 8) NOT NULL,
    longitude     DECIMAL(11, 8) NOT NULL,
    type          VARCHAR(50) NOT NULL,
    specialties   TEXT,
    emergency     VARCHAR(5) DEFAULT 'No',
    phone         VARCHAR(20),
    rating        DECIMAL(2,1) DEFAULT 0.0,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- TABLE 2: USERS
-- Registered users of the application
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    phone         VARCHAR(20) NOT NULL,
    password      VARCHAR(255) NOT NULL,
    city          VARCHAR(100) NOT NULL,
    area          VARCHAR(100) NOT NULL,
    address       TEXT NOT NULL,
    pincode       VARCHAR(10) NOT NULL,
    latitude      DECIMAL(10, 8),
    longitude     DECIMAL(11, 8),
    is_active     TINYINT DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- TABLE 3: ADMINS
-- Admin who manages hospital data
CREATE TABLE admins (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password      VARCHAR(255) NOT NULL,
    is_active     TINYINT DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);




-- TABLE 4: SAVED HOSPITALS
-- Hospitals bookmarked by logged in users
CREATE TABLE saved_hospitals (
    save_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    hospital_id   INT NOT NULL,
    saved_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);


-- TABLE 5: REVIEWS
-- Ratings and feedback by logged in users
CREATE TABLE reviews (
    review_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    hospital_id     INT NOT NULL,
    rating          DECIMAL(2,1) NOT NULL,
    cleanliness     INT,
    waiting_time    INT,
    service_quality INT,
    comment         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
);


-- ================================================
-- DEFAULT ADMIN ACCOUNT
-- ================================================
INSERT INTO admins (name, email, password)
VALUES ('navaa', 'healpoint@gmail.com', '11012006');


INSERT INTO hospitals (name, address, city, area, latitude, longitude, type, specialties, emergency, phone, rating)
VALUES
(
    'Apollo Hospitals',
    '21 Greams Lane, Off Greams Road',
    'Chennai',
    'Greams Road',
    13.05960,
    80.24720,
    'Specialty',
    'Cardiology|Neurology|Oncology|Orthopedics',
    'Yes',
    '044-28293333',
    4.7
),
(
    'Christian Medical College',
    'Ida Scudder Road',
    'Vellore',
    'Scudder Road',
    12.92410,
    79.13530,
    'Specialty',
    'Cardiology|Neurology|Oncology|Transplant|Orthopedics',
    'Yes',
    '0416-2281000',
    4.9
),
(
    'PSG Hospitals',
    'Avinashi Road, Peelamedu',
    'Coimbatore',
    'Peelamedu',
    11.02380,
    77.02430,
    'Specialty',
    'Cardiology|Oncology|Neurology|Pediatrics',
    'Yes',
    '0422-4345678',
    4.6
);


CREATE TABLE specialties (
    specialty_id  INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    simple_name   VARCHAR(100) NOT NULL,
    icon          VARCHAR(10),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- INSERT DEFAULT SPECIALTIES
INSERT INTO specialties (name, simple_name, icon) VALUES
('Emergency',       'Emergency',          '🚨'),
('Cardiology',      'Heart Problem',      '❤️'),
('Neurology',       'Brain & Nerves',     '🧠'),
('Dental',          'Teeth & Mouth',      '🦷'),
('Orthopedics',     'Bone & Joint Pain',  '🦴'),
('Pediatrics',      'Child & Baby Care',  '👶'),
('Ophthalmology',   'Eye Problem',        '👁️'),
('Gynecology',      'Womens Health',      '🤰'),
('Oncology',        'Cancer Treatment',   '🔬'),
('General Medicine','General Checkup',    '🏥'),
('Dermatology',     'Skin & Hair',        '💇');

-- Verify
SELECT * FROM specialties;
-- ================================================
-- VERIFY TABLES
-- ================================================
SELECT * FROM admins;
SELECT * FROM hospitals;
SELECT * FROM users;
SELECT * FROM saved_hospitals;
SELECT * FROM reviews;