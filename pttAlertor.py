import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, time
from bs4 import BeautifulSoup
import re, os
import traceback
from datetime import datetime
import json

cookies = {'over18': '1'}
file_url = "https://filedn.com/XXXXXXXXXX/config.json"
file_url_GD = "https://drive.google.com/uc?id=1RVbI3V1wJHWSiX6qlfu9PITA9-XXXXXX"

# os.system("export PYTHONIOENCODING=utf8")

token = ''
sended = set()
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
        r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload, timeout=10)
        return r.status_code
    except Exception as e:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " lineNotifyMessage Function Error: ", e)
    
def make_line_msg(board,keytype,pushNum,poTitle,poUrl,msg):
    global sended
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
        sended.add(poUrl)
        while len(sended)>100:
            sended.pop(0)

def check_notify_config():
    global keyword_dict
    while True:
        try:
            response = requests.get(file_url, timeout=10)
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
            break
        except Exception as e:
            print("pcloud伺服器沒有回應", e)
            time.sleep(20)
    
def check_notify_config_GD():
    global keyword_dict
    while True:
        try:
            response = requests.get(file_url_GD, timeout=10)
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
            break
        except Exception as e:
            print("GD伺服器沒有回應", e)
            time.sleep(20)
    
if __name__ == '__main__':
    check_notify_config_GD()
    failed_attempts = 0
    for _ in range(5):
        try:
            print("token Get:", keyword_dict["line_token"]["token"])
            token = keyword_dict["line_token"]["token"]
            token_prefix = keyword_dict["line_token"]["token"][:5]
            if os.path.exists("/tmp") and os.path.isdir("/tmp"):
                fileIOName = "/tmp" + f'/file_io_{token_prefix}.txt'
            else:
                fileIOName = os.path.dirname(os.path.abspath(__file__)) + f'\\file_io_{token_prefix}.txt'
            print("File_IO 位置: ",fileIOName)
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
            sended = set(f.read().split("\n"))
            print("file_io exists")
    except FileNotFoundError:
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
                    url_array = []
                    url_array.append("https://www.ptt.cc/bbs/"+ board +"/index.html")
                    r = requests.get("https://www.ptt.cc/bbs/"+ board +"/index.html", cookies=cookies, timeout=20) #將網頁資料GET下來
                    soup = BeautifulSoup(r.text,"html.parser") #將網頁資料以html.parser
                    
                    previous_page_link = soup.find('div', id='action-bar-container').find('a', string='‹ 上頁')
                    
                    if previous_page_link:
                        #print(previous_page_link['href'])
                        url_array.append("https://www.ptt.cc"+ previous_page_link['href'])
                    # print(url_array)
                    for ur in url_array:
                        
                        r = requests.get(ur, cookies=cookies, timeout=20) 
                        soup = BeautifulSoup(r.text,"html.parser")
                        if FIRSTBOOT_CHECK_FLAG:
                            try:
                                check_board_exist = soup.select("div.main-container")[0].select("div.bbs-screen")[0].text
                                if "404 - Not Found" in check_board_exist:
                                    lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有此版: " + board)
                            except:
                                pass
                        
                        # 首先找到分隔元素
                        separator = soup.find('div', class_='r-list-sep')

                        posts = []
                        # 使用.previous_siblings 迭代器遍歷所有位於分隔線之上的兄弟節點
                        if separator:
                            for sibling in separator.previous_siblings:
                                if sibling.name == 'div' and 'r-ent' in sibling.get('class', []):
                                    posts.append(sibling)
                        else:
                            # 如果找不到分隔線，將所有包含 'r-ent' 類別的 div 全部加進去
                            all_divs = soup.find_all('div', class_='r-ent')
                            posts.extend(all_divs)

                        # 反轉列表以獲得正確的順序（從最舊到最新）
                        posts = posts[::-1]
      
                        # posts = soup.select("div.r-ent") 

                        for post in posts:  #for each po文
                            pushNum = ""
                            poTitle = ""
                            poUrl = ""
                            poAuthor = ""
                            msg = ""
                            
                            #author
                            poAuthor =  post.select("div.meta div.author")[0].text
                            if poAuthor != "-": # 已刪文
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
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Dump")
            time.sleep(90)
        except requests.exceptions.RequestException as e:
            print("PTT伺服器沒有回應： ", e)
        except Exception as e:
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "error:", e)
            traceback.print_exc()
            time.sleep(10)
        except KeyboardInterrupt:
            with open(fileIOName, 'w+') as f:
                for item in sended:
                    f.write(f"{item}\n")
            lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
            doubleCheck_Flag = False
            break

    if doubleCheck_Flag:    
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
