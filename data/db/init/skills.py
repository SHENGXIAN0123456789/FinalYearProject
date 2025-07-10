import psycopg2
import csv
import spacy
from spacy.matcher import PhraseMatcher

# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor

conn = psycopg2.connect(dbname='FYP', user='postgres', password='Fist-1211204126.', host='localhost', port='5432')

cursor = conn.cursor()

for skill_id, skill_info in SKILL_DB.items():
    skill_name = skill_info.get('skill_name') 
    skill_type = skill_info.get('skill_type') 
    is_hard = skill_type == 'Hard Skill'
    is_soft = skill_type == 'Soft Skill'
    is_cert = skill_type == 'Certification'
    is_lang = False
    cursor.execute(
        """
        INSERT INTO skills (external_key, skill_name, is_hard_skill, is_soft_skill, is_certification, is_language)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_key) DO NOTHING
        """,
        (skill_id, skill_name, is_hard, is_soft, is_cert, is_lang)
    )

with open('./is_language.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        external_key = row['external_key']
        cursor.execute(
            """
            UPDATE skills 
            SET is_language = TRUE 
            WHERE external_key = %s
            """,
            (external_key,)
        )

conn.commit()
cursor.close()
conn.close()

print(len(SKILL_DB.items()))