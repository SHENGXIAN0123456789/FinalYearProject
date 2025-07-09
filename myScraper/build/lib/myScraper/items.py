# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MyscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

# jobTitle 
# companyName
# salaryRange
# requiredSkills/description
# location
# jobType - example: Full Time, Part Time, Internship
# jobCategory - example: IT/Sience & Technology, Accounting/Finance
# datePosted
# jobUrl
class Job(scrapy.Item):
    jobTitle = scrapy.Field()
    companyName = scrapy.Field()
    salaryRange = scrapy.Field()
    requiredSkills = scrapy.Field()
    description = scrapy.Field()
    location = scrapy.Field()
    jobType = scrapy.Field()
    jobCategory = scrapy.Field()
    datePosted = scrapy.Field()
    scrapedAt = scrapy.Field()
    jobUrl = scrapy.Field()