import sys
import requests, time
from bs4 import BeautifulSoup
import os
import traceback
from datetime import datetime
import json

file_url = "https://filedn.com/XXXXXXXXXX/config.json"
file_url_GD = "https://drive.google.com/uc?id=1RVbI3V1wJHWSiX6qlfu9PITA9-XXXXXX"

sys.stdout.reconfigure(encoding='utf-8')
cookies = {'over18': '1'}

token = ''
keyword_dict = dict()

chtype = {"key": "關鍵字", "push": "推文數", "author": "作者", }

CLOSE_CHECK_FLAG = True
FIRSTBOOT_CHECK_FLAG = True

class LimitedSet:
	def __init__(self, max_size=100):
		self.max_size = max_size
		self.data_set = set()  # 用於快速查找
		self.order_list = []	# 用於維持插入順序

	def add(self, value):
		if value not in self.data_set:
			if len(self.data_set) >= self.max_size:
				# 刪除最舊的項目
				oldest_value = self.order_list.pop(0)  # 刪除最舊的網址
				self.data_set.remove(oldest_value)	  # 同時從 set 中移除

			# 添加新網址
			self.data_set.add(value)
			self.order_list.append(value)

	def exists(self, value):
		return value in self.data_set

	def get_all(self):
		return self.order_list  # 返回當前所有網址的列表

sended = LimitedSet()

def log_msg(msg):
	print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)

def line_notify_message(msg):
	try:
		if token!= '':
			headers = {
				"Authorization": "Bearer " + token,
				"Content-Type": "application/x-www-form-urlencoded"
			}

			payload = {'message': msg}
			requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload, timeout=10)
			# return r_a.status_code
		else:
			log_msg("Line token 為空，無法傳送訊息")
	except Exception as e1:
		log_msg("line_notify_message Function Error: " + str(e1))

def make_line_msg(board_target, key_type, push_num, po_title, po_url, msg):
	if push_num == "100":
		push_num = "爆"
	push_msg = str(msg) + "@" + board_target + "\n" + "看板：" + board_target + " ; " + chtype[key_type] + "：" + str(msg) + "\n\n"
	push_msg += str(push_num) + " " + po_title + "\n" + po_url
	line_notify_message(push_msg)
	try:
		print(push_msg)
	except: # For Special Environment
		print("Environment encoding error, please add \"PYTHONIOENCODING=utf-8 python3 pttAlertor.py\" when executing")
	print("-----------------------------")

def load_config_from_pcloud():
	global keyword_dict
	try:
		response = requests.get(file_url, timeout=5)
		if response.status_code == 200:
			keyword_dict_new = json.loads(response.content.decode('utf-8'))
			if keyword_dict_new != keyword_dict:
				keyword_dict = keyword_dict_new
				log_msg("Keyword 更新:\n" + str(keyword_dict) + "\n")
				if not FIRSTBOOT_CHECK_FLAG:
					line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "Keywords 更新成功")
		else:
			log_msg("沒有辦法下載 Keywords 檔案")
			line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載 Keywords 檔案 ")
		response.close()
	except Exception as e2:
		log_msg("pcloud伺服器沒有回應" + str(e2))
		time.sleep(20)


def load_config_from_gdrive():
	global keyword_dict
	try:
		response = requests.get(file_url_GD, timeout=5)
		if response.status_code == 200:
			keyword_dict_new = json.loads(response.content.decode('utf-8'))
			if keyword_dict_new != keyword_dict:
				keyword_dict = keyword_dict_new
				log_msg("Keywords 更新:\n" + str(keyword_dict) + "\n")
				if not FIRSTBOOT_CHECK_FLAG:
					line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "Keywords 更新成功")
		else:
			log_msg("沒有辦法下載 Keywords 檔案")
			line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有辦法下載 Keywords 檔案 ")
		response.close()
	except Exception as e3:
		log_msg("GD伺服器沒有回應" + str(e3))
		time.sleep(20)


