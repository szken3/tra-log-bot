from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import datetime
import re

app = Flask(__name__)

DAY_COLUMN = 2

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# 辞書オブジェクト。認証に必要な情報をHerokuの環境変数から呼び出している
credential = {
                "type": "service_account",
                "project_id": os.environ['SHEET_PROJECT_ID'],
                "private_key_id": os.environ['SHEET_PRIVATE_KEY_ID'],
                "private_key": os.environ['SHEET_PRIVATE_KEY'],
                "client_email": os.environ['SHEET_CLIENT_EMAIL'],
                "client_id": os.environ['SHEET_CLIENT_ID'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url":  os.environ['SHEET_CLIENT_X509_CERT_URL']
             }

credentials = ServiceAccountCredentials.from_json_keyfile_dict(credential, scope)

gc = gspread.authorize(credentials)

@app.route("/")
def hello_world():
    return "hello world!"

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
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ブック開いてユーザ名と同じ名前のシートを開く
    workbook = gc.open_by_key(os.environ['SPREAD_SHEET_KEY'])
    profile = line_bot_api.get_profile(event.source.user_id)
    worksheet = workbook.worksheet(profile.display_name)

    worksheet.update_cell(1, 1, "test")

    text = event.message.text
    split_text = text.splitlines()
    print(split_text)

    # "/"が入ってたら日付扱い
    if ('/' in split_text[0]):
        write_result(split_text, worksheet)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text))

def write_result(split_text, worksheet):

    today = datetime.date.today()
    day = str(today.year) + '/' + split_text[0]
    list_of_lists = worksheet.col_values(DAY_COLUMN)
    # 対象日のセル検索
    day_row = 0
    for row in range(1, 500):
        if list_of_lists[row] == day:
            break
        # ここまで来たら見つかってない

    # 一行ずつ処理
    for i in range(1, len(split_text)):
        # 空白を潰す
        content = re.sub(r"\s", "", split_text[i])
        s_pos = 0
        e_pos = 0
        for i in range(len(content)):
            tmp = content[i]
            if tmp.isnumeric():
                if s_pos == 0:
                    s_pos = i
                else:
                    e_pos = i
        print(s_pos)
        print(e_pos)

        tra_event = ""
        tra_count = 0

        # 単位に分と秒が入っていると話が変わるので一旦考えない

        #
        if not s_pos == 0:
            # 種目(ここは純粋にこれでOK)
            tra_event = content[:s_pos]
            # 回数取得

            # 時間表記だった場合
            if (not content.find('分') == (-1)) or (not content.find('秒') == (-1)):
                tmp = content[s_pos:]
                min_pos = tmp.find('分')
                sec_pos = tmp.find('秒')
                #print(tmp)
                min = 0
                sec = 0
                if not min_pos == (-1):
                    min = int(tmp[:min_pos])
                if not sec_pos == (-1):
                    #sec = int(tmp[min_pos:sec_pos])
                    #print(tmp[min_pos:sec_pos])
                    print('sec')
                    print(tmp[min_pos + 1:sec_pos])
                #t = datetime.time(0, min, sec, 0)
                # print(t)

            if not e_pos == 0:
                # 数字の最初と最後を含むテキスト抜き出し
                tmp = content[s_pos:e_pos + 1]
                # 掛け算表記のみやる
                mul_pos = tmp.find('×')
                if not mul_pos == (-1):
                    f_part = tmp[:mul_pos]
                    e_part = tmp[mul_pos + 1:]
                    tra_event = int(f_part) * int(e_part)
                    print(tra_event)
                else:
                    tra_count = tmp

        if not e_pos == len(content):
            print(content[e_pos:])

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
