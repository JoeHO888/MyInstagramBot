import asyncio
import logging
import aiohttp
import time
import random


class AsyncCrawler:

    def __init__(self, root_urls, extract_extra_urls_needed, max_concurrency):
        self.seen_urls = set()
        self.loop = asyncio.new_event_loop()
        self.data = []
        self.pending_urls = root_urls
        self.max_concurrency = max_concurrency
        self.extract_extra_urls_needed = extract_extra_urls_needed
        
    def run(self):
        a = time.time()
        self.loop.run_until_complete(self.extract_multi_async())
        b = time.time()
        logging.info("Job Completed in " + str(b-a) +" s")

    async def extract_multi_async(self):
        while self.pending_urls:
            urls_to_fetch = []
            tasks = []
            for _ in range(min(self.max_concurrency,len(self.pending_urls))):
                urls_to_fetch.append(self.pending_urls.pop(0))
            
            for url in urls_to_fetch:
                task = asyncio.create_task(self.extract_async(url))
                tasks.append(task)

            for task in tasks:
                await task
    
    async def extract_async(self,url):
        if url not in self.seen_urls:
            html = await self.request_async(url)
            self.seen_urls.add(url)
            
            data = self.parse(html)
            self.data.append(data)

            if self.extract_extra_urls_needed:
                new_urls = self.extract_url(html)
                self.pending_urls += new_urls

    async def request_async(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    def extract_url(self, html):
        raise NotImplementedError
        # return [html]

    def parse(self, html):
        raise NotImplementedError
        # return html
