import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scraping.items import Recipe


class YummlySpider(CrawlSpider):
    name = "yummly"
    allowed_domains = ["yummly.com"]
    start_urls = ["http://yummly.com/"]

    rules = [Rule(LinkExtractor(), callback='recipe_urls', follow=True)]

    def recipe_urls(self, response):

        recipe_urls = response.xpath('//div[contains(@class, "recipe-card")]/@data_url').get_all()
        for url in recipe_urls:
            url = response.urljoin(url)



# has keywords for possible searches
    # https://mapi.yummly.com/mapi/v19/content/feed?id=Skillet-Chili-Cornbread-Pot-Pie-2596904&reviews-per-recipe=4

# main thing! (seo has keywords too!)
    # https://mapi.yummly.com/mapi/v19/content/feed?id=Skillet-Chili-Cornbread-Pot-Pie-2596904&reviews-per-recipe=4

# bit of url after recipe/ is the site id, can pass into api using this link:
    # https://mapi.yummly.com/mapi/v19/content/feed?id={_____________FEED ID_______________}