# 處理頁面內容
def process_posts(soup_, board_):
	global sended
	# 解析文章列表
	separator = soup_.find('div', class_='r-list-sep')
	posts = []
	if separator:
		for sibling in separator.previous_siblings:
			if sibling.name == 'div' and 'r-ent' in sibling.get('class', []):
				posts.append(sibling)
	else:
		posts.extend(soup_.find_all('div', class_='r-ent'))
	# posts = posts[::-1] // 越下面越新

	for post in posts:
		# 處理每篇文章
		po_author = post.select("div.meta div.author")[0].text
		if po_author != "-":  # 已刪文
			# 取得推文數
			push_tag = post.select_one("div.nrec span")
			push_num = push_tag.text if push_tag else "0"
			push_num = "100" if push_num == "爆" else push_num
			# 取得標題和連結
			title_tag = post.select_one("div.title a")
			if title_tag:
				po_title = title_tag.text
				po_url = "https://www.ptt.cc" + title_tag["href"]
				if "公告" not in po_title and "活動" not in po_title:
					# 根據關鍵字、推文數、作者進行過濾
					if not sended.exists(po_url):
						if "key" in keyword_dict[board_]:
							for key2 in keyword_dict[board_]["key"]:
								if all(word.lower() in po_title.lower() for word in key2):
									msg = '&'.join(str(st) for st in key2)
									make_line_msg(board_, "key", push_num, po_title, po_url, msg)
									sended.add(po_url)
						if "push" in keyword_dict[board_]:
							if "X" not in push_num and int(push_num) >= keyword_dict[board_]["push"]:
								msg = push_num
								make_line_msg(board_, "push", push_num, po_title, po_url, msg)
								sended.add(po_url)
						if "author" in keyword_dict[board_]:
							if po_author in keyword_dict[board_]["author"]:
								msg = po_author
								make_line_msg(board_, "author", push_num, po_title, po_url, msg)
								sended.add(po_url)



if __name__ == '__main__':
	ERROR_COUNT = 0
	FAILED_ATTEMPTS_COUNT = 0
	ERROR_NOTIFY_FLAG = False
	fileIOName = None
	msg2send = ""
	for _ in range(5):
		load_config_from_gdrive()
		try:
			token = keyword_dict["line_token"]["token"]
			token_prefix = keyword_dict["line_token"]["token"][:5]
			msg2send += "\n= 成功取得 Line Token =\n"
			break
		except KeyError:	
			FAILED_ATTEMPTS_COUNT += 1
		
	if FAILED_ATTEMPTS_COUNT >= 5:
		print("Error: Failed to get token after 5 attempts. Exiting program.")
		sys.exit()

	if os.path.exists("/tmp") and os.path.isdir("/tmp"):
		fileIOName = "/tmp" + f'/file_io_{token_prefix}.txt'
		msg2send += "= 成功運行於 Linux =\n"
	else:
		fileIOName = os.path.dirname(os.path.abspath(__file__)) + f'\\file_io_{token_prefix}.txt'
		msg2send += "= 成功運行於 Windows =\n"
	log_msg("File_IO 位置: " + fileIOName)
	

	try:
		with open(fileIOName, 'a+') as f:
			f.seek(0)
			for line in f:
				url = line.strip()  # 去掉行末的換行符
				if url:  # 確保不添加空行
					sended.add(url)
			msg2send += "= 成功讀取已通知列表 ="
	except FileNotFoundError:
		msg2send += "= 已通知列表不存在，建立空表 ="
	line_notify_message(msg2send)
	#line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT START")

	while True:
		try:
			load_config_from_gdrive()
			for board in keyword_dict:  # keyword_dict[board]
				if board == "line_token":
					if token != keyword_dict[board]["token"]:
						token = keyword_dict[board]["token"]
						log_msg("token update:" + str(keyword_dict[board]["token"]))
				else:
					url = "https://www.ptt.cc/bbs/" + board + "/index.html"
					r = requests.get(url, cookies=cookies, timeout=20)
					if r.status_code == 200:
						soup = BeautifulSoup(r.text, "html.parser")

						# 檢查看板是否存在
						if FIRSTBOOT_CHECK_FLAG:
							try:
								check_board_exist = soup.select("div.main-container")[0].select("div.bbs-screen")[0].text
								if "404 - Not Found" in check_board_exist:
									line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 沒有此版: " + board)
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
					else:
						raise requests.exceptions.RequestException("取得{}板的文章HTTP回響錯誤: {}".format(board,str(r.status_code)))

			# break
			FIRSTBOOT_CHECK_FLAG = False
			ERROR_NOTIFY_FLAG = False
			log_msg("Dump")
			ERROR_COUNT = 0
			time.sleep(90)
		except requests.exceptions.RequestException as e4:
			if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
				line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT伺服器沒有回應: " + str(e4))
				ERROR_NOTIFY_FLAG = True
			log_msg("["+str(ERROR_COUNT)+"] PTT伺服器沒有回應： " +  str(e4))
			# traceback.print_exc()
			ERROR_COUNT += 1
			time.sleep(90)
		except Exception as e5:
			if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
				line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Error: " + str(e5))
				ERROR_NOTIFY_FLAG = True
			log_msg("["+str(ERROR_COUNT)+"] Error:" + str(e5))
			traceback.print_exc()
			ERROR_COUNT += 1
			time.sleep(90)
		except KeyboardInterrupt:
			with open(fileIOName, 'w+') as f:
				for item in sended.get_all():
					f.write(f"{item}\n")
			log_msg("PTT ALERT STOP")
			line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
			CLOSE_CHECK_FLAG = False
			break

	if CLOSE_CHECK_FLAG:
		log_msg("PTT ALERT STOP")
		line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
