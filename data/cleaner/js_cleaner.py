#function
#import libraries
import pandas as pd
import numpy as np
from tabulate import tabulate
import concurrent.futures
import re
import pytz 
# from datetime import datetime
import time

#convert jobtypes into ids
def get_jobType_id(job_types):

    job_type_ids = []
    jobType = {
        'full time': 1,
        'part time': 2,
        'contract/temp': 3,
        'casual': 4,
        'internship': 5,
        'remote': 6,
        'hybrid': 7
    }

    if job_types is None or len(job_types) == 0:
        return []

    for type in job_types:
        if type:
            type = type.strip()
            if type == 'nan':
                continue
            elif type == 'casual/vacation':
                type = 'casual'
            # job_type_ids.append(jobType[type])
            job_type_ids.append(jobType.get(type))
    
    return job_type_ids

#get jobCategory id
def get_jobCategory_id(category):
    if 'call-centre-customer-service' in category:
        return '5'  #checked
    elif 'ceo-general-management' in category:
        return '24' #checked
    elif 'banking-financial-services' in category:
        return '2'  #checked
    elif 'advertising-arts-media' in category:
        return '12' #checked
    elif 'administration-office-support' in category:
        return '3'  #checked
    elif 'accounting' in category:
        return '2'  #checked
    elif 'construction' in category: 
        return '13' #checked
    elif 'consulting-strategy' in category:
        return '25' #checked
    elif 'community-services-development' in category:
        return '16' #checked    
    elif 'design-architecture' in category:
        return '12' #checked
    elif 'education-training' in category:
        return '9'  #checked
    elif'engineering' in category:
        return '8' #checked
    elif 'farming-animals-conservation' in category:
        return '15' #checked
    elif 'government-defence' in category:
        return '20' #checked
    elif 'healthcare-medical' in category:
        return '10' #checked
    elif 'human-resources-recruitment' in category:
        return '3' #checked
    elif 'information-communication-technology' in category:
        return '1' #checked
    elif 'legal' in category:
        return '17' #checked
    elif 'hospitality-tourism' in category: 
        return '7' #checked
    elif 'manufacturing-transport-logistics' in category:
        return '11' #checked
    elif 'marketing-communications' in category:
        return '6'  #checked
    elif 'real-estate-property' in category:
        return '18' #checked
    elif 'retail-consumer-products' in category:
        return '4' #checked
    elif 'mining-resources-energy' in category:
        return '19' #checked
    elif 'science-technology' in category:
        return '14' #checked
    elif 'self-employment' in category:
        return '21' #checked
    elif 'sport-recreation' in category:
        return '22' #checked
    elif 'trades-services' in category: 
        return '23' #checked
    elif 'sales' in category:
        return '6'  #checked
    elif 'insurance-superannuation' in category:
        return '2'  #checked

#convert to datetime
def get_clean_datePosted(datePosted):
    date = re.search(r'(\d+)',datePosted)
    if date: 
        date = float(date.group(1))
        if 'd' in datePosted:
            date = date * 24 * 60 * 60
        elif 'h' in datePosted:
            date = date * 60 * 60
        elif 'm' in datePosted:
            date = date * 60
        elif 's' in datePosted:
            date = date
        return date
    else:
        return np.nan

#join
def get_string_desc(description):
    if isinstance(description, list):
        return ' '.join(description)
    else:
        return description

