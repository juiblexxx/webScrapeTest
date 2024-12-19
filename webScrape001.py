import os
import time
import urllib
import csv
# import cv2
import requests
import configparser
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# にいがたLiveカメラサイト https://www.live-cam.pref.niigata.jp/text/select.php?area=3&class=1
# などから写真を読み込み、一覧表示します
# 対象の写真はconfig.iniに「リンク文字列,画像ファイル名」の形式で指定します
# [NIIGATA_LIVE_CAMERA]
# url = https://www.live-cam.pref.niigata.jp/text/select.php?area=3&class=1
# xpath = /html/body/div/div[3]/div/div[3]/img
# # 保存ファイル名,リンクテキスト
# data1 = 00_makiIC,国道116号 巻中央IC
# data2 = 10_zenkouji,国道116号 善光寺
# data3 = 20_kamegaiIC,国道116号 亀貝ＩＣ
# data4 = 30_kurosakiIC,国道8号 黒埼IC
# data5 = 40_sakuragiIC,国道8号 桜木IC
# data6 = 50_sichikuIC,国道7号 紫竹山IC
# # 設定データの数
# data = 6

# 指定したURLとXPATHから画像をダウンロードしてくれる関数
def download_image(driver, wait, base_url: str, link_text: str, image_xpath: str):
    # リンク文字列のクリック
    driver.find_element(By.LINK_TEXT, link_text).click()

    # elements情報が揃うまで待つ
    wait.until(EC.presence_of_all_elements_located)

    # さらに1秒待つ
    time.sleep(1)

    # 開発者モードでコピーしたxpathからelementを取得
    element = driver.find_element(by=By.XPATH, value=image_xpath)

    # elementsのsrc=画像URLを取得
    image_url = element.get_attribute("src")
    print(image_url)

    # urllibライブラリを使って画像URLからバイナリ読み込む
    with urllib.request.urlopen(image_url)as rf:
        image_data = rf.read()

    return image_data


# ダウンロードした画像データ（バイナリ）を別名保存してくれる関数
def save_image(image_data, output_path: str, image_name: str):
    # with open()構文を使ってバイナリデータをpng形式で書き出す
    with open(os.path.join(output_path, image_name), mode="wb")as wf:
        wf.write(image_data)



# 指定したメッセージと画像を貼ってくれるLine通知用の関数
def send_image_to_line_notify(url: str, token: str, notify_message: str, image_path: str):
    headers = {"Authorization" : "Bearer "+ token}

    with open(image_path, 'rb') as file:
        image = file.read()

    payload = {"message" :  notify_message}
    files = {"imageFile": image}



# 全般設定

# 保存する画像に付与するタイムスタンプ
current_time = datetime.now().strftime('%Y-%m-%d_%H%M%S')

#コンフィグの読み込み
# iniフォルダ
output_path = ""
# iniファイル
config_path = "config.ini"

# configparserの宣言とiniファイルの読み込み
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(output_path,'config.ini'), encoding='utf-8')

# LINE関係の情報をiniから取得
line_url = config_ini['LINE']['url']
line_token = config_ini['LINE']['token']

# Chrome起動、バックグラウンド＋シークレットモードで処理
option = webdriver.ChromeOptions()
option.add_argument("--headless --incognito")
driver = webdriver.Chrome(options = option)

# Explicit waitを30秒で追加
# elementsなどの要素が全て出そろうまで待ってくれる
wait = WebDriverWait(driver=driver, timeout=30)



# にいがたライブカメラからのデータ取得

# 取得URL
base_url = config_ini['NIIGATA_LIVE_CAMERA']['url']

# 画像のXPATH
image_xpath = config_ini['NIIGATA_LIVE_CAMERA']['xpath']

# データの数はintで読みたい
number_of_data = config_ini.getint('NIIGATA_LIVE_CAMERA','data')

for data_number in range(number_of_data):
    # 設定値を取得
    reader = config_ini['NIIGATA_LIVE_CAMERA'][f"data{data_number + 1}"]

    # 設定値を分解
    image_name, link_text = reader.split(',')

    # 指定したURLに遷移する（にいがたライブカメラはメニュー→カメラ画面 と遷移する必要があるので、都度戻る）
    driver.get(base_url)

    # elements情報が揃うまで待つ
    wait.until(EC.presence_of_all_elements_located)

    # 画像をダウンロード
    image_data = download_image(driver, wait, base_url, link_text, image_xpath)

    time_image_name = f"{current_time}_{image_name}.png"
    save_image(image_data, output_path, time_image_name)

    # LINEに送信
    send_image_to_line_notify(line_url, line_token, f"{link_text}:{current_time}", os.path.join(output_path, time_image_name))



# NCTライブカメラからのデータ取得

# 取得URL
base_url = config_ini['NCT_LIVE_CAMERA']['url']

# 画像のXPATH
image_xpath = config_ini['NCT_LIVE_CAMERA']['xpath']

# データの数はintで読みたい
number_of_data = config_ini.getint('NCT_LIVE_CAMERA','data')

# 指定したURLに遷移する
# NCTのサイトは1つのxpathをjavascrpitで変更しまくる仕様なのでURLは毎回開かなくてOK
# 逆に毎回開くとうまく画像が取得できなくなる
driver.get(base_url)

# elements情報が揃うまで待つ
wait.until(EC.presence_of_all_elements_located)

for data_number in range(number_of_data):
    # 設定値を取得
    reader = config_ini['NCT_LIVE_CAMERA'][f"data{data_number + 1}"]

    # 設定値を分解
    image_name, link_text = reader.split(',')

    # 2024/04/19 何か不具合でたので一旦お休み

    # 画像をダウンロード
    # image_data = download_image(driver, wait, base_url, link_text, image_xpath)

    # time_image_name = f"{current_time}_{image_name}.png"
    # save_image(image_data, output_path, time_image_name)


# GoogleMapからのデータ取得

# 画面サイズ変更
w = config_ini['GOOGLE_MAP']['window_size_w']
h = config_ini['GOOGLE_MAP']['window_size_h']
driver.set_window_size(w, h)

# 画面のズーム倍率
googlemap_zoom = config_ini['GOOGLE_MAP']['window_zoom']

# 取得URL
googlemap_url = config_ini['GOOGLE_MAP']['url']

# 取得形式
googlemap_option = config_ini['GOOGLE_MAP']['option']

# データの数はintで読みたい
number_of_data = config_ini.getint('GOOGLE_MAP','data')

for data_number in range(number_of_data):
    # 設定値を取得
    reader = config_ini['GOOGLE_MAP'][f"data{data_number + 1}"]

    # 設定値を分解
    image_name, town_name, map_coordinates1, map_coordinates2 = reader.split(',')

    # 設定値に基づきGoogleMapを開く（座標入力が必要なので必ず毎回呼び出す）
    driver.get(f"{googlemap_url}/{map_coordinates1},{map_coordinates2},{googlemap_zoom}/{googlemap_option}")

    # elements情報が揃うまで待つ
    wait.until(EC.presence_of_all_elements_located)

    # さらに1秒待つ
    time.sleep(1)

    # スクショ撮影
    driver.save_screenshot(os.path.join(output_path, f"{current_time}_{image_name}.png"))


# chrome閉じる
driver.quit()
