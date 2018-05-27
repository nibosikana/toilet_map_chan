import os
import sys
from flask import Flask, request, abort, send_file

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage, ImageSendMessage, ImagemapSendMessage, BaseSize, MessageImagemapAction, ImagemapArea
)

from io import BytesIO, StringIO
from PIL import Image
import requests
import urllib.parse

app = Flask(__name__)

# 環境変数からchannel_secret・channel_access_tokenを取得
channel_secret = os.environ['LINE_CHANNEL_SECRET']
channel_access_token = os.environ['LINE_CHANNEL_ACCESS_TOKEN']

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

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



# @app.route("/imagemap/<path:url>/<size>")
# def imagemap(url, size):
    
#     map_image_url = urllib.parse.unquote(url)
#     response = requests.get(map_image_url)
#     img = Image.open(BytesIO(response.content))
#     img_resize = img.resize((int(size), int(size)))
#     byte_io = BytesIO()
#     img_resize.save(byte_io, 'PNG')
#     byte_io.seek(0)
#     return send_file(byte_io, mimetype='image/png')


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.type == "message":
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='位置情報を送ると近くで終電まで空いている駅一覧を教えるよ(0x100079)'),
                TextSendMessage(text='line://nv/location'),
                TextSendMessage(text='{}'.format(event.message.text))
            ]
        )





if __name__ == "__main__":
    app.run()