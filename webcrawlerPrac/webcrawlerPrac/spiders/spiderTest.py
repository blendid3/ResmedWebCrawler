import scrapy
class spiderTest(scrapy.Spider):
    name = "posts"
    start_urls = ['https://www.zyte.com/blog/']
    def parse(self, response):

        # print("number is %d", page)
        filename = 'posts-%s.html' % 2
        with open(filename, 'wb') as f:
            f.write(response.body)
        pass