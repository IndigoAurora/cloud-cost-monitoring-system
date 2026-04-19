CREATE DATABASE cloud_cost_monitoring;
USE cloud_cost_monitoring;


-- 1st step--
CREATE TABLE companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    contact_email VARCHAR(100),
    created_at DATE
);

CREATE TABLE cloud_services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50),
    category VARCHAR(50),
    price_per_unit DECIMAL(10,2)
);

CREATE TABLE teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT,
    team_name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    monthly_budget DECIMAL(10,2),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE cost_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT,
    service_id INT,
    team_id INT,
    amount_spent DECIMAL(10,2),
    usage_hours INT,
    billing_month DATE,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (service_id) REFERENCES cloud_services(service_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    record_id INT,
    alert_type VARCHAR(50),
    message VARCHAR(255),
    status VARCHAR(20),
    triggered_at DATETIME,
    FOREIGN KEY (record_id) REFERENCES cost_records(record_id)
);

SHOW TABLES;


-- 2nd step --
-- Insert companies
INSERT INTO companies (company_name, industry, contact_email, created_at) VALUES
('TechCorp India', 'Technology', 'admin@techcorp.in', '2023-01-15'),
('Zomato Ltd', 'Food Delivery', 'cloud@zomato.com', '2022-06-10'),
('Paytm Services', 'Fintech', 'infra@paytm.com', '2021-03-20'),
('Byju\'s Learning', 'EdTech', 'ops@byjus.com', '2022-11-05');

-- Insert cloud services
INSERT INTO cloud_services (service_name, provider, category, price_per_unit) VALUES
('EC2 Compute', 'AWS', 'Compute', 0.85),
('Cloud Storage', 'Google Cloud', 'Storage', 0.23),
('Azure SQL', 'Microsoft Azure', 'Database', 1.20),
('Lambda Functions', 'AWS', 'Serverless', 0.40),
('BigQuery', 'Google Cloud', 'Analytics', 0.65);

-- Insert teams
INSERT INTO teams (company_id, team_name, department, monthly_budget) VALUES
(1, 'Backend Team', 'Engineering', 5000.00),
(1, 'Data Team', 'Analytics', 3000.00),
(2, 'Platform Team', 'Engineering', 8000.00),
(3, 'Payments Team', 'Fintech', 6000.00),
(4, 'Content Team', 'EdTech', 4000.00);

-- Insert cost records
INSERT INTO cost_records (company_id, service_id, team_id, amount_spent, usage_hours, billing_month) VALUES
(1, 1, 1, 4200.00, 620, '2026-01-01'),
(1, 2, 2, 1800.00, 400, '2026-01-01'),
(2, 1, 3, 7500.00, 900, '2026-01-01'),
(2, 3, 3, 3200.00, 300, '2026-01-01'),
(3, 4, 4, 2100.00, 500, '2026-02-01'),
(3, 1, 4, 6800.00, 800, '2026-02-01'),
(4, 5, 5, 1500.00, 200, '2026-02-01'),
(4, 2, 5, 900.00,  150, '2026-02-01');

-- Insert alerts
INSERT INTO alerts (record_id, alert_type, message, status, triggered_at) VALUES
(1, 'Budget Exceeded', 'TechCorp Backend Team exceeded budget on EC2', 'Active', '2026-01-15 10:30:00'),
(3, 'Budget Exceeded', 'Zomato Platform Team exceeded budget on EC2', 'Active', '2026-01-20 14:45:00'),
(6, 'Critical Spike', 'Paytm Payments Team critical spike on EC2', 'Resolved', '2026-02-10 09:15:00'),
(8, 'Low Usage', 'Byju\'s Content Team low usage on Cloud Storage', 'Active', '2026-02-18 16:00:00');


-- 3rd step --
-- Query 1: See all companies and their details
SELECT * FROM companies;

-- Query 2: See all cost records with company and service names (JOIN)
SELECT 
    c.company_name,
    cs.service_name,
    cs.provider,
    t.team_name,
    cr.amount_spent,
    cr.usage_hours,
    cr.billing_month
FROM cost_records cr
JOIN companies c ON cr.company_id = c.company_id
JOIN cloud_services cs ON cr.service_id = cs.service_id
JOIN teams t ON cr.team_id = t.team_id;

-- Query 3: Total spending per company
SELECT 
    c.company_name,
    SUM(cr.amount_spent) AS total_spent
FROM cost_records cr
JOIN companies c ON cr.company_id = c.company_id
GROUP BY c.company_name
ORDER BY total_spent DESC;

-- Query 4: Teams that EXCEEDED their monthly budget
SELECT 
    t.team_name,
    t.department,
    t.monthly_budget,
    SUM(cr.amount_spent) AS actual_spent,
    SUM(cr.amount_spent) - t.monthly_budget AS overspent_by
FROM cost_records cr
JOIN teams t ON cr.team_id = t.team_id
GROUP BY t.team_id, t.team_name, t.department, t.monthly_budget
HAVING actual_spent > t.monthly_budget;

-- Query 5: All active alerts with company name
SELECT 
    c.company_name,
    a.alert_type,
    a.message,
    a.status,
    a.triggered_at
FROM alerts a
JOIN cost_records cr ON a.record_id = cr.record_id
JOIN companies c ON cr.company_id = c.company_id
WHERE a.status = 'Active';

-- 4th Step --
USE cloud_cost_monitoring;

INSERT INTO cost_records (company_id, service_id, team_id, amount_spent, usage_hours, billing_month) VALUES
(1, 1, 1, 4800.00, 680, '2026-02-01'),
(1, 2, 2, 2100.00, 450, '2026-02-01'),
(2, 1, 3, 8200.00, 950, '2026-02-01'),
(2, 3, 3, 3500.00, 320, '2026-02-01'),
(3, 4, 4, 2400.00, 550, '2026-03-01'),
(3, 1, 4, 7200.00, 820, '2026-03-01'),
(4, 5, 5, 1800.00, 220, '2026-03-01'),
(4, 2, 5, 1100.00, 180, '2026-03-01'),
(1, 1, 1, 5200.00, 720, '2026-03-01'),
(2, 1, 3, 9100.00, 1000, '2026-03-01');

-- 5th step --
SELECT 
    c.company_name,
    t.team_name,
    cr.amount_spent,
    cr.billing_month
FROM cost_records cr
JOIN companies c ON cr.company_id = c.company_id
JOIN teams t ON cr.team_id = t.team_id
WHERE c.company_name = 'TechCorp India'
ORDER BY cr.billing_month;
-- 6th step --
SELECT * FROM companies ORDER BY company_id DESC;
-- 7th step --
SELECT c.company_name, t.team_name, t.monthly_budget
FROM companies c
JOIN teams t ON c.company_id = t.company_id
WHERE c.company_name = 'dbms.ltd';