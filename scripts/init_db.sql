-- Initialize database for text2sql-lab
-- Create extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Create langfuse database
CREATE DATABASE langfuse_db;

-- Switch to text2sql_db (this will be the default)
-- Create sample tables for text2sql practice

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    department_id INTEGER,
    salary DECIMAL(10, 2),
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    budget DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12, 2),
    status VARCHAR(50),
    department_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project assignments table
CREATE TABLE IF NOT EXISTS project_assignments (
    assignment_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    role VARCHAR(100),
    hours_allocated DECIMAL(6, 2),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    customer_id INTEGER,
    employee_id INTEGER,
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    company VARCHAR(200),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lexicon table for RAG (terminology/glossary)
CREATE TABLE IF NOT EXISTS lexicon (
    lexicon_id SERIAL PRIMARY KEY,
    term VARCHAR(200) NOT NULL,
    definition TEXT NOT NULL,
    category VARCHAR(100),
    examples TEXT,
    embedding vector(384),  -- For pgvector embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table for RAG
CREATE TABLE IF NOT EXISTS documents (
    document_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(100),
    metadata JSONB,
    embedding vector(384),  -- For pgvector embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query history table for monitoring
CREATE TABLE IF NOT EXISTS query_history (
    query_id SERIAL PRIMARY KEY,
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT,
    execution_success BOOLEAN,
    execution_time_ms INTEGER,
    result_count INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraints
ALTER TABLE employees ADD CONSTRAINT fk_department 
    FOREIGN KEY (department_id) REFERENCES departments(department_id);

ALTER TABLE employees ADD CONSTRAINT fk_manager 
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id);

ALTER TABLE projects ADD CONSTRAINT fk_project_department 
    FOREIGN KEY (department_id) REFERENCES departments(department_id);

ALTER TABLE sales ADD CONSTRAINT fk_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

-- Create indexes for better performance
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_projects_department ON projects(department_id);
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_employee ON sales(employee_id);
CREATE INDEX idx_sales_customer ON sales(customer_id);

-- Create vector indexes for similarity search
CREATE INDEX idx_lexicon_embedding ON lexicon USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- Insert sample data
-- Departments
INSERT INTO departments (department_name, location, budget) VALUES
    ('Engineering', 'Seoul', 5000000.00),
    ('Sales', 'Busan', 3000000.00),
    ('Marketing', 'Seoul', 2000000.00),
    ('HR', 'Seoul', 1000000.00),
    ('Finance', 'Seoul', 1500000.00);

-- Employees
INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, department_id, salary, manager_id) VALUES
    ('John', 'Kim', 'john.kim@example.com', '010-1234-5678', '2020-01-15', 'Engineering Manager', 1, 8000000.00, NULL),
    ('Sarah', 'Lee', 'sarah.lee@example.com', '010-2345-6789', '2020-03-20', 'Senior Developer', 1, 6500000.00, 1),
    ('Mike', 'Park', 'mike.park@example.com', '010-3456-7890', '2021-06-10', 'Developer', 1, 5000000.00, 1),
    ('Emily', 'Choi', 'emily.choi@example.com', '010-4567-8901', '2019-08-05', 'Sales Manager', 2, 7500000.00, NULL),
    ('David', 'Jung', 'david.jung@example.com', '010-5678-9012', '2021-01-12', 'Sales Representative', 2, 4500000.00, 4),
    ('Lisa', 'Han', 'lisa.han@example.com', '010-6789-0123', '2020-09-18', 'Marketing Manager', 3, 7000000.00, NULL),
    ('Tom', 'Yoon', 'tom.yoon@example.com', '010-7890-1234', '2022-02-01', 'Marketing Specialist', 3, 4000000.00, 6),
    ('Anna', 'Kang', 'anna.kang@example.com', '010-8901-2345', '2019-05-10', 'HR Manager', 4, 6500000.00, NULL),
    ('James', 'Shin', 'james.shin@example.com', '010-9012-3456', '2020-11-22', 'Finance Manager', 5, 7500000.00, NULL),
    ('Sophie', 'Lim', 'sophie.lim@example.com', '010-0123-4567', '2021-07-14', 'Financial Analyst', 5, 5500000.00, 9);

-- Customers
INSERT INTO customers (customer_name, company, email, phone, address, city, country) VALUES
    ('Alice Johnson', 'Tech Corp', 'alice@techcorp.com', '02-1111-2222', '123 Tech St', 'Seoul', 'South Korea'),
    ('Bob Smith', 'Global Industries', 'bob@global.com', '02-2222-3333', '456 Business Ave', 'Seoul', 'South Korea'),
    ('Carol White', 'Innovation Ltd', 'carol@innovation.com', '051-3333-4444', '789 Future Rd', 'Busan', 'South Korea'),
    ('Daniel Brown', 'Solutions Inc', 'daniel@solutions.com', '02-4444-5555', '321 Corporate Blvd', 'Seoul', 'South Korea'),
    ('Eva Green', 'Digital Systems', 'eva@digital.com', '031-5555-6666', '654 Tech Park', 'Incheon', 'South Korea');

-- Projects
INSERT INTO projects (project_name, description, start_date, end_date, budget, status, department_id) VALUES
    ('AI Platform Development', 'Build an AI-powered analytics platform', '2023-01-01', '2023-12-31', 2000000.00, 'Active', 1),
    ('Marketing Campaign 2024', 'Q1 marketing campaign for new product launch', '2024-01-01', '2024-03-31', 500000.00, 'Active', 3),
    ('Sales Training Program', 'Comprehensive sales training for new products', '2023-06-01', '2023-12-31', 300000.00, 'Completed', 2),
    ('HR System Upgrade', 'Upgrade HRIS to cloud-based solution', '2023-09-01', '2024-03-31', 800000.00, 'Active', 4),
    ('Financial Reporting Tool', 'Develop automated financial reporting system', '2023-03-01', '2023-11-30', 600000.00, 'Completed', 5);

-- Project assignments
INSERT INTO project_assignments (project_id, employee_id, role, hours_allocated, start_date, end_date) VALUES
    (1, 1, 'Project Lead', 1000.00, '2023-01-01', '2023-12-31'),
    (1, 2, 'Senior Developer', 1200.00, '2023-01-01', '2023-12-31'),
    (1, 3, 'Developer', 1200.00, '2023-01-01', '2023-12-31'),
    (2, 6, 'Campaign Manager', 500.00, '2024-01-01', '2024-03-31'),
    (2, 7, 'Marketing Specialist', 600.00, '2024-01-01', '2024-03-31'),
    (3, 4, 'Training Lead', 400.00, '2023-06-01', '2023-12-31'),
    (4, 8, 'System Administrator', 600.00, '2023-09-01', '2024-03-31'),
    (5, 9, 'Project Sponsor', 300.00, '2023-03-01', '2023-11-30'),
    (5, 10, 'Financial Analyst', 800.00, '2023-03-01', '2023-11-30');

-- Sales data
INSERT INTO sales (sale_date, product_name, category, quantity, unit_price, total_amount, customer_id, employee_id, region) VALUES
    ('2024-01-05', 'Enterprise Software License', 'Software', 10, 500000.00, 5000000.00, 1, 5, 'Seoul'),
    ('2024-01-10', 'Cloud Storage Plan', 'Services', 50, 10000.00, 500000.00, 2, 5, 'Seoul'),
    ('2024-01-15', 'Consulting Services', 'Services', 100, 50000.00, 5000000.00, 3, 5, 'Busan'),
    ('2024-01-20', 'Training Program', 'Education', 20, 100000.00, 2000000.00, 4, 5, 'Seoul'),
    ('2024-02-01', 'Mobile App License', 'Software', 30, 200000.00, 6000000.00, 5, 5, 'Incheon'),
    ('2024-02-05', 'Data Analytics Tool', 'Software', 15, 800000.00, 12000000.00, 1, 5, 'Seoul'),
    ('2024-02-10', 'API Access', 'Services', 25, 150000.00, 3750000.00, 2, 5, 'Seoul'),
    ('2024-02-15', 'Technical Support', 'Services', 12, 250000.00, 3000000.00, 3, 5, 'Busan'),
    ('2024-03-01', 'Custom Development', 'Services', 5, 2000000.00, 10000000.00, 4, 5, 'Seoul'),
    ('2024-03-05', 'Premium Support Plan', 'Services', 8, 500000.00, 4000000.00, 5, 5, 'Incheon');

-- Sample lexicon entries
INSERT INTO lexicon (term, definition, category, examples) VALUES
    ('Text2SQL', 'Converting natural language queries into SQL statements using AI', 'AI/ML', 'User asks "show me all employees" and system generates SELECT * FROM employees'),
    ('RAG', 'Retrieval-Augmented Generation - combining information retrieval with text generation', 'AI/ML', 'System retrieves relevant documents before generating response'),
    ('pgvector', 'PostgreSQL extension for vector similarity search and storage', 'Database', 'Store embeddings as vector(384) type'),
    ('Embedding', 'Dense vector representation of text for semantic search', 'AI/ML', 'Converting "hello world" into [0.23, -0.45, 0.67, ...]'),
    ('LangChain', 'Framework for developing applications powered by language models', 'Framework', 'Building chatbots, agents, and RAG systems'),
    ('LangGraph', 'Library for building stateful multi-actor applications with LLMs', 'Framework', 'Creating agent workflows with cycles and state management'),
    ('Ollama', 'Tool for running open-source LLMs locally', 'Infrastructure', 'Running Llama 2, Mistral, or other models on-premise'),
    ('Langfuse', 'Open source LLM engineering platform for monitoring and debugging', 'Observability', 'Track token usage, latency, and quality of LLM responses');

-- Sample documents
INSERT INTO documents (title, content, document_type, metadata) VALUES
    ('Database Schema Guide', 'This document describes the database schema used in the text2sql-lab project. The main tables include employees, departments, projects, sales, and customers. Each table has specific relationships and indexes for optimal performance.', 'Documentation', '{"version": "1.0", "author": "System"}'),
    ('Text2SQL Best Practices', 'When implementing text2sql systems: 1) Always validate user input, 2) Use parameterized queries to prevent SQL injection, 3) Provide clear error messages, 4) Log all queries for monitoring, 5) Implement rate limiting.', 'Guide', '{"category": "security", "priority": "high"}'),
    ('RAG Implementation Guide', 'Implementing RAG involves: 1) Document chunking, 2) Generating embeddings, 3) Storing in vector database, 4) Similarity search for retrieval, 5) Context augmentation in prompts.', 'Tutorial', '{"difficulty": "intermediate"}'),
    ('LangChain Agent Patterns', 'Common agent patterns in LangChain: ReAct (Reasoning + Acting), Plan-and-Execute, Self-Ask, Tree of Thoughts. Each pattern has different use cases and performance characteristics.', 'Reference', '{"framework": "langchain", "version": "0.1.0"}'),
    ('Monitoring and Observability', 'Key metrics to monitor in LLM applications: latency, token usage, cost, error rate, user satisfaction. Use tools like Langfuse for comprehensive monitoring.', 'Guide', '{"topic": "observability"}');

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO text2sql;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO text2sql;
