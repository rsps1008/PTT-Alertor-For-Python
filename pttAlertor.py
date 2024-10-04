import sys

sys.stdout.reconfigure(encoding='utf-8')
import requests, time
from bs4 import BeautifulSoup
import os
import traceback
from datetime import datetime
import json

cookies = {'over18': '1'}
file_url = "https://filedn.com/XXXXXXXXXX/config.json"
file_url_GD = "https://drive.google.com/uc?id=1RVbI3V1wJHWSiX6qlfu9PITA9-XXXXXX"

# os.system("export PYTHONIOENCODING=utf8")

token = ''
sended = dict()
keyword_dict = dict()

chtype = {"key": "關鍵字", "push": "推文數", "author": "作者", }

CLOSE_CHECK_FLAG = True
FIRSTBOOT_CHECK_FLAG = True


def lineNotifyMessage(msg):
    global token
    try:
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {'message': msg}
        r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload, timeout=10)
        return r.status_code
    except Exception as e:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " lineNotifyMessage Function Error: ", e)


def make_line_msg(board, keytype, pushNum, poTitle, poUrl, msg):
    global sended
    # print(board,keytype,pushNum,poTitle,poUrl,msg)
    if pushNum == "100":
        pushNum = "爆"
    if poUrl not in sended:
        push_msg = str(msg) + "@" + board + "\n" + "看板：" + board + " ; " + chtype[keytype] + "：" + str(msg) + "\n\n"
        push_msg += str(pushNum) + " " + poTitle + "\n" + poUrl
        lineNotifyMessage(push_msg)
        try:
            print(push_msg)
        except:
            print(
                "Environment encoding error, please add \"PYTHONIOENCODING=utf-8 python3 pttAlertor.py\" when executing")
        print("-----------------------------")
        sended.add(poUrl)
        while len(sended) > 100:
            sended.pop(0)


def load_config_from_pcloud():
    global keyword_dict
    try:
        response = requests.get(file_url, timeout=5)
        if response.status_code == 200:
            keyword_dict_new = json.loads(response.content.decode('utf-8'))
            if keyword_dict_new != keyword_dict:
                keyword_dict = keyword_dict_new
                print("keyword_dict更新:\n", keyword_dict, "\n")
                if not FIRSTBOOT_CHECK_FLAG:
                    lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "keyword dict 更新成功")
        else:
            print("沒有辦法下載dict檔案")
            lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載dict檔案 ")
        response.close()
    except Exception as e:
        print("pcloud伺服器沒有回應", e)
        time.sleep(20)


def load_config_from_GDrive():
    global keyword_dict
    try:
        response = requests.get(file_url_GD, timeout=5)
        if response.status_code == 200:
            keyword_dict_new = json.loads(response.content.decode('utf-8'))
            if keyword_dict_new != keyword_dict:
                keyword_dict = keyword_dict_new
                print("keyword_dict更新:\n", keyword_dict, "\n")
                if not FIRSTBOOT_CHECK_FLAG:
                    lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "keyword dict 更新成功")
        else:
            print("沒有辦法下載dict檔案")
            lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載dict檔案 ")
        response.close()
    except Exception as e:
        print("GD伺服器沒有回應", e)
        time.sleep(20)


# 處理頁面內容
def process_posts(soup, board):
    global keyword_dict
    # 解析文章列表
    separator = soup.find('div', class_='r-list-sep')
    posts = []
    if separator:
        for sibling in separator.previous_siblings:
            if sibling.name == 'div' and 'r-ent' in sibling.get('class', []):
                posts.append(sibling)
    else:
        posts.extend(soup.find_all('div', class_='r-ent'))
    # posts = posts[::-1] // 越下面越新

    for post in posts:
        # 處理每篇文章
        poAuthor = post.select("div.meta div.author")[0].text
        if poAuthor != "-":  # 已刪文
            # 取得推文數
            push_tag = post.select_one("div.nrec span")
            pushNum = push_tag.text if push_tag else "0"
            pushNum = "100" if pushNum == "爆" else pushNum
            # 取得標題和連結
            title_tag = post.select_one("div.title a")
            if title_tag:
                poTitle = title_tag.text
                poUrl = "https://www.ptt.cc" + title_tag["href"]
                if "公告" not in poTitle and "活動" not in poTitle:
                    # 根據關鍵字、推文數、作者進行過濾
                    if "key" in keyword_dict[board]:
                        for key2 in keyword_dict[board]["key"]:
                            if all(word.lower() in poTitle.lower() for word in key2):
                                msg = '&'.join(str(e) for e in key2)
                                make_line_msg(board, "key", pushNum, poTitle, poUrl, msg)
                    if "push" in keyword_dict[board]:
                        if "X" not in pushNum and int(pushNum) >= keyword_dict[board]["push"]:
                            msg = pushNum
                            make_line_msg(board, "push", pushNum, poTitle, poUrl, msg)
                    if "author" in keyword_dict[board]:
                        if poAuthor in keyword_dict[board]["author"]:
                            msg = poAuthor
                            make_line_msg(board, "author", pushNum, poTitle, poUrl, msg)


