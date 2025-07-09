import psycopg2
# imports
import spacy
from spacy.matcher import PhraseMatcher

# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor
all_languages = ['abkhaz', 'acehnese', 'acholi', 'afar', 'afrikaans', 'albanian', 'alur', 'amharic', 'arabic', 'armenian', 'assamese', 'avar', 'awadhi', 'aymara', 'azerbaijani', 'balinese', 'baluchi', 'bambara', 'baoulé', 'bashkir', 'basque', 'batak karo', 'batak simalungun', 'batak toba', 'belarusian', 'bemba', 'bengali', 'betawi', 'bhojpuri', 'bikol', 'bosnian', 'breton', 'bulgarian', 'buryat', 'cantonese', 'catalan', 'cebuano', 'chamorro', 'chechen', 'chichewa', 'chinese', 'chuukese', 'chuvash', 'corsican', 'crimean tatar', 'croatian', 'czech', 'danish', 'dari', 'dhivehi', 'dinka', 'dogri', 'dombe', 'dutch', 'dyula', 'dzongkha', 'english', 'esperanto', 'estonian', 'ewe', 'faroese', 'fijian', 'filipino', 'finnish', 'fon', 'french', 'frisian', 'friulian', 'fulani', 'ga', 'galician', 'georgian', 'german', 'greek', 'guarani', 'gujarati', 'haitian creole', 'hakha chin', 'hausa', 'hawaiian', 'hebrew', 'hiligaynon', 'hindi', 'hmong', 'hungarian', 'hunsrik', 'iban', 'icelandic', 'igbo', 'ilocano', 'indonesian', 'inuktut', 'irish', 'italian', 'jamaican patois', 'japanese', 'javanese', 'jingpo', 'kalaallisut', 'kannada', 'kanuri', 'kapampangan', 'kazakh', 'khasi', 'khmer', 'kiga', 'kikongo', 'kinyarwanda', 'kituba', 'kokborok', 'komi', 'konkani', 'korean', 'krio', 'kurdish', 'kyrgyz', 'lao', 'latgalian', 'latin', 'latvian', 'ligurian', 'limburgish', 'lingala', 'lithuanian', 'lombard', 'luganda', 'luo', 'luxembourgish', 'macedonian', 'madurese', 'maithili', 'makassar', 'malagasy', 'malay', 'malayalam', 'maltese', 'mam', 'manx', 'maori', 'marathi', 'marshallese', 'marwadi', 'mauritian creole', 'meadow mari', 'meiteilon', 'minang', 'mizo', 'mongolian', 'myanmar', 'nahuatl', 'ndau', 'ndebele', 'nepalbhasa', 'nepali', 'nko', 'norwegian', 'nuer', 'occitan', 'odia', 'oromo', 'ossetian', 'pangasinan', 'papiamento', 'pashto', 'persian', 'polish', 'portuguese', 'punjabi', 'quechua', 'qʼeqchiʼ', 'romani', 'romanian', 'rundi', 'russian', 'sami', 'samoan', 'sango', 'sanskrit', 'santali', 'scots gaelic', 'sepedi', 'serbian', 'sesotho', 'seychellois creole', 'shan', 'shona', 'sicilian', 'silesian', 'sindhi', 'sinhala', 'slovak', 'slovenian', 'somali', 'spanish', 'sundanese', 'susu', 'swahili', 'swati', 'swedish', 'tahitian', 'tajik', 'tamazight', 'tamil', 'tatar', 'telugu', 'tetum', 'thai', 'tibetan', 'tigrinya', 'tiv', 'tok pisin', 'tongan', 'tshiluba', 'tsonga', 'tswana', 'tulu', 'tumbuka', 'turkish', 'turkmen', 'tuvan', 'twi', 'udmurt', 'ukrainian', 'urdu', 'uyghur', 'uzbek', 'venda', 'venetian', 'vietnamese', 'waray', 'welsh', 'wolof', 'xhosa', 'yakut', 'yiddish', 'yoruba', 'yucatec maya', 'zapotec', 'zulu']

conn = psycopg2.connect(dbname='FYP', user='postgres', password='Fist-1211204126.', host='localhost', port='5432')

cursor = conn.cursor()

for skill_id, skill_info in SKILL_DB.items():
    skill_name = skill_info.get('skill_name') 
    skill_type = skill_info.get('skill_type') 
    is_hard = skill_type == 'Hard Skill'
    is_soft = skill_type == 'Soft Skill'
    is_cert = skill_type == 'Certification'
    is_lang = skill_name in all_languages
    cursor.execute(
        """
        INSERT INTO skills (external_key, skill_name, is_hard_skill, is_soft_skill, is_certification, is_language)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_key) DO NOTHING
        """,
        (skill_id, skill_name, is_hard, is_soft, is_cert, is_lang)
    )

conn.commit()
cursor.close()
conn.close()

print(len(SKILL_DB.items()))