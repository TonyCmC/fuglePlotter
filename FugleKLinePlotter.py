import configparser
import datetime
import json
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
        self.get_price_plot()
        self.get_price_info_of_stock()

    def get_price_plot(self):
        api_for_stock = self.api_url + '/chart?symbolId={stock}&apiToken={token}'.format(stock=self.stock_id,
                                                                                         token=config['FUGLE']['TOKEN'])
        res = requests.get(api_for_stock)
        self.data = json.loads(res.text)
        price_set = self.data.get('data').get('chart')

        self.market_time = self.isoformat_transfer(self.data.get('data').get('info').get('lastUpdatedAt'))

        time_arr = []
        open_arr = []
        high_arr = []
        low_arr = []
        close_arr = []
        volume_arr = []
        for time_spot in price_set.keys():
            time_arr.append(self.isoformat_transfer(time_spot))
            open_arr.append(price_set.get(time_spot).get('open'))
            high_arr.append(price_set.get(time_spot).get('high'))
            low_arr.append(price_set.get(time_spot).get('low'))
            close_arr.append(price_set.get(time_spot).get('close'))
            volume_arr.append(price_set.get(time_spot).get('unit'))

        arranged_dict = {
            "time": time_arr,
            "open": open_arr,
            "high": high_arr,
            "low": low_arr,
            "close": close_arr,
            "volume": volume_arr,
        }
        return arranged_dict

    def get_price_info_of_stock(self):
        api_for_stock = self.api_url + '/meta?symbolId={stock}&apiToken={token}'.format(stock=self.stock_id,
                                                                                         token=config['FUGLE']['TOKEN'])
        res = requests.get(api_for_stock)
        data = json.loads(res.text)
        self.stock_name = data.get('data').get('meta').get('nameZhTw')
        self.last_closed = float(round(data.get('data').get('meta').get('priceReference'), 2))
        self.highest_price = float(round(data.get('data').get('meta').get('priceHighLimit'), 2))
        self.lowest_price = float(round(data.get('data').get('meta').get('priceLowLimit'), 2))

    def isoformat_transfer(self, datetime_string):
        # datetime.datetime.strptime("2020-09-01T01:01:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
        raw_datetime = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        raw_datetime += datetime.timedelta(hours=8)
        parsed_datetime_string = raw_datetime.strftime('%Y-%m-%d %H:%M:%S')
        return parsed_datetime_string

    def draw_plot(self):
        arranged_dict = self.get_price_plot()
        df = pd.DataFrame(arranged_dict)

        fig = plt.figure(figsize=(10, 8))

        # 用add_axes創建副圖框
        ax = fig.add_axes([0.1, 0.3, 0.8, 0.6])
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.2])

        ax2.set_xticks(range(0, 270, 54))
        ax2.set_xticklabels(['09', '10', '11', '12', '13'])
        ax.set_ylim(round(self.lowest_price, 2), round(self.highest_price, 2))

        mpf.candlestick2_ohlc(ax, df['open'], df['high'], df['low'], df['close'],
                              width=1, colorup='r', colordown='lime', alpha=0.75)

        mpf.volume_overlay(ax2, df['open'], df['close'], df['volume'],
                           colorup='r', colordown='lime', width=1, alpha=0.8)

        # 畫均線圖
        sma_5 = abstract.SMA(df, 5)
        sma_30 = abstract.SMA(df, 30)
        ax.plot([0, 270], [self.last_closed, self.last_closed])
        ax.plot(sma_5, label='5MA')
        ax.plot(sma_30, label='30MA')
        current_price_list = [x for x in arranged_dict['close'] if x is not None]
        current_closed_price = current_price_list[len(current_price_list) - 1]

        if current_closed_price > self.last_closed:
            stock_color = 'r'
            stock_mark = '▲'
        elif current_closed_price < self.last_closed:
            stock_color = 'lime'
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
        plt.setp(title_obj, color='ivory')  # set the color of title to red
        ax.legend(fontsize='x-large')
        file_name = self.stock_id + '-' + self.f_name
        fig.savefig('images/lower_{file_name}.png'.format(file_name=file_name), dpi=100)
        fig.savefig('images/{file_name}.png'.format(file_name=file_name))
