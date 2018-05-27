import sys
import os
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, LocationSendMessage,TextSendMessage, StickerSendMessage, MessageImagemapAction, ImagemapArea, ImagemapSendMessage, BaseSize, URIImagemapAction
)
from PIL import Image, ImageFilter
from io import BytesIO, StringIO
import requests
import json
import urllib.parse
import numpy
import math


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


# pins = [
#         [35.690810, 139.704500, 'A1'],
#         [35.691321, 139.703438, 'A5'],
#         [35.691074, 139.705056, 'B2'],
#         [35.691172, 139.704962, 'B3'],
#         [35.691209, 139.704300, 'B4'],
#         [35.692279, 139.702208, 'B10'],
#         [35.690521, 139.705810, 'C4'],
#         [35.690621, 139.706777, 'C5'],
#         [35.691267, 139.706879, 'C6'],
#         [35.691502, 139.707242, 'C7'],
#         [35.693777, 139.706166, 'E1'],
#         [35.693143, 139.706104, 'E2'],
#         [35.689273, 139.703907, 'E5'],
#         [35.688629, 139.703212, 'E6'],
#         [35.688497, 139.703397, 'E7'],
#         [35.689831, 139.703384, 'E9'],
#         [35.689421, 139.701877, 'E10'],
#         ]

pins = []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.isdigit():
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=pins[int(event.message.text)][0]),
                TextSendMessage(text=pins[int(event.message.text)][1]),
                TextSendMessage(text="ピン")
                
                
            ]
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='位置情報を送ると近くで終電まで空いている駅一覧を教えるよ(※絵文字1) '),
                TextSendMessage(text='line://nv/location'),
            ]
        )

@app.route("/imagemap/<path:url>/<size>")
def imagemap(url, size):
    map_image_url = urllib.parse.unquote(url)
    response = requests.get(map_image_url)
    img = Image.open(BytesIO(response.content))
    img_resize = img.resize((int(size), int(size)))
    byte_io = BytesIO()
    img_resize.save(byte_io, 'PNG')
    byte_io.seek(0)
    return send_file(byte_io, mimetype='image/png')


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):

    lat = event.message.latitude
    lon = event.message.longitude

    zoomlevel = 18
    imagesize = 1040


    key = 'AIzaSyD_0kx_crEIA5mMLJWnfZN9Fo86Odp4LGY'

    place_map_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?&rankby=distance&location={},{}&types=convenience_store&key={}'.format(lat, lon, key)
    placeJson = requests.get(place_map_url)
    placeData = json.loads(placeJson.text)

    
    for name in placeData["results"]:
        pins.append([name["geometry"]["location"]["lat"],name["geometry"]["location"]["lng"]])



    map_image_url = 'https://maps.googleapis.com/maps/api/staticmap?center={},{}&zoom={}&size=520x520&scale=2&maptype=roadmap&key={}'.format(lat, lon, zoomlevel, key)
    map_image_url += '&markers=color:{}|label:{}|{},{}'.format('red', '', lat, lon)

    center_lat_pixel, center_lon_pixel = latlon_to_pixel(lat, lon)

    marker_color = 'blue'
    pin_width = 60 * 1.5
    pin_height = 84 * 1.5

    actions = []
    for i, pin in enumerate(pins):

        target_lat_pixel, target_lon_pixel = latlon_to_pixel(pin[0], pin[1])

        # (4)
        delta_lat_pixel  = (target_lat_pixel - center_lat_pixel) >> (21 - zoomlevel - 1)
        delta_lon_pixel  = (target_lon_pixel - center_lon_pixel) >> (21 - zoomlevel - 1)

        marker_lat_pixel = imagesize / 2 + delta_lat_pixel
        marker_lon_pixel = imagesize / 2 + delta_lon_pixel

        x = marker_lat_pixel
        y = marker_lon_pixel

        label = '{}'.format(i)

        if(pin_width / 2 < x < imagesize - pin_width / 2 and pin_height < y < imagesize - pin_width):

            map_image_url += '&markers=color:{}|label:{}|{},{}'.format(marker_color, label, pin[0], pin[1])

            actions.append(MessageImagemapAction(
                text='{}'.format(str(i)),
                area = ImagemapArea(
                    x = x - pin_width / 2,
                    y = y - pin_height / 2,
                    width = pin_width,
                    height = pin_height
                )
            ))
            if len(actions) > 10:
                break

    message = ImagemapSendMessage(
            base_url = 'https://{}/imagemap/{}'.format(request.host, urllib.parse.quote_plus(map_image_url)),
            alt_text = '地図',
            base_size = BaseSize(height=imagesize, width=imagesize),
            actions = actions
        )

    line_bot_api.reply_message(
        event.reply_token,
        [
            message,
            TextSendMessage(text='ピンをタップすると詳細が送られるよ！')
        ]
    )

offset = 268435456
radius = offset / numpy.pi

def latlon_to_pixel(lat, lon):
    lat_pixel = round(offset + radius * lon * numpy.pi / 180)
    lon_pixel = round(offset - radius * math.log((1 + math.sin(lat * numpy.pi / 180)) / (1 - math.sin(lat * numpy.pi / 180))) / 2)
    return lat_pixel, lon_pixel

if __name__ == "__main__":
    app.run()

