import sys
import requests, time
from bs4 import BeautifulSoup
import os
import traceback
from datetime import datetime
import json, random
import re
from collections import deque
from functools import lru_cache

file_url_GD = "https://drive.google.com/uc?id=1RVbI3V1wJHWSiX6qlfu9PITA9-XXXXXX"

sys.stdout.reconfigure(encoding='utf-8')
cookies = {'over18': '1'}

tokens = []
current_token = None
current_receiver = None
keyword_dict = dict()
update_frequency = 90

chtype = {"key": "關鍵字", "push": "推文數", "author": "作者", }

CLOSE_CHECK_FLAG = True
FIRSTBOOT_CHECK_FLAG = True

session = requests.Session()

class LimitedSet:
	def __init__(self, max_size=200):
		self.max_size = max_size
		self.q = deque(maxlen=max_size)   # 固定長度自動丟舊資料
		self.s = set()

	def add(self, value):
		if value in self.s:
			return

		# 若已滿，先記住即將被 deque 淘汰的最舊元素
		oldest = self.q[0] if len(self.q) == self.max_size else None

		self.q.append(value)			  # append 會自動 pop left
		if oldest is not None:
			self.s.discard(oldest)		# 同步移除 set 中的舊值
		self.s.add(value)


	def exists(self, value):
		return value in self.s

	def get_all(self):
		return list(self.q)

sended = LimitedSet()

def log_msg(msg):
	print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)

def line_notify_message(msg):
	global current_token, current_receiver

	headers = {
		"Authorization": f"Bearer {current_token}",
		"Content-Type": "application/json"
	}
	payload = {
		"to": current_receiver,
		"messages": [ { "type": "text", "text": msg } ]
	}
	try:
		response = session.post(
			"https://api.line.me/v2/bot/message/push",
			headers=headers,
			data=json.dumps(payload)
		)
		if response.status_code == 200:
			log_msg(f"\n-----------------------------\n訊息發送成功: \n{msg} \n-----------------------------\n")
		elif response.status_code == 429:
			log_msg(f"發送失敗: {response.status_code} - Rate Limit Exceeded. 隨機換一組 Token 再試。{msg}")
			current_token = random.choice(tokens)
			line_notify_message(msg)
			time.sleep(1)
		else:
			log_msg(f"發送失敗: {response.status_code}")
			log_msg(response.json())
	except Exception as e:
		log_msg(f"發送失敗，發生例外: {e}")

def make_line_msg(board_target, key_type, push_num, po_title, po_url, msg):
	push_num_display = "爆" if push_num == "100" else push_num
	push_msg = (
		f"{msg}@{board_target}\n"
		f"看板：{board_target} ; {chtype[key_type]}：{msg}\n\n"
		f"{push_num_display} {po_title}\n{po_url}"
	)
	line_notify_message(push_msg)

def load_config_from_gdrive():
	global keyword_dict, tokens, current_token, current_receiver
	try:
		r = session.get(file_url_GD, timeout=5)
		if r.status_code == 200:
			new_dict = json.loads(r.content.decode('utf-8'))
			if new_dict != keyword_dict:
				new_tokens   = new_dict.get("line_token", [])
				new_receiver = new_dict.get("line_receiver", "")

				if not new_tokens or not new_receiver:
					log_msg("Config 更新失敗：line_token 或 line_receiver 缺失")
					# 用已設定的 token/receiver 發出通知
					if current_token and current_receiver:
						line_notify_message(
							"⚠️ Config 更新失敗：請同時補齊 line_token 與 line_receiver！"
						)
					# 清空，讓主迴圈暫停爬蟲
					tokens = []
					current_token = None
					current_receiver = None
				else:
					# 一切正常，套用新設定
					keyword_dict = new_dict
					tokens = new_tokens
					if current_token not in tokens:
						log_msg("原token不在新列表中，更新token")
						current_token = random.choice(tokens)
					current_receiver = new_receiver
					log_msg("Config 更新完成，已套用新 token & receiver")
					if not FIRSTBOOT_CHECK_FLAG:
						line_notify_message(
							f"{datetime.now():%Y-%m-%d %H:%M:%S} Config 更新成功"
						)
		else:
			log_msg(f"下載 Config 檔失敗: HTTP {r.status_code}")
			if current_token and current_receiver:
				line_notify_message(
					f"⚠️ 下載 Config 檔失敗: HTTP {r.status_code}"
				)
		r.close()
	except Exception as ex:
		log_msg("GD 配置檔有誤: " + str(ex))
		if current_token and current_receiver:
			line_notify_message(f"⚠️ GD 配置檔有誤: {ex}")
		time.sleep(20)