if __name__ == '__main__':
    ERROR_COUNT = 0
    ERROR_NOTIFY_FLAG = False
    failed_attempts = 0
    fileIOName = None
    for _ in range(5):
        try:
            load_config_from_GDrive()
            print("token Get:", keyword_dict["line_token"]["token"])
            token = keyword_dict["line_token"]["token"]
            token_prefix = keyword_dict["line_token"]["token"][:5]
            if os.path.exists("/tmp") and os.path.isdir("/tmp"):
                fileIOName = "/tmp" + f'/file_io_{token_prefix}.txt'
                print("[Linux系統] File_IO 位置: ", fileIOName)
            else:
                fileIOName = os.path.dirname(os.path.abspath(__file__)) + f'\\file_io_{token_prefix}.txt'
                print("[Windows系統] File_IO 位置: ", fileIOName)
            break
        except:
            print("Warring: Cannot get token from Json")
            traceback.print_exc()
            failed_attempts += 1
            time.sleep(2)
    if failed_attempts == 5:
        print("Error: Failed to get token after 5 attempts. Exiting program.")
        sys.exit()

    try:
        with open(fileIOName, 'a+') as f:
            f.seek(0)
            sended = set(f.read().split("\n"))
            print("File_IO 已存在，讀取已通知列表")
    except FileNotFoundError:
        print("File_IO 不存在")

    lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT START")

    while True:
        try:
            load_config_from_GDrive()
            for board in keyword_dict:  # keyword_dict[board]
                if board == "line_token":
                    if token != keyword_dict[board]["token"]:
                        token = keyword_dict[board]["token"]
                        print("token update!!!:", keyword_dict[board]["token"])
                else:
                    url = "https://www.ptt.cc/bbs/" + board + "/index.html"
                    r = requests.get(url, cookies=cookies, timeout=20)
                    soup = BeautifulSoup(r.text, "html.parser")

                    # 檢查看板是否存在
                    if FIRSTBOOT_CHECK_FLAG:
                        try:
                            check_board_exist = soup.select("div.main-container")[0].select("div.bbs-screen")[0].text
                            if "404 - Not Found" in check_board_exist:
                                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有此版: " + board)
                        except:
                            pass

                    # 獲取「上頁」的連結，並處理「上頁」的內容
                    previous_page_link = soup.find('div', id='action-bar-container').find('a', string='‹ 上頁')
                    if previous_page_link:
                        previous_page_url = "https://www.ptt.cc" + previous_page_link['href']
                        r = requests.get(previous_page_url, cookies=cookies, timeout=20)
                        soup_pre = BeautifulSoup(r.text, "html.parser")
                        process_posts(soup_pre, board)

                    # 處理當前頁面
                    process_posts(soup, board)

            # break
            FIRSTBOOT_CHECK_FLAG = False
            ERROR_NOTIFY_FLAG = False
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Dump")
            ERROR_COUNT = 0
            time.sleep(90)
        except requests.exceptions.RequestException as e:
            if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT伺服器沒有回應: " + str(e))
                ERROR_NOTIFY_FLAG = True
            print("PTT伺服器沒有回應： ", e)
            traceback.print_exc()
            ERROR_COUNT += 1
            time.sleep(90)
        except Exception as e:
            if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Error: " + str(e))
                ERROR_NOTIFY_FLAG = True
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Error:", e)
            traceback.print_exc()
            ERROR_COUNT += 1
            time.sleep(90)
        except KeyboardInterrupt:
            with open(fileIOName, 'w+') as f:
                for item in sended:
                    f.write(f"{item}\n")
            lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
            CLOSE_CHECK_FLAG = False
            break

    if CLOSE_CHECK_FLAG:
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
