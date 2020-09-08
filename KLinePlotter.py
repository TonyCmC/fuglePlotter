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


class KLinePlotter:
    # define the font attributes of title
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 20
    plt.style.use('dark_background')

    api_url = 'https://ws.api.cnyes.com/charting/api/v1/history?'

    def __init__(self, stock_id, f_name):
        self.stock_id = stock_id
        self.f_name = f_name
        self.data = {}
        self.market_time = datetime.datetime.now()
        self.last_closed = 0.0
        self.get_current_price()
        self.get_previous_closed_price()

    def get_current_price(self):
        api_for_stock = self.api_url + 'resolution=1&symbol=TWS:{stock}:STOCK'.format(stock=self.stock_id)
        res = requests.get(api_for_stock)
        self.data = json.loads(res.text)
        self.market_time = datetime.datetime.fromtimestamp(self.data.get('data').get('t')[0]).strftime('%H:%M')

    def timestamp_transfer(self):
        tmp = []
        for e in self.data.get('data').get('t'):
            tmp.append(datetime.datetime.fromtimestamp(e))
        tmp.reverse()
        data_belong_date = tmp[0]
        total_open_mins = datetime.timedelta(minutes=270)
        closed_time = data_belong_date + total_open_mins

        one_min_delta = datetime.timedelta(minutes=1)

        while tmp[len(tmp) - 1] < closed_time:
            tmp.append(tmp[len(tmp) - 1] + one_min_delta)
        return tmp

    def list_arranger(self, raw_list, length):
        tmp = raw_list
        tmp.reverse()
        while len(tmp) < length:
            tmp.append(None)
        return tmp

    def get_previous_closed_price(self):
        api_for_history = self.api_url + 'resolution=D&symbol=TWS:{stock}:STOCK&quote=1'.format(stock=self.stock_id)
        print('url: ', api_for_history)
        res = requests.get(api_for_history.format(stock=self.stock_id))
        json_data = json.loads(res.text)
        print(json_data)
        self.last_closed = json_data.get('data').get('quote').get('21')
        print('last_closed', self.last_closed)

    def draw_plot(self):
        # 處理股票代號 => 股票(ETF)名
        with open('stock.json', 'r', encoding='utf-8') as st:
            stock_dict = json.loads(st.read())

        arranged_dict = {
            "time": self.timestamp_transfer(),
            "open": self.data.get('data').get('o'),
            "high": self.data.get('data').get('h'),
            "low": self.data.get('data').get('l'),
            "close": self.data.get('data').get('c'),
            "volume": self.data.get('data').get('v'),
        }
        data_length = len(arranged_dict.get('time'))
        arranged_dict['open'] = self.list_arranger(arranged_dict['open'], data_length)
        arranged_dict['high'] = self.list_arranger(arranged_dict['high'], data_length)
        arranged_dict['low'] = self.list_arranger(arranged_dict['low'], data_length)
        arranged_dict['close'] = self.list_arranger(arranged_dict['close'], data_length)
        arranged_dict['volume'] = self.list_arranger(arranged_dict['volume'], data_length)
        df = pd.DataFrame(arranged_dict)
        stock_name = stock_dict.get(self.stock_id)
        chart_title = '{name}({id})'.format(name=stock_name, id=self.stock_id)

        fig = plt.figure(figsize=(10, 8))
        # 用add_axes創建副圖框
        ax = fig.add_axes([0.1, 0.3, 0.8, 0.6])
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.2])

        ax2.set_xticks(range(0, 270, 54))
        ax2.set_xticklabels(['09', '10', '11', '12', '13'])
        ax.set_ylim(round(self.last_closed * 0.9, 2), round(self.last_closed * 1.1, 2))

        mpf.candlestick2_ohlc(ax, df['open'], df['high'], df['low'], df['close'],
                              width=0.6, colorup='r', colordown='lime', alpha=0.75)

        mpf.volume_overlay(ax2, df['open'], df['close'], df['volume'],
                           colorup='r', colordown='lime', width=0.5, alpha=0.8)

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

        title = '{name}({id})                               {time}     \n'.format(name=stock_name,
                                                                            id=self.stock_id,
                                                                            time=self.market_time)
        sub_title = '{price}   {mark}{diff} ({percent}%)                             成交量: {volume}'.format(
                                                                            volume=str(int(sum(current_volume_list))),
                                                                            price=current_closed_price,
                                                                            mark=stock_mark,
                                                                            diff=title_diff,
                                                                            percent=title_diff_percent)
        plt.suptitle(sub_title,x=0.385, y=0.93, size='xx-large', color=stock_color)
        title_obj = ax.set_title(title, loc='Left', pad=0.5)
        # plt.getp(title_obj)  # print out the properties of title
        # plt.getp(title_obj, 'text')  # print out the 'text' property for title
        plt.setp(title_obj, color='ivory')  # set the color of title to red
        ax.legend(fontsize='x-large')
        file_name = self.stock_id + '-' + self.f_name
        fig.savefig('images/lower_{file_name}.png'.format(file_name=file_name), dpi=100)
        fig.savefig('images/{file_name}.png'.format(file_name=file_name))
