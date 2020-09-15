import configparser
import datetime
import json
import logging
import os
import re

import requests
import telegram
from flask import Flask, request, abort, jsonify, redirect
from telegram.ext import Dispatcher, MessageHandler, Filters

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageSendMessage)

# Load data from config.ini file
from FugleKLinePlotter import FugleKLinePlotter

config = configparser.ConfigParser()
config.read('config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial Flask app
app = Flask(__name__, static_url_path="/images", static_folder="./images/")

server_url = config['SERVER']['SERVER_URL']

# Initial bot by Telegram access token
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))

line_bot_api = LineBotApi(config['LINE']['LINE_BOT_API'])
handler = WebhookHandler(config['LINE']['LINE_BOT_SECRET'])

STATUS_ID_NOT_FOUND = '1'
STATUS_PASS = '2'

def init_telegram_webhook():
    if '127.0.0.1' not in config['SERVER']['SERVER_URL']:
        url = "https://api.telegram.org/bot{tgbot_token}/setWebhook?url={hook_url}/hook".format(tgbot_token=config['TELEGRAM']['ACCESS_TOKEN'], hook_url=server_url)
        res = requests.get(url)
        print(res.text)


@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'


def get_stock_id(input_text):
    """

    @param input_text: expect something like p2002, P2002, p中鋼, P中鋼
    @return: STATUS_ID_NOT_FOUND = '1' || STATUS_PASS = '2'
    """
    stock_dict: dict
    num_list = [a for a in range(0, 10)]
    str_num_list = [str(a) for a in range(0, 10)]
    stock_dict = json.load(open('stock.json', encoding='utf-8'))
    stock_dict_flip = dict((v, k) for k, v in stock_dict.items())

    res_d = re.search(r'^[p|P](\S+.)', input_text)
    if res_d is None:
        return STATUS_PASS
    try:
        result = res_d.group(1)
        if result[0] in num_list or result[0] in str_num_list:
            if result in stock_dict.keys():
                return result
        else:
            if result in stock_dict_flip.keys():
                return stock_dict_flip.get(result)
    except Exception as ez:
        print(ez.args)

    return STATUS_ID_NOT_FOUND


def reply_handler(bot, update):
    """Reply message."""
    text = update.message.text
    try:
        if 10 > len(text) > 0:
            f_name = ('%032x' % int(datetime.datetime.now().timestamp()))[-10:]
            stock_id = get_stock_id(text)
            if stock_id == STATUS_ID_NOT_FOUND:
                raise ValueError('查無股票代號 / 名稱, Invalid Stock Name / Id.')
            if stock_id != STATUS_PASS:
                klp = FugleKLinePlotter(stock_id, f_name)
                file_name = stock_id + '-' + f_name
                klp.draw_plot()
                img_url = server_url + '/images/{file_name}.png'.format(file_name=file_name)
                lower_img_url = server_url + '/images/lower_{file_name}.png'.format(file_name=file_name)
                update.message.reply_photo(photo=open('images/{file_name}.png'.format(file_name=file_name), 'rb'))
    except ValueError as e:
        update.message.reply_text(e.args)
    except Exception as ex:
        print(ex.args)



# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    try:
        if 10 > len(text) > 0:
            f_name = ('%032x' % int(datetime.datetime.now().timestamp()))[-10:]
            stock_id = get_stock_id(text)
            if stock_id == STATUS_ID_NOT_FOUND:
                raise ValueError('查無股票代號 / 名稱, Invalid Stock Name / Id.')
            if stock_id != STATUS_PASS:
                klp = FugleKLinePlotter(stock_id, f_name)
                file_name = stock_id + '-' + f_name
                klp.draw_plot()
                img_url = server_url + '/images/{file_name}.png'.format(file_name=file_name)
                lower_img_url = server_url + '/images/lower_{file_name}.png'.format(file_name=file_name)
                line_bot_api.reply_message(event.reply_token,
                                           ImageSendMessage(original_content_url=img_url, preview_image_url=lower_img_url))
    except ValueError as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e.args)))

@app.route("/getStockGraph", methods=['GET'])
def get_stock_graph():
    stock_id = request.args.get('stock_id')
    res = re.search(r'^(\S+.)', stock_id)

    if len(stock_id) > 0 and res is not None:
        f_name = ('%032x' % int(datetime.datetime.now().timestamp()))[-10:]
        stock_id = res.group(1)
        klp = FugleKLinePlotter(stock_id, f_name)
        file_name = stock_id + '-' + f_name
        klp.draw_plot()
        img_url = server_url + '/images/{file_name}.png'.format(file_name=file_name)
        lower_img_url = server_url + '/images/lower_{file_name}.png'.format(file_name=file_name)
        return redirect(img_url)
    else:
        return jsonify({'result': '1', 'message': 'stock_id Not Found'})


init_telegram_webhook()

if __name__ == "__main__":
    # Running server
    app.run(host=config['HOST']['HOST'], port=config['HOST']['PORT'], debug=True)
