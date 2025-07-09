#import
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np
import pytz

#database connection
db_user = 'postgres'
db_password = 'Fist-1211204126.'
db_host = 'localhost'
db_port = '5432'
db_name = 'FYP'

#database URL
DB_URL = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}' 

#create connection to the database
engine = create_engine(DB_URL,echo=False)

#reflect
Base = automap_base()
Base.prepare(engine, reflect=True)  

#session
Session = sessionmaker(bind=engine)
session = Session()

#reflect the tables from database
#jobs
jobs = Base.classes.jobs
# print(jobs.__table__.columns.keys())
# ['id', 'job_title', 'max_salary', 'min_salary', 'state', 'job_category_id', 'date_posted', 'scraped_at', 'job_url', 'source', 'company_name']
#skills
skills = Base.classes.skills
# print(skills.__table__.columns.keys())
# ['id', 'external_key', 'skill_name', 'is_hard_skill', 'is_soft_skill', 'is_certification', 'is_language']
#job_job_types
job_job_types = Base.classes.job_job_types
# print(job_job_types.__table__.columns.keys())
# ['id', 'job_id', 'job_type_id']
#job_skills
job_skills = Base.classes.job_skills
# print(job_skills.__table__.columns.keys())
# ['id', 'job_id', 'skill_id']
#job_categories
job_categories = Base.classes.job_categories
# print(job_categories.__table__.columns.keys())
# ['id', 'name']
#job_types 
job_types = Base.classes.job_types
# print(job_types.__table__.columns.keys())
# ['id', 'type_name']

#read file
rb_filepath = 'rb/cleaned/cleaned_items_ricebowl_28.jl'
# js_filepath = 'js/cleaned/cleaned_items_jobstreet_20.jl'
filepath = rb_filepath 
data = pd.read_json(f'../../cleaner/data/{filepath}',lines=True)
#get columns
# print(data.columns)
'''
Index(['jobTitle', 'companyName', 'requiredSkills', 'state', 'jobType',
       'jobCategory', 'datePosted', 'scrapedAt', 'jobUrl', 'minSalary',
       'maxSalary', 'source'],
      dtype='object')
'''
# print(data.dtypes)

# print('--------------------------------------------------check time zone--------------------------------------------')
# for index, row in testing.iterrows():
#     print(f'datePosted: {row["datePosted"]}')
#     print(f'scrapedAt: {row["scrapedAt"]}')

data.scrapedAt = pd.to_datetime(data.scrapedAt,unit = 'ms', errors='coerce',utc=True)
data.datePosted = pd.to_datetime(data.datePosted,unit = 'ms', errors='coerce',utc=True)

#convert to malaysia timezone
malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur') 
data.scrapedAt = data.scrapedAt.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)
data.datePosted = data.datePosted.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)  


# for index, row in data.iterrows():
#     print(f'datePosted: {row["datePosted"]}')
#     print(f'scrapedAt: {row["scrapedAt"]}')

# print('----------------------------------------------end check time zone--------------------------------------------')


