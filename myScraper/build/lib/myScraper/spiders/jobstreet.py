import scrapy
from urllib.parse import urljoin
from datetime import datetime
import pytz
import re
from myScraper.items import Job

class JobstreetSpider(scrapy.Spider):
    name = "jobstreet"
    # allowed_domains = ["my.jobstreet.com"]
    # start_urls = ["https://my.jobstreet.com/"]
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
        # states = ["johor","kedah","kelantan","kuala-lumpur","labuan","melaka","negeri-sembilan","perak","perlis","pahang","penang","putrajaya","sabah","sarawak","selangor","terengganu"]
        # for state in states:
        #     for jobIndustry in jobIndustries:
        #         fullPageUrl = 'https://www.ricebowl.my/jobsearch/jobs-in-{state}?cat={jobIndustry}&sortBy=date&created=now-1d'.format(state=state,jobIndustry=jobIndustry)
        # testing : 
        # fullPageUrl = ['https://my.jobstreet.com/jobs-in-construction/in-Melaka?daterange=1','https://my.jobstreet.com/jobs-in-advertising-arts-media/in-Kuala-Lumpur?daterange=1&sortmode=ListedDate']
        # fullPageUrl = 'https://my.jobstreet.com/jobs-in-accounting/in-Kuala-Lumpur?daterange=1&sortmode=ListedDate'
        # testing : 
        # for url in fullPageUrl:
        #     yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'state': 'melaka', 'jobIndustry': 'construction'},meta={'render_js': True})
        states = ["Johor","Kedah","Kelantan","Kuala-Lumpur","Labuan","Melaka","Negeri-Sembilan","Perak","Perlis","Pahang","Penang","Putrajaya","Sabah","Sarawak","Selangor","Terengganu"]        
        classifications = ['accounting','administration-office-support','advertising-arts-media','banking-financial-services',
                           'call-centre-customer-service','ceo-general-management','community-services-development','construction',
                           'consulting-strategy','design-architecture','education-training','engineering','farming-animals-conservation',
                           'government-defence','healthcare-medical','hospitality-tourism','human-resources-recruitment','information-communication-technology',
                           'insurance-superannuation','legal','manufacturing-transport-logistics','marketing-communications','mining-resources-energy',
                           'real-estate-property','retail-consumer-products','sales','science-technology',
                           'self-employment','sport-recreation','trades-services'] 
        for state in states:
            for classification in classifications:
                #https://my.jobstreet.com/jobs-in-accounting/in-Melaka?daterange=1
                fullPageUrl = 'https://my.jobstreet.com/jobs-in-{classification}/in-{state}?daterange=31'.format(classification=classification,state=state)
                yield scrapy.Request(url=fullPageUrl, callback=self.parse, cb_kwargs={'state': state, 'classification': classification},meta={'render_js': True})

    def parse(self,response,state,classification):
        baseUrl = 'https://my.jobstreet.com'
        # checkPageLink = response.url
        # print(f'Page= {checkPageLink}')
        allJobsLink = response.xpath('//a[@data-automation="job-list-view-job-link"]/@href').getall()
        if allJobsLink:
            # print(len(allJobsLink))
            for link in allJobsLink:

                fullLink = urljoin(baseUrl, link)
                
                # print(fullLink)
                yield scrapy.Request(
                    url = fullLink,
                    cb_kwargs= {
                        'state': state,
                        'classification': classification,
                        'fullLink': fullLink
                    },
                    callback=self.parse_details,
                    meta={'render_js': True}
                )

        nextPageLink = response.xpath('//a[@aria-label="Next" and @title="Next"]/@href').get()
        if nextPageLink:
            nextPageFullLink = urljoin(baseUrl, nextPageLink)
            # print(f'Moving to next page: {nextPageFullLink}')
            yield scrapy.Request(
                url = nextPageFullLink,
                cb_kwargs= {
                    'state': state,
                    'classification': classification
                },
                callback=self.parse,
                meta={'render_js': True}
            )


    def parse_details(self,response,state,classification,fullLink):
        try:
            job = Job()
            #<h1 class="gg45di0 _1ubeeig4z _1oxsqkd0 _1oxsqkdl _18ybopc4 _1oxsqkds _1oxsqkd21" data-automation="job-detail-title">Associate, Audit and Assurance (Melaka Office)</h1>
            job['jobTitle'] = response.xpath('.//h1[@data-automation="job-detail-title"]/text()').get() or "N/A"
            #<span class="gg45di0 _1ubeeig4z _1ubeeigi7 _1oxsqkd0 _1oxsqkd1 _1oxsqkd21 _18ybopc4 _1oxsqkda" data-automation="advertiser-name">Crowe Malaysia PLT<!-- --> <span class="gg45di0 _1ubeeig57"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" xml:space="preserve" focusable="false" fill="currentColor" width="16" height="16" class="gg45di0 _1ubeeig57 _1ubeeig5f mtt2v30 mtt2v32 mtt2v33 mtt2v34" aria-hidden="true"><path d="m20.4 4.1-8-3c-.2-.1-.5-.1-.7 0l-8 3c-.4.1-.7.5-.7.9v7c0 6.5 8.2 10.7 8.6 10.9.1.1.2.1.4.1s.3 0 .4-.1c.4-.2 8.6-4.4 8.6-10.9V5c0-.4-.3-.8-.6-.9zM19 12c0 4.5-5.4 7.9-7 8.9-1.6-.9-7-4.3-7-8.9V5.7l7-2.6 7 2.6V12z"></path><path d="M9.7 11.3c-.4-.4-1-.4-1.4 0s-.4 1 0 1.4l2 2c.2.2.5.3.7.3s.5-.1.7-.3l4-4c.4-.4.4-1 0-1.4s-1-.4-1.4 0L11 12.6l-1.3-1.3z"></path></svg></span></span>
            job['companyName'] = response.xpath('.//span[@data-automation="advertiser-name"]/text()').get() or "N/A"
            #job-detail-salary job-detail-add-expected-salary
            #<span class="gg45di0 _1ubeeig4z _1oxsqkd0 _1oxsqkd1 _1oxsqkd22 _18ybopc4 _1oxsqkd7" data-automation="job-detail-add-expected-salary">Add expected salary to your profile for insights</span>
            #<span class="gg45di0 _1ubeeig4z _1oxsqkd0 _1oxsqkd1 _1oxsqkd21 _18ybopc4 _1oxsqkd7" data-automation="job-detail-salary">RM&nbsp;3,000 – RM&nbsp;3,500 per month</span>
            job['salaryRange'] = response.xpath('.//span[@data-automation="job-detail-add-expected-salary"]/text()').get() or response.xpath('.//span[@data-automation="job-detail-salary"]/text()').get() or "N/A"
            
            job['requiredSkills'] = None
            #<div data-automation="jobAdDetails"><div class="gg45di0 _1apz9us0"><p><strong>Why Join Us?</strong></p><ul><li><p><strong>Ownership &amp; Impact&nbsp;</strong>– Manage full-set accounts and essential financial tasks that contribute to business success.</p></li><li><p><strong>Career Growth&nbsp;– </strong>Develop your expertise in a supportive environment with exposure to diverse financial functions.</p></li><li><p><strong>Work-Life Balance&nbsp;</strong>– A structured role with clear responsibilities and minimal overtime.</p></li><li><p><strong>Collaborative Team&nbsp;–</strong> Join a workplace that values teamwork, open communication, and professional development.</p></li></ul><p><strong>&nbsp;</strong></p><p><strong>What you will be doing (Key Responsibilities):</strong></p><ul><li><p>Manage day-to-day accounting tasks (AP/AR, invoicing, reconciliations).</p></li><li><p>Prepare full-set accounts and financial reports.</p></li><li><p>Assist with administrative duties to ensure smooth operations.</p></li></ul><p><strong>&nbsp;</strong></p><p><strong>What do we need from you (Job Requirements):</strong></p><ul><li><p>Diploma in Accounting or a related field.</p></li><li><p>Minimum 2 years of experience in accounting or finance.</p></li><li><p>Proficiency in AutoCount Software and MS Office.</p></li><li><p>Mandarin language skills have added advantage.</p></li></ul><p><strong>&nbsp;</strong></p><p><strong>职位优势：</strong></p><ul><li><p><strong>自主性与影响力</strong>&nbsp;– 负责全盘账目及关键财务工作，助力业务发展。</p></li><li><p><strong>职业成长&nbsp;</strong>– 在支持性环境中提升专业技能，接触多元化财务工作。</p></li><li><p><strong>工作与生活平衡&nbsp;</strong>– 职责明确，加班少，工作安排合理。</p></li><li><p><strong>团队协作&nbsp;</strong>– 加入重视合作、开放沟通与专业成长的工作环境。</p></li></ul><p><strong>&nbsp;</strong></p><p><strong>主要职责：</strong></p><ul><li><p>处理日常会计工作（应付/应收账款、发票、对账等）。</p></li><li><p>编制全盘账目及财务报表。</p></li><li><p>协助行政事务以确保高效运作。</p></li></ul><p><strong>&nbsp;</strong></p><p><strong>任职要求：</strong></p><ul><li><p>会计或相关专业文凭。</p></li><li><p>至少2年财务/会计工作经验。</p></li><li><p>熟练使用AutoCount软件及MS Office。</p></li><li><p>中文沟通能力为加分项。</p></li></ul></div></div>
            job['description'] = response.xpath('.//div[@data-automation="jobAdDetails"]//text()').getall() or "N/A"
            
            job['location'] = state
            
            job['jobType'] = response.xpath('//span[@data-automation="job-detail-work-type"]/a/text()').get() or response.xpath('//span[@data-automation="job-detail-work-type"]/text()').get() or "N/A"
            
            job['jobCategory'] = classification 
            #div class="gg45di0 _1ubeeig5b _1ubeeighf _1ubeeig6z", second child
            # job['datePosted'] = response.xpath('.//div[contains(@class, "gg45di0") and contains(@class, "_1ubeeig5b") and contains(@class, "_1ubeeighf") and contains(@class, "_1ubeeig6z")]/*[2]/text()').get() or "N/A"
            job['datePosted'] = (response.xpath('.//div[contains(@class, "gg45di0") and contains(@class, "_1ubeeig5b") and contains(@class, "_1ubeeighf") and contains(@class, "_1ubeeig6z")]/*[2]/text()').get()
            or (re.search(r'Posted \d+\w? ago', response.text).group(0) if re.search(r'Posted \d+\w? ago', response.text) else "N/A")
            or "N/A")

            malaysiaTimezone = pytz.timezone('Asia/Kuala_Lumpur')
            now = datetime.now(malaysiaTimezone)
            job['scrapedAt'] = now.timestamp()
            
            job['jobUrl'] = fullLink
            yield job
        except Exception as e:
            self.logger.error(f"Error parsing details for {response.url}: {e}")
