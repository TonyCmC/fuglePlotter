import configparser
import datetime
import json
import operator
import os
import re

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 導入蠟燭圖套件
import mpl_finance as mpf
# 專門做『技術分析』的套件
from talib import abstract

from definitions import ROOT_DIR

config = configparser.ConfigParser()
config.read('config.ini')


class FugleKLinePlotter:
    # define the font attributes of title
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 20
    plt.style.use('dark_background')

    api_url = config['FUGLE']['API_URL']

    def __init__(self, stock_id, file_name):
        self.stock_id = stock_id
        self.stock_name = ''
        self.file_name = file_name
        self.data = {}
        self.market_time = datetime.datetime.now()
        self.last_closed = 0.0
        self.highest_price = 0.0
        self.lowest_price = 0.0
        self.is_stock = True
        self.get_price_plot()
        self.get_price_info_of_stock()

    def request_factory(self, api_url, params=''):
        if params == '':
            params = {
                'symbolId': self.stock_id,
                'apiToken': config['FUGLE']['TOKEN']
            }
        res = requests.get(api_url, params=params)
        self.logger(res)
        return res.text

    def get_endpoint_of_url(self, url):
        match = re.search(r'/(\w+)\?', url)
        return match.group(1)

    def logger(self, res_obj):
        res = res_obj
        today_date = datetime.datetime.today().strftime('%Y-%m-%d')
        endpoint_name = self.get_endpoint_of_url(res.url)
        file_path = os.path.join(ROOT_DIR, 'logs/{date}-fugle-{filename}.log'.format(date=today_date,
                                                                                     filename=endpoint_name))
        with open(file_path, 'a', encoding='utf-8') as f:
            now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write('=====================================\n')
            f.write("[{0}]".format(now_timestamp) + '\n')
            f.write("requests url: {0}".format(res.url) + '\n')
            f.write('response: \n' + res.text + '\n')
            f.write('=====================================' + '\n')

    def get_price_plot(self):
        api_for_stock = self.api_url + '/chart'
        res = self.request_factory(api_for_stock)
        self.data = json.loads(res)
        price_set = self.data.get('data').get('chart')
        if price_set == {}:
            arranged_dict = {
                "time": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": []
            }
            return arranged_dict

        self.market_time = self.isoformat_transfer(self.data.get('data').get('info').get('lastUpdatedAt'))

        time_series = list(price_set.keys())
        new_price_dict = {}

        for idx, e in enumerate(time_series):
            ticker_stack = datetime.timedelta(minutes=1)
            tmp_price_dict = {}
            content_stack = price_set.get(e)
            if 'volume' not in content_stack.keys():
                content_stack['volume'] = 0
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

    def get_best_five_quote(self, data=''):
        if data == '':
            api_for_stock = self.api_url + '/quote'
            res = self.request_factory(api_for_stock)
            data = json.loads(res)

        arranged_dict = self.get_price_plot()

        if len(arranged_dict['close']) != 0:
            current_price_list = [x for x in arranged_dict['close'] if x is not None]
            current_closed_price = current_price_list[len(current_price_list) - 1]
        else:
            current_closed_price = self.last_closed

        if current_closed_price > self.last_closed:
            stock_mark = '▲'
        elif current_closed_price < self.last_closed:
            stock_mark = '▼'
        else:
            stock_mark = '-'

        current_volume_list = [x for x in arranged_dict['volume'] if x is not None]

        title_diff = round(current_closed_price - self.last_closed, 2)
        title_diff_percent = round(title_diff / self.last_closed * 100, 2)

        title = '{name}({id})     {time}\n'.format(name=self.stock_name,
                                                   id=self.stock_id,
                                                   time=self.market_time)

        sub_title = '{price}   {mark}{diff} ({percent}%)    成交量: {volume}\n'.format(
            volume=str(int(sum(current_volume_list))),
            price=current_closed_price,
            mark=stock_mark,
            diff=title_diff,
            percent=title_diff_percent)
        order_list = data.get('data').get('quote').get('order')

        best_asks = order_list.get('bestAsks')
        best_bids = order_list.get('bestBids')

        ordered_best_bids = sorted(best_bids, key=operator.itemgetter('price'), reverse=True)
        result = title + sub_title + '-' * len(title) + '\n'
        for idx, bid in enumerate(ordered_best_bids):
            buyer = '{vol} @ {price:.2f}'.format(vol=str(bid.get('unit')), price=bid.get('price'))
            seller = '{vol_ask} @ {price_ask:.2f}'.format(vol_ask=str(best_asks[idx].get('unit')),
                                                          price_ask=best_asks[idx].get('price'))
            result += '{buyer:>15}\t|\t{seller:>15}\n'.format(buyer=buyer, seller=seller)
        return result

    def get_price_info_of_stock(self):
        api_for_stock = self.api_url + '/meta'
        res = self.request_factory(api_for_stock)
        data = json.loads(res)
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
        # print(arranged_dict)

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
        empty_arr = [0 for x in range(270 - len(df))]
        df2 = {
            'time': empty_arr,
            'open': empty_arr,
            'high': empty_arr,
            'low': empty_arr,
            'close': empty_arr,
            'volume': empty_arr
        }
        df2 = pd.DataFrame(df2)
        df3 = df.append(df2, ignore_index=True)
        mpf.volume_overlay(ax2, df3['open'], df3['close'], df3['volume'],
                           colorup='r', colordown='springgreen', width=1, alpha=0.8)

        # 畫均線圖
        sma_5 = abstract.SMA(df, 5)
        sma_30 = abstract.SMA(df, 30)

        # 開盤價水平線
        ax.plot([0, 270], [self.last_closed, self.last_closed])

        # 高低點標記
        ymax = df['close'].max()
        xmax = df['close'].idxmax()
        ymin = df['close'].min()
        xmin = df['close'].idxmin()

        ax.annotate(str(ymax), xy=(xmax, ymax), xycoords='data',
                    xytext=(0, 15), textcoords='offset points', color='r',
                    bbox=dict(boxstyle='round,pad=0.2', fc='navy', alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.95',
                                    color='white'),
                    horizontalalignment='right', verticalalignment='bottom', fontsize=15)
        ax.annotate(str(ymin), xy=(xmin, ymin), xycoords='data',
                    xytext=(0, -25), textcoords='offset points', color='springgreen',
                    bbox=dict(boxstyle='round,pad=0.2', fc='navy', alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.95',
                                    color='white'),
                    horizontalalignment='right', verticalalignment='bottom', fontsize=15)

        # 5MA + 30MA
        ax.plot(sma_5, label='5MA')
        ax.plot(sma_30, label='30MA')

        current_price_list = [x for x in arranged_dict['close'] if x is not None]
        current_closed_price = current_price_list[len(current_price_list) - 1]

        if current_closed_price > self.last_closed:
            stock_color = 'r'
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

        stock_info = '{name}({id})'.format(name=self.stock_name, id=self.stock_id)
        if len(stock_info) > 10:
            space_fill = 83
        else:
            space_fill = 90
        title = '{stock_info: <{fill}}{time}\n'.format(fill=space_fill - len(str(self.market_time)) - len(stock_info),
                                                       stock_info=stock_info,
                                                       time=self.market_time)

        price_info = '{price}   {mark}{diff} ({percent}%)'.format(
            price=current_closed_price,
            mark=stock_mark,
            diff=title_diff,
            percent=title_diff_percent)

        sub_title = '{price_info:<90}成交量: {volume}'.format(
            price_info=price_info,
            volume=str(int(sum(current_volume_list))))

        plt.suptitle(sub_title, y=0.93, size='xx-large', color=stock_color)
        title_obj = ax.set_title(title, loc='Left', pad=0.5)
        plt.setp(title_obj, color='ivory')  # set the color of title to red
        ax.legend(fontsize='x-large', loc=2)
        file_name = self.stock_id + '-' + self.file_name
        fig.savefig('images/lower_{file_name}.png'.format(file_name=file_name), dpi=100)
        fig.savefig('images/{file_name}.png'.format(file_name=file_name))
        plt.clf()
