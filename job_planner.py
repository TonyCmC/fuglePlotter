from apscheduler.schedulers.blocking import BlockingScheduler

from Services.CostcoCrawler import CostcoCrawler

ccl = CostcoCrawler()

scheduler = BlockingScheduler()

scheduler.add_job(ccl.crawler, 'interval', id='crawl_every_hour', minutes=30)
scheduler.start()