def init_skill_extractor():
    global nlp, skill_extractor
    
    #import
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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Run
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    #read file 
    filename = 'items_jobstreet_20.jl'

    #jobstreet
    js = pd.read_json(f'./data/js/raw/{filename}', lines=True) 

    #--------------------------------------------------------------------
    #format the jobTitle
    #lower & strip
    js.jobTitle = js.jobTitle.str.lower().str.strip()

    #change to string
    js.jobTitle = js.jobTitle.astype('string')

    #--------------------------------------------------------------------
    #format the companyName
    #lower & strip
    js.companyName = js.companyName.str.lower().str.strip()

    #change to string
    js.companyName = js.companyName.astype('string')

    #--------------------------------------------------------------------
    #format the salaryRange - add max & min columns
    #remove empty salaryRange
    js.salaryRange = js.salaryRange.apply(lambda x : np.nan if x == 'Add expected salary to your profile for insights' else x)

    #lower & strip 
    js.salaryRange = js.salaryRange.str.lower().str.strip()

    #remove ,
    js.salaryRange = js.salaryRange.str.replace(',','')

    #only keep RM/MYR
    js.salaryRange = js.salaryRange.apply(lambda x: np.nan if 'rm' not in str(x) and 'myr' not in str(x) else x)

    #get min and max
    min_max = js.salaryRange.str.split('–',expand=True)

    #add columns
    js['minSalary'] = min_max[0].str.extract(r'(\d+)')
    js['maxSalary'] = min_max[1].str.extract(r'(\d+)')
    js.minSalary = pd.to_numeric(js.minSalary, errors='coerce')
    js.maxSalary = pd.to_numeric(js.maxSalary, errors='coerce')

    #--------------------------------------------------------------------
    #inspect state & format state
    #inspect unique state 13 + 3
    # print(js.location.unique())
    # print(len(js.location.unique()))

    #lower & strip
    js.location = js.location.str.lower().str.strip()

    #change to string
    js.location = pd.Categorical(js.location)

    #--------------------------------------------------------------------
    #format job type
    #lower & strip
    js.jobType = js.jobType.str.lower().str.strip()

    #replace 'n/a' to nan
    js.jobType = js.jobType.replace('n/a',np.nan)

    # datebase
    # 1 = full time
    # 2 = part time
    # 3 = contract/temp
    # 4 = casual
    # 5 = internship
    # 6 = remote
    # 7 = hybrid

    #check internship
    # js.jobType = js.apply(lambda x: str(x['jobType']) + ','+ ' internship' if 'internship' in str(x['jobTitle']) else str(x['jobType']),axis = 1)
    js.jobType = js.apply(
    lambda x: str(x['jobType']) + ', internship'
    if re.search(r'(^|[\s\(\[\-])intern(ship)?([\s\)\]\-]|$)', str(x['jobTitle']))
    else str(x['jobType']),
    axis=1
    )

    #split jobType
    js.jobType = js.jobType.str.split(',')

    #check 1
    # print('jobtypes')
    # print(tabulate(js[['jobType']], headers='keys', tablefmt='grid'))

    #convert jobType to ids
    js['jobType'] = js.jobType.apply(lambda x: get_jobType_id(x))

    #remove empty list to nan
    js['jobType'] = js['jobType'].apply(lambda x: np.nan if len(x) == 0 else x)

    #--------------------------------------------------------------------
    #format jobCategory
    #lower & strip
    js.jobCategory = js.jobCategory.str.lower().str.strip()

    # 1	"information and communication technology"
    # 2	"accounting and finance"
    # 3	"administration and human resources"
    # 4	"retail and consumer products"
    # 5	"customer service"
    # 6	"sales and marketing"
    # 7	"food, beverage, hospitality and tourism"
    # 8	"engineering and maintenance"
    # 9	"education and training"
    # 10	"healthcare, beauty and medical"
    # 11	"manufacturing, transport and logistics"
    # 12	"advertising, arts, media and journalism"
    # 13	"construction"
    # 14	"science and research"
    # 15	"agriculture and conservation"
    # 16	"community and social services"
    # 17	"legal"
    # 18	"real estate and property"
    # 19	"mining, resources and energy"
    # 20	"government and defence"
    # 21	"self-employment"
    # 22	"sport and recreation"
    # 23	"trades and services"
    # 24	"executive and general management"
    # 25	"consulting and strategy"
    # 26	"other industries"

    js.jobCategory = js.jobCategory.apply(lambda x: get_jobCategory_id(x) if x is not None else np.nan)
    js.jobCategory = js.jobCategory.astype('string')

    #--------------------------------------------------------------------    
    #get post date

    #extract the text
    js.datePosted = js.datePosted.str.extract(r'Posted (\d+[hmd]) ago')

    js.datePosted = js.apply(lambda x: x['scrapedAt'] - get_clean_datePosted(str(x['datePosted'])),axis = 1) 

    #change dtypes to datetime
    #change dtypes to datetime
    js.datePosted = pd.to_datetime(js.datePosted, unit='s',utc=True)
    js.scrapedAt = pd.to_datetime(js.scrapedAt, unit='s',utc=True)

    #convert to malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    js.datePosted = js.datePosted.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)
    js.scrapedAt = js.scrapedAt.apply(lambda x: x.tz_convert(malaysia_tz) if pd.notna(x) else x)

    #--------------------------------------------------------------------
    #extract requiredSkills

    js.description = js.description.apply(lambda x: get_string_desc(x))

    #concatenate job title and description
    js.description = js.apply(lambda x: x['jobTitle'] + ' ' + x['description'],axis=1)

    #format the description
    #create a cleaner
    from skillNer.cleaner import Cleaner
    cleaner = Cleaner(
                to_lowercase=True,
                include_cleaning_functions=["remove_punctuation", "remove_extra_space"]
            )

    js.description = js.description.apply(lambda x: cleaner(x))
    #change description to string and requiredSkills to list
    js.description = js.description.astype('string')
    js.requiredSkills = js.requiredSkills.astype('object')
    
    #extract skills
    start_time = time.time()

    max_workers = 10
    nlp = None
    skill_extractor = None
    
    js['requiredSkills'] = mp_executor(js.description, get_skills, max_workers=10)

    end_time = time.time()
    print(f"Time taken to extract skills: {end_time - start_time} seconds")


    #---------------------------------------------------------------------
    # #testing without multiprocessing
    # #testing 100 rows
    # js = js.head(100)

    # #import
    # import spacy
    # from spacy.matcher import PhraseMatcher
    # # load default skills data base
    # from skillNer.general_params import SKILL_DB
    # # import skill extractor
    # from skillNer.skill_extractor_class import SkillExtractor
    # # init params of skill extractor
    # nlp = spacy.load("en_core_web_lg")
    # # init skill extractor
    # skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
    
    # js['requiredSkills'] = js.description.apply(lambda x: get_skills(x))

    # end_time = time.time()
    # print(f"Time taken to extract skills: {end_time - start_time} seconds")

    #--------------------------------------------------------------------
    #save to file
    #drop useless columns
    js.drop(columns=['salaryRange','description','_type'],axis = 1, inplace=True)

    #add source column
    js['source'] = 'jobstreet' 

    #rename location to state
    js.rename(columns={'location': 'state'}, inplace=True)

    #save to jsonl
    filename = 'cleaned_' + filename
    js.to_json(f'./data/js/cleaned/{filename}',orient='records', lines=True, force_ascii=False)


