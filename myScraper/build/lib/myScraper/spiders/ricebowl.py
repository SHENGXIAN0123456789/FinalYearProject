import scrapy
from urllib.parse import urljoin
from myScraper.items import Job
from datetime import datetime
import pytz

class RicebowlSpider(scrapy.Spider):
    name = "ricebowl"
    # allowed_domains = ["www.ricebowl.my"]
    # start_urls = ["https://www.ricebowl.my"]
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


    def start_requests(self):
        states = ["johor","kedah","kelantan","kuala-lumpur","labuan","melaka","negeri-sembilan","perak","perlis","pahang","penang","putrajaya","sabah","sarawak","selangor","terengganu"]
        jobIndustries = ["468-other","470-fnb","457-account","451-admin","454-retail","459-transportation_logistic","467-social_service","469-sales","460-journalism","453-customer_service",
                         "462-it","455-construction","458-art_design","464-health_beauty","456-education","465-engineering","461-manufacturing","452-hotel","463-rnd","466-agriculture"]
        for state in states:
            for jobIndustry in jobIndustries:
                fullPageUrl = 'https://www.ricebowl.my/jobsearch/jobs-in-{state}?cat={jobIndustry}&sortBy=date&created=now-30d'.format(state=state,jobIndustry=jobIndustry)
                #testing : fullPageUrl = 'https://www.ricebowl.my/jobsearch/jobs-in-melaka?cat=458-art_design&sortBy=relevance'
                #testing : yield scrapy.Request(url=fullPageUrl, callback=self.parse, cb_kwargs={'state': 'melaka', 'jobIndustry': '459-transportation'},meta={'render_js': True})
                yield scrapy.Request(url=fullPageUrl, callback=self.parse, cb_kwargs={'state': state, 'jobIndustry': jobIndustry},meta={'render_js': True})



    def parse(self, response,state,jobIndustry):
        baseUrl = 'https://www.ricebowl.my'
        allJobsLink = response.xpath('.//div[contains(@class,"font-bold") and contains(@class,"text-truncate-2-line")]/a[contains(@class,"has-text-dark") and contains(@class,"is-hover-changed")]/@href').getall()
        if allJobsLink:
            removeDupJobsLink = list(dict.fromkeys(allJobsLink))
            # print(len(removeDupJobsLink))
            for link in removeDupJobsLink:
                fullLink = urljoin(baseUrl, link)
                yield scrapy.Request(
                    url = fullLink,
                    cb_kwargs= {
                        'state': state,
                        'jobIndustry': jobIndustry,
                        'fullLink': fullLink
                    },
                    callback=self.parse_details,
                    meta={'render_js': True}
                )

        nextPageLink = response.xpath('//a[contains(@class,"pagination-next")]/@href').get() or None
        if nextPageLink:
            nextPageFullLink = urljoin(baseUrl, nextPageLink)
            # print(f'Moving to next page: {nextPageFullLink}')
            yield scrapy.Request(
                url = nextPageFullLink,
                cb_kwargs= {
                    'state': state,
                    'jobIndustry': jobIndustry
                },
                callback=self.parse,
                meta={'render_js': True}
            )

    def parse_details(self,response,state,jobIndustry,fullLink):
        try:
            job = Job()
            job['jobTitle'] = response.xpath('//div[contains(@class,"card-content")]//h2/text()').get() or "N/A"
            job['companyName'] = response.xpath('//div[contains(@class,"media-content")]//h2/text()').get() or "N/A"
            job['salaryRange'] = response.xpath('//div[contains(@class,"column") and contains(@class,"is-paddingless")]//span[contains(@class,"has-text-primary") and contains(@class,"has-text-weight-semibold")]/text()').get() or "N/A"
            job['requiredSkills'] = response.xpath('//div[contains(@class,"skills")]//div[contains(@class,"job-detail-text")]//span/text()').getall() or "N/A"
            job['description'] = response.xpath('//div[contains(@class,"job-detail-text")]/div[@id="checker"]//text()').getall() or "N/A"
            job['location'] = state
            job['jobType'] = response.xpath('//a[contains(@class,"jobtype-link")]/span/text()').getall() or "N/A"
            job['jobCategory'] = jobIndustry 
            job['datePosted'] = response.xpath('//div[contains(@class,"card-content")]//div[4]/div/span/text()').get() or "N/A"
            malaysiaTimezone = pytz.timezone('Asia/Kuala_Lumpur')
            now = datetime.now(malaysiaTimezone)
            job['scrapedAt'] = now.timestamp()
            job['jobUrl'] = fullLink
            yield job
        except Exception as e:
            self.logger.error(f"Error parsing details for {response.url}: {e}")