def match_keywords(title, keyword_groups):
	title_lower = title.lower()
	for key_group in keyword_groups:
		# 確保每個詞都在標題中（AND 條件）
		if all(re.search(re.escape(word.lower()), title_lower) for word in key_group):
			return key_group
	return None

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
							keywords = keyword_dict[board_]["key"]
							match = match_keywords(po_title, keywords)
							if match:
								msg = '&'.join(match)
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
	# 初始化
	for _ in range(5):
		load_config_from_gdrive()
		try:
			tokens = keyword_dict["line_token"]
			current_token = random.choice(tokens)
			token_prefix = keyword_dict["line_token"][0][:5]
			msg2send += f"= 成功取得 Line Tokens: {current_token}(隨機) =\n"
			current_receiver = keyword_dict["line_receiver"]
			msg2send += f"= 成功設定接收者：{current_receiver} =\n"
			break
		except KeyError:	
			FAILED_ATTEMPTS_COUNT += 1
		
	if FAILED_ATTEMPTS_COUNT >= 5:
		print("Error: Failed to get tokens after 5 attempts. Exiting program.")
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
			# 先拉最新 config
			load_config_from_gdrive()

			# tokens 或 receiver 若任一為空，就跳過爬蟲、60秒後再試
			if not tokens or not current_receiver:
				log_msg(f"line_token 或 line_receiver 未設定，暫停爬蟲 {update_frequency} 秒")
				time.sleep(update_frequency)
				continue

			# 只有真正的看板 key 才做爬蟲
			for board in keyword_dict:  # keyword_dict[board]
				if board in ("line_token", "line_receiver"):
					continue
				else:
					url = "https://www.ptt.cc/bbs/" + board + "/index.html"
					r = session.get(url, cookies=cookies, timeout=20)
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
							r = session.get(previous_page_url, cookies=cookies, timeout=20)
							soup_pre = BeautifulSoup(r.text, "html.parser")
							process_posts(soup_pre, board)

						# 處理當前頁面
						process_posts(soup, board)
					else:
						raise requests.exceptions.RequestException("取得{}板的文章HTTP回響錯誤: {}".format(board,str(r.status_code)))

			# break
			FIRSTBOOT_CHECK_FLAG = False
			ERROR_NOTIFY_FLAG = False
			# 每輪結束時就存檔
			try:
				with open(fileIOName, 'w+') as f:
					for item in sended.get_all():
						f.write(f"{item}\n")
			except Exception as e:
				log_msg("寫入通知記錄檔失敗：" + str(e))
			log_msg("Dump")
			ERROR_COUNT = 0
			backoff = min(update_frequency * (2 ** min(ERROR_COUNT, 5)), 270)  # 最多 600 秒
			time.sleep(backoff)
		except requests.exceptions.RequestException as e4:
			if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
				line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT伺服器沒有回應: " + str(e4))
				ERROR_NOTIFY_FLAG = True
			log_msg("["+str(ERROR_COUNT)+"] PTT伺服器沒有回應： " +  str(e4))
			# traceback.print_exc()
			ERROR_COUNT += 1
			time.sleep(update_frequency)
		except Exception as e5:
			if ERROR_COUNT > 40 and ERROR_NOTIFY_FLAG == False:
				line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Error: " + str(e5))
				ERROR_NOTIFY_FLAG = True
			log_msg("["+str(ERROR_COUNT)+"] Error:" + str(e5))
			traceback.print_exc()
			ERROR_COUNT += 1
			time.sleep(update_frequency)
		except KeyboardInterrupt:
			with open(fileIOName, 'w+') as f:
				for item in sended.get_all():
					f.write(f"{item}\n")
			log_msg("PTT ALERT STOP")
			line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
			CLOSE_CHECK_FLAG = False
			session.close()
			break

	if CLOSE_CHECK_FLAG:
		log_msg("PTT ALERT STOP")
		line_notify_message(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " PTT ALERT STOP")
