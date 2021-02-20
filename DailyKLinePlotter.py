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


class DailyKLinePlotter:
    # define the font attributes of title
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.titlesize'] = 20
    plt.style.use('dark_background')

    api_url = 'https://ws.api.cnyes.com/ws/api/v1/charting/history'

    def __init__(self, stock_id, f_name):
        self.stock_id = stock_id
        self.f_name = f_name
        self.data = {}
        self.arranged_dict = {}
        self.market_time = datetime.datetime.now()
        self.get_last_180_days_data()

    def request_factory(self, params):
        res = requests.get(self.api_url, params=params)
        self.logger(res)
        return res.text

    def logger(self, res_obj):
        res = res_obj
        today_date = datetime.datetime.today().strftime('%Y-%m-%d')
        with open('logs/{date}-cnyes-{filename}.log'.format(date=today_date,
                                                            filename=self.api_url[
                                                                     self.api_url.index('/', -10) + 1:].lower()),
                  'a',
                  encoding='utf-8') as f:
            now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write('=====================================\n')
            f.write("[{0}]".format(now_timestamp) + '\n')
            f.write("requests url: {0}".format(res.url) + '\n')
            f.write('response: \n' + res.text + '\n')
            f.write('=====================================' + '\n')

    def get_last_180_days_data(self):
        params = {
            'resolution': 'D',
            'symbol': 'TWS:{stock}:STOCK'.format(stock=self.stock_id),
            'quote': '1',
            'from': int(datetime.datetime.now().timestamp()),
            'to': int((datetime.datetime.now() - datetime.timedelta(days=180)).timestamp())
        }

        res = self.request_factory(params)
        result = json.loads(res)
        time_arr = [datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d') for t in result.get('data').get('t')]
        time_arr.reverse()
        open_arr = list(result.get('data').get('o'))
        open_arr.reverse()

        high_arr = list(result.get('data').get('h'))
        high_arr.reverse()
        close_arr = list(result.get('data').get('c'))
        close_arr.reverse()
        low_arr = list(result.get('data').get('l'))
        low_arr.reverse()
        vol_arr = list(result.get('data').get('v'))
        vol_arr.reverse()

        self.arranged_dict = {'time': time_arr,
                              'open': open_arr,
                              'high': high_arr,
                              'low': low_arr,
                              'close': close_arr,
                              'volume': vol_arr,
                              }

    def draw_plot(self):
        # 處理股票代號 => 股票(ETF)名
        with open('stock.json', 'r', encoding='utf-8') as st:
            stock_dict = json.loads(st.read())

        df = pd.DataFrame.from_dict(self.arranged_dict)
        stock_name = stock_dict.get(self.stock_id)
        chart_title = '{name}({id})'.format(name=stock_name, id=self.stock_id)

        fig = plt.figure(figsize=(10, 8))
        # 用add_axes創建副圖框
        ax = fig.add_axes([0.1, 0.3, 0.8, 0.6])
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.2])

        data_length = len(df['close'])
        ax2.set_xticks(range(0, data_length, int(data_length / 4)))
        ax2.set_xticklabels([df['time'][int(data_length / 4) - 1],
                             df['time'][int(data_length / 4 * 2) - 1],
                             df['time'][int(data_length / 4 * 3) - 1],
                             df['time'][data_length - 1]])
        ax.set_ylim(min(df['close']) * 0.9, max(df['close']) * 1.1)

        mpf.candlestick2_ohlc(ax, df['open'], df['high'], df['low'], df['close'],
                              width=0.6, colorup='r', colordown='lime', alpha=0.75)

        mpf.volume_overlay(ax2, df['open'], df['close'], df['volume'],
                           colorup='r', colordown='lime', width=0.5, alpha=0.8)

        # 畫均線圖
        sma_5 = abstract.SMA(df, 5)
        # sma_20 = abstract.SMA(df, 20)
        sma_60 = abstract.SMA(df, 60)
        upperband, middleband, lowerband = abstract.BBANDS(df['close'].astype(float), timeperiod=20, nbdevup=2.0,
                                                           nbdevdn=2.0, matype=0)

        # ax.plot([0, len(df['close'])], [last_closed, last_closed])
        ax.plot(sma_5, label='5MA')
        # ax.plot(sma_20, label='20MA')
        ax.plot(sma_60, label='60MA')
        ax.plot(upperband, label='BBAND', alpha=0.3)
        ax.plot(middleband, alpha=0.8)
        ax.plot(lowerband, alpha=0.3)
        current_closed_price = df['close'][len(df['close']) - 1]
        last_closed = df['close'][len(df['close']) - 2]

        if current_closed_price > last_closed:
            stock_color = 'r'
            stock_mark = '▲'
        elif current_closed_price < last_closed:
            stock_color = 'lime'
            stock_mark = '▼'
        else:
            stock_color = 'ivory'
            stock_mark = '-'

        current_volume_list = df['volume']

        title_diff = round(current_closed_price - last_closed, 2)
        title_diff_percent = round(title_diff / last_closed * 100, 2)

        title = '{name}({id}) 日K線                            {time}     \n'.format(name=stock_name,
                                                                                   id=self.stock_id,
                                                                                   time=df['time'][
                                                                                       len(df['close']) - 1])
        sub_title = '{price}   {mark}{diff} ({percent}%)                             成交量: {volume}'.format(
            volume=str(int(current_volume_list[len(current_volume_list) - 1])),
            price=current_closed_price,
            mark=stock_mark,
            diff=title_diff,
            percent=title_diff_percent)
        plt.suptitle(sub_title, x=0.385, y=0.93, size='xx-large', color=stock_color)
        title_obj = ax.set_title(title, loc='Left', pad=0.5)
        plt.setp(title_obj, color='ivory')  # set the color of title to red
        ax.legend(fontsize='x-large', loc=2)
        file_name = self.stock_id + '-' + self.f_name
        fig.savefig('images/lower_{file_name}.png'.format(file_name=file_name), dpi=100)
        fig.savefig('images/{file_name}.png'.format(file_name=file_name))
