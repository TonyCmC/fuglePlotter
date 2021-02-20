import configparser

import requests
import json
from decimal import Decimal


class US10YCrawler:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.tg_token = config['TELEGRAM']['ACCESS_TOKEN']
        self.chat_id = config['TELEGRAM']['CHAT_ID']

    def send_msg(self, msg):
        url = 'https://api.telegram.org/bot{0}/sendMessage'.format(self.tg_token)

        body_payload = {
            'chat_id': self.chat_id,
            'text': str(msg)
        }
        res = requests.post(url, data=body_payload)
        print(res.text)

    def parse_finnhub(self):
        finnhub_url = 'https://finnhub.io/api/v1/forex/rates?base=USD&token=bvpioln48v6s8ntrvs8g'
        res = requests.get(finnhub_url)
        parsed_res = json.loads(res.text)
        return Decimal(parsed_res.get('quote').get('TWD'))

    def parse_by_ticker(self, ticker):
        endpoint = 'https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol'
        params = {
            'symbols': ticker,
            'requestMethod': 'itv',
            'noform': '1',
            'partnerId': '2',
            'fund': '1',
            'exthrs': '1',
            'output': 'json',
            'events': '1'
        }
        res = requests.get(endpoint, params=params)
        parsed_res = json.loads(res.text)
        price_bars = parsed_res.get('FormattedQuoteResult').get('FormattedQuote')
        change_type = price_bars[0].get('changetype')
        if change_type == 'DOWN':
            stock_mark = '▼ '
        elif change_type == 'UP':
            stock_mark = '▲ '
        else:
            stock_mark = ' '

        return {
            'last_price': price_bars[0].get('last').replace('%', ''),
            'change': stock_mark + price_bars[0].get('change'),
            'last_timedate': price_bars[0].get('last_time')
        }

    def get_us_10y(self):
        us10y = self.parse_by_ticker('US10Y')
        tsm_adr = self.parse_by_ticker('TSM')
        usd_twd = self.parse_finnhub()
        tsm_dividend = Decimal('10')  # 2.5*4
        tsm_transferred = round(Decimal(tsm_adr.get('last_price')) * usd_twd / 5, 2)
        tsm_dividend_yield = round(tsm_dividend / tsm_transferred * 100, 2)
        us10y_yield = Decimal(us10y.get('last_price'))
        foreign_invest_leave_rate = (tsm_dividend_yield - us10y_yield) * 100
        result = '#外資逃難指數 \n'\
                 '資料時間: {market_time}\n' \
                 '美國10年公債利率 {us10y_rate} {us10y_changed}\n' \
                 '台積電ADR {tsmadr_price} {tsmadr_changed}\n' \
                 '台積電ADR 轉換台股價格: {tsm_transferred_price}\n' \
                 '外資逃難指數 {leave_rate}'.format(market_time=us10y.get('last_timedate'),
                                              us10y_rate=us10y.get('last_price'),
                                              us10y_changed=us10y.get('change'),
                                              tsmadr_price=tsm_adr.get('last_price'),
                                              tsmadr_changed=tsm_adr.get('change'),
                                              tsm_transferred_price=tsm_transferred,
                                              leave_rate=str(foreign_invest_leave_rate) + '%')
        self.send_msg(result)
