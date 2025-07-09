import pandas as pd
from tabulate import tabulate
import numpy as np
import re
import pytz
import time
import concurrent.futures

# datebase
# 1 = full time = full time
# 2 = part time = part time
# 3 = contract/temp = -
# 4 = casual = -
# 5 = internship = internship
# 6 = remote = work from home
# 7 = hybrid = hybrid    

def get_jobType_id(jobTypes):
    job_type_ids = []
    jobType_dict = {
        'full time': 1,
        'part time': 2,
        'contract/temp': 3,
        'casual': 4,
        'internship': 5,
        'work from home': 6,
        #remote = work from home
        'hybrid': 7
    }

    if jobTypes is None:
        return []


    if isinstance(jobTypes, str):
        jobTypes = jobTypes.strip()
        jobTypes = jobTypes.lower()
        job_type_ids.append(jobType_dict.get(jobTypes))
        return job_type_ids
    elif isinstance(jobTypes, list):
        if len(jobTypes) == 0:
            return []
        for type in jobTypes:
            if type:
                type = type.strip().lower()
                if type == 'nan':
                    continue
                elif type in jobType_dict:
                    # job_type_ids.append(jobType_dict[type])
                    job_type_ids.append(jobType_dict.get(type))
        
        return job_type_ids
    
#get jobCategory id
def get_jobCategory_id(category):
    if "462-it" in category:
        return 1
    elif "457-account" in category:
        return 2
    elif "451-admin" in category:
        return 3
    elif "454-retail" in category:
        return 4
    elif "453-customer_service" in category:
        return 5
    elif "469-sales" in category:
        return 6
    elif "470-fnb" in category:
        return 7
    elif "452-hotel" in category:
        return 7
    elif "465-engineering" in category:
        return 8
    elif "456-education" in category:
        return 9
    elif "464-health_beauty" in category:
        return 10
    elif "459-transportation_logistic" in category:
        return 11
    elif "461-manufacturing" in category:
        return 11
    elif "458-art_design" in category:
        return 12
    elif "460-journalism" in category:
        return 12
    elif "455-construction" in category:
        return 13
    elif "463-rnd" in category:
        return 14
    elif "466-agriculture" in category:
        return 15
    elif "467-social_service" in category:
        return 16
    elif "468-other" in category:
        return 26

#get clean datePosted
def get_clean_datePosted(datePosted):

    if datePosted is None:
        return None
    if 'day' in datePosted:
        if 'days' in datePosted:
            date = re.search(r'(\d+)', datePosted)
            if date:
                date = float(date.group(1))
                date = date * 24 * 60 * 60
                return date
        else:
            date = 1
            date = date * 24 * 60 * 60   
            return date
    elif 'hour' in datePosted:
        if 'hours' in datePosted:
            date = re.search(r'(\d+)', datePosted)
            if date:
                date = float(date.group(1))
                date = date * 60 * 60
                return date
        else:
            date = 1
            date = date * 60 * 60
            return date
    elif 'minute' in datePosted:
        if 'minutes' in datePosted:
            date = re.search(r'(\d+)', datePosted)
            if date:
                date = float(date.group(1))
                date = date * 60
                return date
        else:
            date = 1
            date = date * 60
            return date
    elif 'second' in datePosted:
        if 'seconds' in datePosted:
            date = re.search(r'(\d+)', datePosted)
            if date:
                date = float(date.group(1))
                return date
        else:
            date = 1
            return date

#join description
def get_string_desc(description):
    if isinstance(description, list):
        return ' '.join(description)
    else:
        return description
#join skills    
def get_string_skills(skills):
    if isinstance(skills, list):
        return ' '.join(skills)
    else:
        return skills


def init_skill_extractor():
    global nlp, skill_extractor
    
    # import
    import spacy
    from spacy.matcher import PhraseMatcher

    # load default skills data base
    from skillNer.general_params import SKILL_DB

    # import skill extractor
    from skillNer.skill_extractor_class import SkillExtractor
    
    nlp = spacy.load("en_core_web_lg")
    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

def mp_executor(descriptions, func, max_workers=10):
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers,initializer=init_skill_extractor) as executor:
        results = list(executor.map(func, descriptions))
    return results

