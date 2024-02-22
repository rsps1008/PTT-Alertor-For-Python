import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, time
from bs4 import BeautifulSoup
import re, os
import traceback
from datetime import datetime
import json

file_url = "https://filedn.com/XXXXXXXXXX/config.json"
file_url_GD = "https://drive.google.com/uc?id=1RVbI3V1wJHWSiX6qlfu9PITA9-XXXXXX"

# os.system("export PYTHONIOENCODING=utf8")

token = ''
token_prefix = ''
sended = []
chtype = {"key":"關鍵字","push":"推文數","author":"作者",}


doubleCheck_Flag = True
FIRSTBOOT_CHECK_FLAG = True

keyword_dict =  dict()
    
def lineNotifyMessage(msg):
    global token
    try:
        headers = {
            "Authorization": "Bearer " + token, 
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        payload = {'message': msg}
        r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
        return r.status_code
    except Exception as e:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " lineNotifyMessage Function Error: ", e)
    
def make_line_msg(board,keytype,pushNum,poTitle,poUrl,msg):
    #print(board,keytype,pushNum,poTitle,poUrl,msg)
    if pushNum == "100":
        pushNum = "爆"
    if poUrl not in sended:
        push_msg = str(msg) + "@" + board + "\n" + "看板："+ board +" ; "+ chtype[keytype] + "：" + str(msg) + "\n\n"
        push_msg += str(pushNum) + " " + poTitle + "\n" + poUrl
        lineNotifyMessage(push_msg)
        try:
            print(push_msg)
        except:
            print("Environment encoding error, please add \"PYTHONIOENCODING=utf-8 python3 pttAlertor.py\" when executing")
        print("-----------------------------")
        sended.append(poUrl)
        while len(sended)>100:
            sended.pop(0)

def check_notify_config():
    global keyword_dict
    response = requests.get(file_url)
    if response.status_code == 200:
        keyword_dict_new = json.loads(response.content.decode('utf-8'))
        if keyword_dict_new != keyword_dict:
            keyword_dict = keyword_dict_new
            print("keyword_dict更新:\n",keyword_dict,"\n")
            if not FIRSTBOOT_CHECK_FLAG:
                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "keyword dict 更新成功" )
    else:
        print("沒有辦法下載dict檔案")
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載dict檔案 ")
    response.close()
    
def check_notify_config_GD():
    global keyword_dict
    response = requests.get(file_url_GD)
    if response.status_code == 200:
        keyword_dict_new = json.loads(response.content.decode('utf-8'))
        if keyword_dict_new != keyword_dict:
            keyword_dict = keyword_dict_new
            print("keyword_dict更新:\n",keyword_dict,"\n")
            if not FIRSTBOOT_CHECK_FLAG:
                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "keyword dict 更新成功" )
    else:
        print("沒有辦法下載dict檔案")
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載dict檔案 ")
    response.close()
    
if __name__ == '__main__':
    check_notify_config_GD()
    failed_attempts = 0
    for _ in range(5):
        try:
            print("token Get:", keyword_dict["line_token"]["token"])
            token = keyword_dict["line_token"]["token"]
            token_prefix = keyword_dict["line_token"]["token"][:5]
            break
        except:    
            print("Warring: Cannot get token from Json")
            failed_attempts += 1
            time.sleep(2)
    if failed_attempts == 5:
        print("Error: Failed to get token after 5 attempts. Exiting program.")
        sys.exit()
    
    try:
        f = open(os.path.dirname(os.path.abspath(__file__))+'/file_io_'+token_prefix+'.txt', 'r')
        sended = f.read().split("\n")
        print("file_io exists")
        f.close()
    except:
        print("file_io not exists")

    lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT START")

    while True:
        try:
            check_notify_config_GD()
            for board in keyword_dict:  #keyword_dict[board]
                if board == "line_token":
                    if token != keyword_dict[board]["token"]:
                        token = keyword_dict[board]["token"]
                        print("token update!!!:", keyword_dict[board]["token"])
                else:
                    r = requests.get("https://www.ptt.cc/bbs/"+ board +"/index.html") #將網頁資料GET下來
                    soup = BeautifulSoup(r.text,"html.parser") #將網頁資料以html.parser

                    if FIRSTBOOT_CHECK_FLAG:
                        try:
                            check_board_exist = soup.select("div.main-container")[0].select("div.bbs-screen")[0].text
                            if "404 - Not Found" in check_board_exist:
                                lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有此版: " + board)
                        except:
                            pass
                    
                    posts = soup.select("div.r-ent") 

                    for post in posts:  #for each po文
                        pushNum = ""
                        poTitle = ""
                        poUrl = ""
                        poAuthor = ""
                        msg = ""
                        
                        #author
                        poAuthor =  post.select("div.meta div.author")[0].text
                        if poAuthor != "-":
                            #push numbers
                            pushNum_len = str(post.select("div.nrec")[0].select("span")).split('>', 1 )
                            if len(pushNum_len)>1:
                                pushNum_tmp = pushNum_len[1].replace("</span>]","")
                                if pushNum_tmp == "爆":
                                    pushNum = "100"
                                else:
                                    pushNum = pushNum_tmp
                            else:
                                pushNum  =  "0"
                            #push title and url
                            poTitle = post.select("div.title a")[0].text
                            poUrl = "https://www.ptt.cc"+post.select("div.title a")[0]["href"]
                            
                            if "公告" not in poTitle and "活動" not in poTitle:
                                if "key" in keyword_dict[board]:
                                    for key2 in keyword_dict[board]["key"]:
                                        if all(word.lower() in poTitle.lower() for word in key2):
                                            #print(poAuthor,pushNum,poTitle,poUrl)
                                            msg = '&'.join(str(e) for e in key2)
                                            make_line_msg(board,"key",pushNum,poTitle,poUrl,msg)
                                            pass
                                if "push" in keyword_dict[board]:
                                    if "X" not in pushNum:
                                        if int(pushNum) >= keyword_dict[board]["push"]:
                                            #print(poAuthor,pushNum,poTitle,poUrl)
                                            if pushNum == "100":
                                                pushNum = "爆"
                                            msg = pushNum
                                            make_line_msg(board,"push",pushNum,poTitle,poUrl,msg)
                                            pass
                                if "author" in keyword_dict[board]:
                                    if poAuthor in keyword_dict[board]["author"]:
                                        #print(poAuthor,pushNum,poTitle,poUrl)
                                        msg = poAuthor
                                        make_line_msg(board,"author",pushNum,poTitle,poUrl,msg)
                                        pass
                    time.sleep(2)
            #break
            FIRSTBOOT_CHECK_FLAG = False
            time.sleep(90)
        except Exception as e:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "error:", e)
            traceback.print_exc()
            time.sleep(10)
        except KeyboardInterrupt:
            # f.close()
            f = open(os.path.dirname(os.path.abspath(__file__))+'/file_io_'+token_prefix+'.txt', 'w')
            f.write("\n".join(sended))
            f.close()
            lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
            doubleCheck_Flag = False
            break

    if doubleCheck_Flag:    
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