skipped_count = 0
inserted_count = 0       
for index, row in data.iterrows():
    drop_marks = 0
    #8
    #4
    #2
    #1

    if pd.notna(row['scrapedAt']):
        row['scrapedAt'] = row['scrapedAt'].to_pydatetime()        
    elif pd.isna(row['scrapedAt']):
        row['scrapedAt'] = None

    if pd.notna(row['datePosted']):
        row['datePosted'] = row['datePosted'].to_pydatetime()
    elif pd.isna(row['datePosted']):
        row['datePosted'] = None
    

    if row['scrapedAt'] == None or pd.isna(row['scrapedAt']) or row['scrapedAt'] == 'n/a' or row['scrapedAt'] == '':
        drop_marks += 8
    if row['jobCategory'] == None or pd.isna(row['jobCategory']) or row['jobCategory'] == '' or row['jobCategory'] == 'n/a':
        drop_marks += 4
    if row['state'] == None or pd.isna(row['state']) or row['state'] == 'n/a' or row['state'] == '':
        drop_marks += 2
    try:
        if row['jobType'] == None or row['jobType'] == 'n/a' or len(row['jobType']) == 0:
            drop_marks += 1
    except TypeError:
        if row['jobType'] == None or row['jobType'] == 'n/a':
            drop_marks += 1    

    if drop_marks > 0:
        skipped_count += 1
        if drop_marks == 1:
            print(f'Skipped index:{index} due to jobType empty')
        elif drop_marks == 2:
            print(f'Skipped index:{index} due to state empty')
        elif drop_marks == 3:
            print(f'Skipped index:{index} due to jobType and state are empty')
        elif drop_marks == 4:
            print(f'Skipped index{index} due to jobCategory is empty')
        elif drop_marks == 5:
            print(f'Skipped index:{index} due to jobCategory and jobType are empty')
        elif drop_marks == 6:
            print(f'Skipped index:{index} due to jobCategory and state are empty')
        elif drop_marks == 7:
            print(f'Skipped index:{index} due to jobCategory, jobType and state are empty')
        elif drop_marks == 8:
            print(f'Skipped index:{index} due to scrapedAt is empty')
        elif drop_marks == 9:
            print(f'Skipped index:{index} due to scrapedAt and jobType are empty')
        elif drop_marks == 10:
            print(f'Skipped index:{index} due to scrapedAt and state are empty')
        elif drop_marks == 11:
            print(f'Skipped index:{index} due to scrapedAt, jobType and state are empty')
        elif drop_marks == 12:
            print(f'Skipped index:{index} due to scrapedAt and jobCategory are empty')
        elif drop_marks == 13:
            print(f'Skipped index:{index} due to scrapedAt, jobCategory and jobType are empty')
        elif drop_marks == 14:
            print(f'Skipped index:{index} due to scrapedAt, jobCategory and state are empty')
        elif drop_marks == 15:
            print(f'Skipped index:{index} due to scrapedAt, jobCategory, jobType and state are empty')
        continue

    #check url
    inserted_job = session.query(jobs).filter(jobs.job_url == row['jobUrl']).first()
    if inserted_job:
        print(f'Skipped index:{index} due to jobUrl already exists')
        skipped_count += 1
        continue

    #insert job table
    # ['id', 'job_title', 'max_salary', 'min_salary', 'state', 'job_category_id', 'date_posted', 'scraped_at', 'job_url', 'source', 'company_name']
    job = jobs(job_title = row['jobTitle'], 
               max_salary = row['maxSalary'], 
               min_salary = row['minSalary'], 
               state = row['state'], 
               job_category_id = row['jobCategory'], 
               date_posted = row['datePosted'], 
               scraped_at = row['scrapedAt'], 
               job_url = row['jobUrl'], 
               source = row['source'], 
               company_name = row['companyName'])
    session.add(job)
    session.flush()
    job_id = job.id
    # print(
    #       row['jobTitle'], 
    #       row['companyName'], 
    #       row['requiredSkills'], 
    #       row['requiredSkills'],  
    #       row['state'], 
    #       row['jobType'],
    #       row['jobCategory'], 
    #       row['datePosted'], 
    #       row['scrapedAt'], 
    #       row['jobUrl'], 
    #       row['minSalary'],
    #       row['maxSalary'], 
    #       row['source'])

    # print(
    #     type(row['jobTitle']), #<class 'str'>
    #     type(row['companyName']), #<class 'str'>
    #     type(row['requiredSkills']), #<class 'list'>
    #     type(row['state']), #<class 'str'>
    #     type(row['jobType']), #<class 'list'>
    #     type(row['jobCategory']), #<class 'int'> 
    #     type(row['datePosted']), #<class 'int'>
    #     type(row['scrapedAt']), #<class 'int'>
    #     type(row['jobUrl']), #<class 'str'>
    #     type(row['minSalary']), #<class 'float'>
    #     type(row['maxSalary']), #<class 'float'>
    #     type(row['source']) #<class 'str'>
    #     )
    
    
    # <class 'str'> <class 'str'> <class 'list'> <class 'str'> <class 'list'> <class 'int'> <class 'int'> <class 'int'> <class 'str'> <class 'float'> <class 'float'> <class 'str'>
    
    # print('-------------------------------get skill ids------------------------------')
    skill_ids = []

    for skill in row['requiredSkills']:
        if skill is None or pd.isna(skill):
            continue
        skill_id = session.query(skills.id).filter(skills.external_key == skill).first() 
        if skill_id:
            # print('print skill_id = ')
            # print(type(skill_id))  
            # print(skill_id)     
            # print(skill_id._mapping['id'])
            # print(type(skill_id._mapping['id']))
            # print("print skill_id[0] = ")
            # print(type(skill_id[0]))
            # print(skill_id[0])
        
            skill_ids.append(skill_id._mapping['id'])

    # print(f'{index}. skill id list = {skill_ids}')
    # print('----------------------------end---------------------------------')
    # print('------------insert job_skills table---------------------')
    insert_job_skills_list = []
    for skill_id in skill_ids:
        insert_job_skills_list.append(job_skills(job_id=job_id, skill_id=skill_id))
    # print('--------------------------end----------------------------')

    # print('--------------------------get job types ids-----------------------------------')
    job_type_ids = []
    if row['jobType'] is None:
        print('jobType is None')
        continue
    else:
        for job_type in row['jobType']:
            if job_type is None or pd.isna(job_type):
                continue
            job_type_id = session.query(job_types.id).filter(job_types.id == job_type).first() 
            if job_type_id:
                job_type_ids.append(job_type_id._mapping['id'])
        # print(f'{index}. job type id list = {job_type_ids}')
    # print('--------------------------------end------------------------------')
    # print('-------------insert job_job_types table---------------------')
    insert_job_job_types_list = []
    for job_type_id in job_type_ids:
        insert_job_job_types_list.append(job_job_types(job_id=job_id, job_type_id=job_type_id))
    # print('-------------------------end----------------------------')


    #------------------------------
    # commit
    session.add_all(insert_job_skills_list)
    session.add_all(insert_job_job_types_list)
    session.commit()
    inserted_count += 1
    #------------------------------

session.close()
print(f'Total inserted rows: {inserted_count}')    
print(f'Total skipped rows: {skipped_count}')