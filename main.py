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
    splittext = text.splitlines()
    print(splittext)

    if ('/' in splittext[0]):
        write_result(splittext, worksheet)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text))

def write_result(splittext, worksheet):
    #
    today = datetime.date.today()
    day = str(today.year) + '/' + splittext[0]
    list_of_lists = worksheet.col_values(DAY_COLUMN)
    # 対象日のセル検索
    day_row = 0
    for row in range(1, 500):
        if list_of_lists[row] == day:
            break
        # ここまで来たら見つかってない

    for i in range(1, len(splittext)):
        content = splittext[i]
        pattern = '.*?(\d+).*'
        result = re.match(pattern, content)
        print(result)

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
