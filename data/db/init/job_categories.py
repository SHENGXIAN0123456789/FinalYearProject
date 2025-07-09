import psycopg2
categories = [
"information and communication technology",
"accounting and finance",
"administration and human resources", 
"retail and consumer products",
"customer service",
"sales and marketing",
"food, beverage, hospitality and tourism",
"engineering and maintenance",
"education and training",
"healthcare, beauty and medical",
"manufacturing, transport and logistics",
"advertising, arts, media and journalism",
"construction",
"science and research",
"agriculture and conservation",
"community and social services",
"legal",
"real estate and property",
"mining, resources and energy",
"government and defence",
"self-employment",
"sport and recreation",
"trades and services",
"executive and general management", 
"consulting and strategy",
"other industries",
]

# print(len(categories))

conn = psycopg2.connect(dbname='FYP', user='postgres', password='Fist-1211204126.', host='localhost', port='5432')

cursor = conn.cursor()

for category in categories:
    cursor.execute(
        "INSERT INTO job_categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (category,)
    )

conn.commit()
cursor.close()
conn.close()