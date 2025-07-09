import psycopg2

conn = psycopg2.connect(
    dbname='FYP',  
    user='postgres',    
    password='Fist-1211204126.',
    host='localhost',
    port='5432'
)

cursor = conn.cursor()

create_tables_sql = """

CREATE TABLE IF NOT EXISTS job_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    external_key TEXT UNIQUE,
    skill_name TEXT UNIQUE NOT NULL,
    is_hard_skill BOOLEAN DEFAULT FALSE,
    is_soft_skill BOOLEAN DEFAULT FALSE,
    is_certification BOOLEAN DEFAULT FALSE,
    is_language BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS job_types (
    id SERIAL PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    max_salary NUMERIC,
    min_salary NUMERIC,
    state TEXT,
    job_category_id INTEGER REFERENCES job_categories(id) ON DELETE SET NULL,
    date_posted TIMESTAMP,
    scraped_at TIMESTAMP,
    job_url TEXT UNIQUE NOT NULL,
    source TEXT,
    company_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE(job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS job_job_types (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    job_type_id INTEGER REFERENCES job_types(id) ON DELETE CASCADE,
    UNIQUE(job_id, job_type_id)
);
"""

cursor.execute(create_tables_sql)
conn.commit()

print('successfully created tables')

cursor.close()
conn.close()
