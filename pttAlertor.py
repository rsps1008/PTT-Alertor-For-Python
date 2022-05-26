import requests, time
from bs4 import BeautifulSoup
import re, os
import traceback
from datetime import datetime

FIRSTBOOT_CHECK_FLAG = True

keyword_dict =  { \
                    "Lifeismoney":  { \
                                        "key":[["Line","pay"],["pchome"],["point"],["蝦皮"]], \
                                        "push":50 \
                                    }, \
                    "tainan":       { \
                                        "key":["Line","群"] \
                                    }, \
                    "Kaohsiung":    { \
                                        "author":["exelop"] \
                                    }, \
                    "stock":        { \
                                        "author": ["a26893997","blueian","chengwaye","robertshih","nuggets","newconfidenc","guilty13","drgon","s10330076","tamama000","test520","zesonpso"] \
                                    }, \
                    "bank_service": { \
                                        "key":[["情報","中信"],["情報","國泰"],["情報","新光"],["情報","聯邦"]] \
                                    }, \
                    "creditcard":   { \
                                        "key":[["情報","聯邦"]] \
                                    }, \
                    "mobilecomm":   { \
                                        "key":[["mi","12","pro"],["小米","12","pro"],["magisk"]] \
                                    } \
                }


token = ''
sended = []
chtype = {"key":"關鍵字","push":"推文數","author":"作者",}

f = open(os.path.dirname(os.path.abspath(__file__))+'/file_io.txt', 'r')
sended = f.readline().split(",")

def lineNotifyMessage(msg):
    try:
        headers = {
            "Authorization": "Bearer " + token, 
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        payload = {'message': msg}
        r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
        return r.status_code
    except Exception as e:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), e)

lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT START")

while True:
    try:
        for board in keyword_dict:  #keyword_dict[board]
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
            
            def push_line(board,keytype,pushNum,poTitle,poUrl,msg):
                #print(board,keytype,pushNum,poTitle,poUrl,msg)
                #if 1:
                if poUrl not in sended:
                    push_msg = str(msg) + "@" + board + "\n" + "看板："+ board +" ; "+ chtype[keytype] + "：" + str(msg) + "\n\n"
                    push_msg += str(pushNum) + " " + poTitle + "\n" + poUrl
                    lineNotifyMessage(push_msg)
                    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), push_msg + "\n--------------------\n")
                    sended.append(poUrl)
                    while len(sended)>100:
                        sended.pop(0)  

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
                    poTitle_tmp = post.select("div.title a")
                    poTitle = poTitle_tmp[0].text
                    poUrl = "https://www.ptt.cc"+poTitle_tmp[0]["href"]
                    
                    if "公告" not in poTitle and "活動" not in poTitle:
                        if "key" in keyword_dict[board]:
                            for key2 in keyword_dict[board]["key"]:
                                if all(word.lower() in poTitle.lower() for word in key2):
                                    #print(poAuthor,pushNum,poTitle,poUrl)
                                    msg = '&'.join(str(e) for e in key2)
                                    push_line(board,"key",pushNum,poTitle,poUrl,msg)
                                    pass
                        if "push" in keyword_dict[board]:
                            if "X" not in pushNum:
                                if int(pushNum) >= keyword_dict[board]["push"]:
                                    #print(poAuthor,pushNum,poTitle,poUrl)
                                    msg = pushNum
                                    push_line(board,"push",pushNum,poTitle,poUrl,msg)
                                    pass
                        if "author" in keyword_dict[board]:
                            if poAuthor in keyword_dict[board]["author"]:
                                #print(poAuthor,pushNum,poTitle,poUrl)
                                msg = poAuthor
                                push_line(board,"author",pushNum,poTitle,poUrl,msg)
                                pass
            time.sleep(3)
        #break
        FIRSTBOOT_CHECK_FLAG = False
        time.sleep(60)
    except Exception as e:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "error:", e)
        traceback.print_exc()
    except KeyboardInterrupt:
        f.close()
        f = open(os.path.dirname(os.path.abspath(__file__))+'/file_io.txt', 'w')
        f.write(",".join(sended))
        f.close()
        lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
        break
    
lineNotifyMessage(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
