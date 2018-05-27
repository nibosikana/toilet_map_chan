import os
import sys
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, TextSendMessage, ImageSendMessage, ImagemapSendMessage, BaseSize, MessageImagemapAction, ImagemapArea
)

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

@app.route("/imagemap")
def imagemap():
#@app.route("/imagemap/<path:url>/<size>")

# def imagemap(url, size):


    # map_image_url = urllib.parse.unquote(url)
    # response = requests.get(map_image_url)
    # img = Image.open(BytesIO(response.content))
    # img_resize = img.resize((int(size), int(size)))
    # byte_io = BytesIO()
    # img_resize.save(byte_io, 'PNG')
    # byte_io.seek(0)
    # return send_file(byte_io, mimetype='image/png')
    return "imagemap!!!!!!れ"


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


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):

    lat = event.message.latitude
    lon = event.message.longitude

    zoomlevel = 16
    imagesize = 1040

    # actions = [
    #     MessageImagemapAction(
    #         text = "位置情報教えて！",
    #         area = ImagemapArea(
    #             x = 0,
    #             y = 0,
    #             width = 1040,
    #             height = 1040
    #     )
    # )]


    key = 'AIzaSyD_0kx_crEIA5mMLJWnfZN9Fo86Odp4LGY'


    map_image_url = 'https://maps.googleapis.com/maps/api/staticmap?center={},{}&zoom={}&size=520x520&scale=2&maptype=roadmap&key={}'.format(lat, lon, zoomlevel, key)
    line_bot_api.reply_message(
        event.reply_token,
        [
            # ImagemapSendMessage(
            #     base_url = 'https://toilet-map-chan.herokuapp.com/imagemap/{}'.format(urllib.parse.quote_plus(map_image_url)),
            #     alt_text = '地図',
            #     base_size = BaseSize(height=imagesize, width=imagesize),
            #     actions = actions
            # )
            TextSendMessage(text='終電まで空いている出口一覧です(※絵文字2)')
        ]
    )


if __name__ == "__main__":
    app.run()