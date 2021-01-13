import configparser
import datetime
import json
import operator

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 導入蠟燭圖套件
import mpl_finance as mpf
# 專門做『技術分析』的套件
from talib import abstract

config = configparser.ConfigParser()
config.read('config.ini')


class FugleKLinePlotter:
    # define the font attributes of title
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 20
    plt.style.use('dark_background')

    api_url = config['FUGLE']['API_URL']

    def __init__(self, stock_id, f_name):
        self.stock_id = stock_id
        self.stock_name = ''
        self.f_name = f_name
        self.data = {}
        self.market_time = datetime.datetime.now()
        self.market_time_set = []
        self.last_closed = 0.0
        self.highest_price = 0.0
        self.lowest_price = 0.0
        self.is_stock = True
        self.get_price_plot()
        self.get_price_info_of_stock()

    def chart_x_axis_fixer(self, chart_dict):
        pass

    def get_price_plot(self):
        api_for_stock = self.api_url + '/chart?symbolId={stock}&apiToken={token}'.format(stock=self.stock_id,
                                                                                         token=config['FUGLE']['TOKEN'])
        res = requests.get(api_for_stock)
        self.data = json.loads(res.text)
        price_set = self.data.get('data').get('chart')
        with open('tmp2.log', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data))
        self.market_time = self.isoformat_transfer(self.data.get('data').get('info').get('lastUpdatedAt'))

        time_series = list(price_set.keys())
        new_price_dict = {}

        for idx, e in enumerate(time_series):
            ticker_stack = datetime.timedelta(minutes=1)
            tmp_price_dict = {}
            content_stack = price_set.get(e)
            if content_stack['volume'] >= 1000:
                content_stack['volume'] = int(content_stack['volume'] / 1000)
            if idx == 0:
                tmp_price_dict[self.isoformat_transfer(time_series[idx])] = content_stack
            else:
                # 取上一次內容
                content_stack = price_set.get(time_series[idx])
                # 計算 這次減掉上次tick，計算共漏掉幾分鐘
                ticker_minute_diff = (self.isoformat_to_datetime(time_series[idx]) - self.isoformat_to_datetime(
                    time_series[idx - 1]) - datetime.timedelta(minutes=1))

                # 遺漏分鐘數不等於一分鐘
                if ticker_minute_diff != datetime.timedelta(minutes=0):
                    # 計算遺漏的ticker數量
                    missing_ticker = ticker_minute_diff / datetime.timedelta(minutes=1)
                    # 迴圈補遺漏
                    for tick in range(int(missing_ticker)):
                        previous_content_stack = price_set.get(time_series[idx - 1])
                        current_timestamp = (self.isoformat_to_datetime(time_series[idx - 1]) + ticker_stack).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        ticker_stack += datetime.timedelta(minutes=1)
                        previous_content_stack_with_zero_vol = previous_content_stack.copy()
                        previous_content_stack_with_zero_vol['volume'] = 0
                        tmp_price_dict[current_timestamp] = previous_content_stack_with_zero_vol
                tmp_price_dict[self.isoformat_transfer(time_series[idx])] = content_stack
            new_price_dict.update(tmp_price_dict)
        arranged_dict = {
            "time": list(new_price_dict.keys()),
            "open": list(map(operator.itemgetter('open'), list(new_price_dict.values()))),
            "high": list(map(operator.itemgetter('high'), list(new_price_dict.values()))),
            "low": list(map(operator.itemgetter('low'), list(new_price_dict.values()))),
            "close": list(map(operator.itemgetter('close'), list(new_price_dict.values()))),
            "volume": list(map(operator.itemgetter('volume'), list(new_price_dict.values()))),
        }
        return arranged_dict

    def get_price_info_of_stock(self):
        api_for_stock = self.api_url + '/meta?symbolId={stock}&apiToken={token}'.format(stock=self.stock_id,
                                                                                        token=config['FUGLE']['TOKEN'])
        res = requests.get(api_for_stock)
        data = json.loads(res.text)
        self.stock_name = data.get('data').get('meta').get('nameZhTw')
        self.last_closed = float(round(data.get('data').get('meta').get('priceReference'), 2))
        self.highest_price = float(round(data.get('data').get('meta').get('priceHighLimit') or
                                         round(float(self.last_closed) * 1.1, 2)))
        self.lowest_price = float(round(data.get('data').get('meta').get('priceLowLimit') or
                                        round(float(self.last_closed) * 0.9, 2)))
        print('self.highest_price: ', self.highest_price)
        print('self.lowest_price: ', self.lowest_price)

        # 針對興櫃公司 or 無昨收的股票(通常為第一天興櫃之類的) 處理
        if 'volumePerUnit' not in data.get('data').get('meta').keys() or self.last_closed == 0:
            self.is_stock = False

    def isoformat_to_datetime(self, datetime_string):
        raw_datetime = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        raw_datetime += datetime.timedelta(hours=8)
        return raw_datetime

    def isoformat_transfer(self, datetime_string):
        raw_datetime = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        raw_datetime += datetime.timedelta(hours=8)
        parsed_datetime_string = raw_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return parsed_datetime_string

    def draw_plot(self):
        arranged_dict = self.get_price_plot()
        print(arranged_dict)

        # 針對第一次興櫃公司處理 (無last_closed資訊則用開盤價當作基準)
        if self.last_closed == 0:
            self.last_closed = arranged_dict.get('open')[0]

        if self.is_stock is False:
            if self.highest_price < max(arranged_dict.get('close')):
                self.highest_price = max(arranged_dict.get('close'))
            if self.lowest_price > min(arranged_dict.get('close')):
                self.lowest_price = min(arranged_dict.get('close'))

        df = pd.DataFrame(arranged_dict)

        fig = plt.figure(figsize=(10, 8))

        # 用add_axes創建副圖框
        ax = fig.add_axes([0.1, 0.3, 0.8, 0.6])
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.2])

        ax2.set_xticks(range(0, 270, 54))
        ax2.set_xticklabels(['09', '10', '11', '12', '13'])

        ax.set_ylim(round(self.lowest_price, 2), round(self.highest_price, 2))

        mpf.candlestick2_ohlc(ax, df['open'], df['high'], df['low'], df['close'],
                              width=1, colorup='r', colordown='springgreen', alpha=0.75)

        mpf.volume_overlay(ax2, df['open'], df['close'], df['volume'],
                           colorup='r', colordown='springgreen', width=1, alpha=0.8)

        # 畫均線圖
        sma_5 = abstract.SMA(df, 5)
        sma_30 = abstract.SMA(df, 30)

        # 開盤價水平線
        ax.plot([0, 270], [self.last_closed, self.last_closed])

        # 5MA + 30MA
        ax.plot(sma_5, label='5MA')
        ax.plot(sma_30, label='30MA')

        current_price_list = [x for x in arranged_dict['close'] if x is not None]
        current_closed_price = current_price_list[len(current_price_list) - 1]

        if current_closed_price > self.last_closed:
            stock_color = 'brown'
            stock_mark = '▲'
        elif current_closed_price < self.last_closed:
            stock_color = 'springgreen'
            stock_mark = '▼'
        else:
            stock_color = 'ivory'
            stock_mark = '-'

        current_volume_list = [x for x in arranged_dict['volume'] if x is not None]

        title_diff = round(current_closed_price - self.last_closed, 2)
        title_diff_percent = round(title_diff / self.last_closed * 100, 2)

        title = '{name}({id})                               {time}     \n'.format(name=self.stock_name,
                                                                                  id=self.stock_id,
                                                                                  time=self.market_time)
        sub_title = '{price}   {mark}{diff} ({percent}%)                             成交量: {volume}'.format(
            volume=str(int(sum(current_volume_list))),
            price=current_closed_price,
            mark=stock_mark,
            diff=title_diff,
            percent=title_diff_percent)
        plt.suptitle(sub_title, x=0.385, y=0.93, size='xx-large', color=stock_color)
        title_obj = ax.set_title(title, loc='Left', pad=0.5)
        # plt.getp(title_obj)  # print out the properties of title
        # plt.getp(title_obj, 'text')  # print out the 'text' property for title
        plt.setp(title_obj, color=stock_color)  # set the color of title to red
        ax.legend(fontsize='x-large')
        file_name = self.stock_id + '-' + self.f_name
        fig.savefig('images/lower_{file_name}.png'.format(file_name=file_name), dpi=100)
        fig.savefig('images/{file_name}.png'.format(file_name=file_name))
