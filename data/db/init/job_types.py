import psycopg2

job_types = [
'full time',
'part time',
'contract/temp',
'casual',
'internship',
'remote',
'hybrid',
]

conn = psycopg2.connect(dbname='FYP', user='postgres', password='Fist-1211204126.', host='localhost', port='5432')

cursor = conn.cursor()

for job_type in job_types:
    cursor.execute(
        "INSERT INTO job_types (type_name) VALUES (%s) ON CONFLICT (type_name) DO NOTHING",
        (job_type,)
    )

conn.commit()
cursor.close()
conn.close()