import scrapy
from urllib.parse import urljoin
from urllib.parse import quote_plus
from myScraper.items import Job
import pytz
from datetime import datetime

class JoraSpider(scrapy.Spider):
    name = "jora"
    # allowed_domains = ["my.jora.com"]
    # start_urls = ["https://my.jora.com/"]
    apiKey = '53781916-783c-498e-b69b-0f5d9b962203'
    custom_settings = {
        'SCRAPEOPS_API_KEY': apiKey,
        'SCRAPEOPS_FAKE_HEADERS_ENABLED': True,
        'SCRAPEOPS_PROXY_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'myScraper.middlewares.ScrapeOpsFakeBrowserHeadersMiddleware': 400,
            'myScraper.middlewares.ScrapeOpsProxyMiddleware': 725,
        },
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408,429],
        'RETRY_EXCEPTIONS': [
            'twisted.internet.error.TimeoutError',
            'twisted.internet.error.ConnectionRefusedError'
        ]
    }
    # fullPageUrl = 'https://my.jora.com/j?sp=search&trigger_source=serp&r=0&a=24h&q=human+resource+manager&l=Johor'
    search_keywords = {
        "Information and Communication Technology": 
        [
            "software developer", 
            "web developer", 
            "backend developer", 
            "frontend developer",
            "IT support", 
            "system administrator", 
            "cybersecurity", 
            "data analyst", 
            "cloud engineer"
        ],
        "Accounting and Finance": 
        [
            "accountant", 
            "auditor", 
            "finance executive",  
            "tax consultant",
            "financial analyst", 
            "accounts assistant"
        ],
        "Administration and Human Resources": 
        [
            "admin assistant", 
            "office administrator", 
            "human resource", 
            "recruiter", 
            "HR executive",
            "personal assistant", 
            "clerk"
        ],
        "Retail and Consumer Products": 
        [
            "retail assistant", 
            "retail manager", 
            "store supervisor", 
            "sales promoter", 
            "cashier"
        ],
        "Customer Service": 
        [
            "customer service", 
            "call center", 
            "support specialist",
            "customer support",
            "helpdesk"
        ],
        "Sales and Marketing": [
            "sales executive", 
            "business development", 
            "marketing executive", 
            "digital marketing",
            "account manager", 
            "telemarketer", 
            "sales manager"
        ],
        "Food, Beverage, Hospitality and Tourism": 
        [
            "chef", 
            "waiter", 
            "kitchen helper", 
            "restaurant manager", 
            "hotel front desk",
            "housekeeping", 
            "barista", 
            "tour guide"
        ],

        "Engineering and Maintenance": 
        [
            "mechanical engineer", 
            "electrical engineer", 
            "maintenance technician", 
            "civil engineer",
            "engineering assistant", 
            "facility technician"
        ],
        "Education and Training": 
        [
            "teacher", 
            "tutor", 
            "lecturer", 
            "education consultant", 
            "teaching assistant"
        ],
        "Healthcare, Beauty and Medical": 
        [
            "nurse", 
            "clinic assistant", 
            "pharmacist", 
            "beautician", 
            "dermatologist", 
            "nutritionist",
            "therapist",
            "medical assistant"
        ],

        "Manufacturing, Transport and Logistics": 
        [
            "logistics coordinator", 
            "warehouse assistant", 
            "driver", 
            "delivery rider",
            "forklift operator", 
            "factory worker", 
            "production operator", 
            "supply chain executive"
        ],

        "Advertising, Arts, Media and Journalism": 
        [
            "graphic designer", 
            "art director", 
            "creative writer", 
            "copywriter",
            "multimedia designer", 
            "journalist", 
            "media executive", 
            "content creator"
        ],

        "Construction": [
            "site supervisor", 
            "construction worker", 
            "quantity surveyor", 
            "project engineer",
            "site engineer", 
            "foreman"
        ],

        "Science and Research": 
        [
            "research assistant", 
            "lab technician", 
            "data scientist",
            "scientific officer",
            "research and development engineer", 
            "research analyst"
        ],

        "Agriculture and Conservation": 
        [
            "farm worker", 
            "agronomist", 
            "aquaculture technician", 
            "agriculture executive",
            "plantation supervisor", 
            "environmental officer"
        ],

        "Community and Social Services": 
        [
            "social worker", 
            "counselor", 
            "welfare officer", 
            "ngo officer", 
            "case manager"
        ],

        "Legal": 
        [
            "lawyer", 
            "legal advisor", 
            "legal executive", 
            "paralegal"
        ],

        "Real Estate and Property": 
        [
            "property agent", 
            "real estate negotiator", 
            "valuation executive",
            "property manager", 
            "leasing consultant"
        ],

        "Mining, Resources and Energy": 
        [
            "mining engineer", 
            "geologist", 
            "drilling technician", 
            "energy consultant",
            "environmental engineer"
        ],

        "Government and Defence": 
        [
            "government officer", 
            "civil servant", 
            "army", 
            "navy", 
            "defence personnel",
            "customs officer"
        ],

        "Self Employment": 
        [
            "freelancer", 
            "self employed", 
            "gig worker", 
            "independent contractor"
        ],

        "Sport and Recreation": 
        [
            "fitness trainer", 
            "coach", "sports coordinator", 
            "recreation officer",
            "gym instructor", 
            "swimming coach"
        ],

        "Trades and Services": 
        [
            "electrician", 
            "plumber", 
            "technician", 
            "mechanic", 
            "pest control", 
            "handyman", 
            "AC technician", 
            "aircon technician"
        ],

        "Executive and General Management": 
        [
            "general manager", 
            "ceo", 
            "managing director", 
            "chief officer", 
            "operations manager"
        ],
        "Consulting and Strategy": 
        [
            "business consultant", 
            "management consultant", 
            "strategy analyst", 
            "project consultant"
        ],
        "Other Industries": 
        [
            "general worker", 
            "unclassified", 
            "open category", 
            "miscellaneous jobs"
        ]
    }

    @staticmethod
    def getFullPageUrl(keyword,state):
        baseFullPageUrl = 'https://my.jora.com/j?sp=search&trigger_source=serp&r=0&a=24h&q={keyword}&l={state}'
        formattedFullPageUrl = baseFullPageUrl.format(keyword=quote_plus(keyword),state=quote_plus(state))
        return formattedFullPageUrl

    states = ["johor","kedah","kelantan","kuala lumpur","labuan","melaka","negeri sembilan","perak","perlis","pahang","penang","putrajaya","sabah","sarawak","selangor","terengganu"]


    def start_requests(self):
        for category, keywords in JoraSpider.search_keywords.items():
            for keyword in keywords:
                for state in JoraSpider.states:
                    fullPageUrl = JoraSpider.getFullPageUrl(keyword,state)
                    yield scrapy.Request(url=fullPageUrl, callback=self.parse, cb_kwargs={'state': state, 'category': category},meta={'render_js': True})

    def parse(self, response,state,category):
        baseUrl = 'https://my.jora.com/'
        allJobsLink = response.xpath('//a[contains(@class,"job-link") and contains(@class,"-desktop-only")]/@href').getall()
        # print('allJobsLink = ',len(allJobsLink))
        if allJobsLink:
            for link in allJobsLink:
                fullLink = urljoin(baseUrl, link)
                # print(f'fullLink = {fullLink}')
                yield scrapy.Request(
                    url = fullLink,
                    cb_kwargs= {
                        'state': state,
                        'category': category,
                        'fullLink': fullLink
                    },
                    callback=self.parse_details,
                    meta={'render_js': True}
                )


        nextPageLink = response.xpath('//a[@class="next-page-button"]/@href').get()
        if nextPageLink:
            nextPageFullLink = urljoin(baseUrl, nextPageLink)
            yield scrapy.Request(url = nextPageFullLink, callback=self.parse, meta={'render_js': True},cb_kwargs = {'state':state, 'category': category})


    def parse_details(self,response,state,category,fullLink):
        try:
            job = Job()
            job['jobTitle'] = response.xpath('//div[@id="job-info-container"]/h1/text()').get() or "N/A"
            #from other sources
            job['companyName'] = response.xpath('//div[@id="company-location-container"]//*[contains(@class,"company")]/text()').get() or "N/A"
            job['salaryRange'] = response.xpath('//div[@id="job-info-container"]/*[3]/div[@class="content"]/text()').get() or "N/A"
            job['requiredSkills'] = None
            job['description'] = response.xpath('//div[@id="job-description-container"]//text()').getall() or "N/A"
            job['location'] = state
            job['jobType'] = response.xpath('//div[@id="job-info-container"]/*[4]/div[@class="content"]/text()').get() or "N/A"
            job['jobCategory'] = category 
            job['datePosted'] = response.xpath('//span[@class="listed-date"]/text()').get() or "N/A"
            malaysiaTimezone = pytz.timezone('Asia/Kuala_Lumpur')
            now = datetime.now(malaysiaTimezone)
            job['scrapedAt'] = now.timestamp()
            #data cleaning ads
            job['jobUrl'] = fullLink
            yield job
        except Exception as e:
            self.logger.error(f"Error parsing details for {response.url}: {e}")