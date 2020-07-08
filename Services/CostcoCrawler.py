import configparser

import requests
from bs4 import BeautifulSoup
from datetime import datetime


config = configparser.ConfigParser()
config.read('config.ini')


class CostcoCrawler:
    def send_tg_msg(self, text):
        tg_token = config['TG_REMINDER']['ACCESS_TOKEN']
        chat_id = config['TG_REMINDER']['CHAT_ID']
        url = 'https://api.telegram.org/bot{token}/sendMessage'.format(token=tg_token)
        res = requests.post(url, data={'text': text, 'chat_id': chat_id})
        print(res.text)
        if res.status_code == 200:
            return True
        else:
            return False

    def crawler(self):
        url = "https://www.costco.com.tw/Health-Beauty/Personal-Body/Oral-Care/Braun-Oral-B-Electric-Toothbrush-Set-SMART3500/p/117740"
        res = requests.get(url)
        now_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open('tmp.log', 'a', encoding='utf-8') as f:
            f.write('--------------- Start -----------------------]\n')
            f.write('[{time} -----------------------]\n'.format(time=now_time_str))
            f.write(res.text[:1000])
            f.write('--------------- End -----------------------]\n')

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "lxml")
            button_text = soup.find(id='addToCartForm').button.text.strip()
            if button_text == '缺貨':
                self.send_tg_msg('缺貨')
            else:
                self.send_tg_msg('狀態已更新 \n'+ url)

