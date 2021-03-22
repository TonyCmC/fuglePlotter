from apscheduler.schedulers.blocking import BlockingScheduler
from US10YCrawler import US10YCrawler
from apscheduler.triggers.cron import CronTrigger


us10y = US10YCrawler()

scheduler = BlockingScheduler()
cron1 = CronTrigger(day_of_week='mon-fri', hour='8', minute='51', timezone='Asia/Taipei')

scheduler.add_job(us10y.get_us_10y, cron1)
scheduler.start()