def get_skills(description):

    global skill_extractor

    if pd.isna(description) or description is None or description == '':
        return []
    
    description = str(description)
    skills = []

    try:
        annotations = skill_extractor.annotate(description)
        if annotations['results']['full_matches']:
            for match in annotations['results']['full_matches']:
                skill_id = match['skill_id']
                skills.append(skill_id)
        if annotations['results']['ngram_scored']:
            for match in annotations['results']['ngram_scored']:
                skill_id = match['skill_id']
                skills.append(skill_id)
        skills = list(set(skills))

    except Exception as e:
        return []
    
    return skills

# #testing get_skills without multiprocessing
# def get_skills(description):
#     if pd.isna(description) or description is None or description == '':
#         return []

#     description = str(description)  
#     skills = []
    
#     try:
#         annotations = skill_extractor.annotate(description)
#         if annotations['results']['full_matches']:
#             for match in annotations['results']['full_matches']:
#                 skill_id = match['skill_id']
#                 skills.append(skill_id)
#         if annotations['results']['ngram_scored']:
#             for match in annotations['results']['ngram_scored']:
#                 skill_id = match['skill_id']
#                 skills.append(skill_id)

#         skills = list(set(skills))
#     except Exception as e:
#         return []
        
#     return skills


if __name__ == "__main__":
    #read file
    filename = "items_ricebowl_28.jl"

    #ricebowl
    rb = pd.read_json(f'./data/rb/raw/{filename}',lines=True)

    #--------------------------------------------------------------------
    #format the jobTitle
    #lower & strip
    rb.jobTitle = rb.jobTitle.str.lower().str.strip()

    #change to string
    rb.jobTitle = rb.jobTitle.astype('string')

    #--------------------------------------------------------------------
    #format the companyName
    #lower & strip
    rb.companyName = rb.companyName.str.lower().str.strip()

    #change to string
    rb.companyName = rb.companyName.astype('string')

    #--------------------------------------------------------------------
    #format the salaryRange - add max & min columns
    #lower & strip 
    rb.salaryRange = rb.salaryRange.str.lower().str.strip()

    #remove empty salaryRange
    rb.salaryRange = rb.salaryRange.apply(lambda x : np.nan if x == 'undisclosed' else x)

    #remove ,
    rb.salaryRange = rb.salaryRange.str.replace(',','')

    #get min and max
    min_max = rb.salaryRange.str.split('-',expand=True)

    #add columns
    rb['minSalary'] = min_max[0].str.extract(r'(\d+)')
    rb['maxSalary'] = min_max[1].str.extract(r'(\d+)')
    rb.minSalary = pd.to_numeric(rb.minSalary, errors='coerce')
    rb.maxSalary = pd.to_numeric(rb.maxSalary, errors='coerce')

    #--------------------------------------------------------------------
    #state
    #lower & strip
    rb.location = rb.location.str.lower().str.strip()
    
    #inspect state & format state
    #inspect unique state 13 + 3
    # print(rb.location.unique())
    # print(len(rb.location.unique()))

    #change to string
    rb.location = pd.Categorical(rb.location)

    #--------------------------------------------------------------------
    #format job type
    #lower & strip
    # rb.jobType = rb.jobType.str.lower().str.strip()

    #replace 'n/a' to nan
    rb.jobType = rb.jobType.replace('n/a',np.nan)

    # datebase
    # 1 = full time = full time
    # 2 = part time = part time
    # 3 = contract/temp = -
    # 4 = casual = -
    # 5 = internship = internship
    # 6 = remote = work from home
    # 7 = hybrid = hybrid

    rb.jobType = rb.jobType.apply(lambda x: get_jobType_id(x))

    #check 1
    # print('jobtypes')
    # print(tabulate(rb[['jobType']], headers='keys', tablefmt='grid'))

    #--------------------------------------------------------------------
    #format jobCategory
    #lower & strip
    rb.jobCategory = rb.jobCategory.str.lower().str.strip()

    # 1	"information and communication technology" = "462-it"
    # 2	"accounting and finance" = "457-account"
    # 3	"administration and human resources" = "451-admin"
    # 4	"retail and consumer products" = "454-retail"
    # 5	"customer service" = "453-customer_service"
    # 6	"sales and marketing" = "469-sales"
    # 7	"food, beverage, hospitality and tourism" = "470-fnb", "452-hotel"
    # 8	"engineering and maintenance" = "465-engineering"
    # 9	"education and training" = "456-education"
    # 10	"healthcare, beauty and medical" = "464-health_beauty"
    # 11	"manufacturing, transport and logistics" = "459-transportation_logistic", "461-manufacturing"
    # 12	"advertising, arts, media and journalism" = "458-art_design","460-journalism"
    # 13	"construction" = "455-construction"
    # 14	"science and research" = "463-rnd"
    # 15	"agriculture and conservation" = "466-agriculture"
    # 16	"community and social services" = "467-social_service"
    # 17	"legal"
    # 18	"real estate and property"
    # 19	"mining, resources and energy"
    # 20	"government and defence"
    # 21	"self-employment"
    # 22	"sport and recreation"
    # 23	"trades and services"
    # 24	"executive and general management"
    # 25	"consulting and strategy"
    # 26	"other industries" = "468-other"

    #inspect jobCategory
    # print(rb.jobCategory.unique())
    # print(len(rb.jobCategory.unique()))
    # print(tabulate(rb[['jobCategory']], headers='keys', tablefmt='grid'))

    rb.jobCategory = rb.jobCategory.apply(lambda x: get_jobCategory_id(x) if x is not None else np.nan)
    rb.jobCategory = rb.jobCategory.astype('string')

    #--------------------------------------------------------------------    
    #get post date
    #lower & strip
    rb.datePosted = rb.datePosted.str.lower().str.strip()

    #remove empty datePosted
    rb = rb[rb['datePosted'] != 'n/a']

    #split datePosted
    split_datePosted = rb.datePosted.str.split('•', expand=True)
    rb.datePosted = split_datePosted[0].str.strip()

    rb.datePosted = rb.datePosted.str.replace('posted','')
    rb.datePosted = rb.datePosted.str.replace('ago','')
    rb.datePosted = rb.datePosted.str.strip()
    # y = rb[['datePosted','scrapedAt','jobTitle','jobUrl']]
    # print(tabulate(y, headers='keys', tablefmt='psql'))
    rb.datePosted = rb.apply(lambda x: x['scrapedAt'] - get_clean_datePosted(x['datePosted']),axis = 1)

    # change dtypes to datetime
    rb.datePosted = pd.to_datetime(rb.datePosted, unit='s',utc=True)
    rb.scrapedAt = pd.to_datetime(rb.scrapedAt, unit='s',utc=True)

    #convert to malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    rb.datePosted = rb.datePosted.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)
    rb.scrapedAt = rb.scrapedAt.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)
    
    #inspect datePosted
    # empty_datePosted = rb[rb['datePosted'] == 'N/A']
    # print(tabulate(empty_datePosted, headers='keys', tablefmt='grid'))
    # total_empty = rb[rb['datePosted'] == 'n/a']
    # print(total_empty)
    # print(len(total_empty))
    #--------------------------------------------------------------------
    #extract requiredSkills
    rb.requiredSkills = rb.requiredSkills.replace('N/A', np.nan)
    rb.requiredSkills = rb.requiredSkills.apply(lambda x: get_string_skills(x) if isinstance(x, list) else x)
    rb.description = rb.description.replace('N/A', np.nan)
    rb.description = rb.description.apply(lambda x: get_string_desc(x) if isinstance(x, list) else x)
    
    #concatenate job title, requiredSkills and description
    rb.description = rb.apply(lambda x: str(x['jobTitle']) + ' ' + str(x['requiredSkills']) + ' ' + str(x['description']),axis=1)

    #format the description
    #create a cleaner
    from skillNer.cleaner import Cleaner
    cleaner = Cleaner(
                to_lowercase=True,
                include_cleaning_functions=["remove_punctuation", "remove_extra_space"]
            )

    rb.description = rb.description.apply(lambda x: cleaner(x))
    #change description to string and requiredSkills to list
    rb.description = rb.description.astype('string')
    rb.requiredSkills = rb.requiredSkills.astype('object')
    # print(rb.dtypes)
    
    #extract skills
    start_time = time.time()

    max_workers = 10
    nlp = None
    skill_extractor = None
    
    rb['requiredSkills'] = mp_executor(rb.description, get_skills, max_workers=10)

    end_time = time.time()
    print(f"Time taken to extract skills: {end_time - start_time} seconds")

    #--------------------------------------------------------------------
    #save to file
    #drop useless columns
    rb.drop(columns=['salaryRange','description','_type'],axis = 1, inplace=True)

    #add source column
    rb['source'] = 'ricebowl' 

    #rename location to state
    rb.rename(columns={'location': 'state'}, inplace=True)

    #save to jsonl
    filename = 'cleaned_' + filename
    rb.to_json(f'./data/rb/cleaned/{filename}',orient='records', lines=True, force_ascii=False)
    