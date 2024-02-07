import os, time, csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import configparser
import re

from sys import argv

print("\n" * 100)

os.environ["DEBUSSY"] = "1"

# Configure browser session
wd_options = Options()
wd_options.add_argument("--disable-notifications")
wd_options.add_argument("--disable-infobars")
wd_options.add_argument("--mute-audio")
browser = webdriver.Chrome(options=wd_options)

# --------------- Ask user to log in -----------------
def fb_login(credentials):
	print("Opening browser...")
	email = credentials.get('credentials', 'email')
	password = credentials.get('credentials', 'password')
	browser.get("https://www.facebook.com/")
	browser.find_element(By.ID, 'email').send_keys(email)
	browser.find_element(By.ID, 'pass').send_keys(password)
	browser.find_element(By.NAME, 'login').click()

# --------------- Scroll to bottom of page -----------------
def scroll_to_bottom():
	SCROLL_PAUSE_TIME = 0.5

	# Get scroll height
	last_height = browser.execute_script("return document.body.scrollHeight")

	while True:
			# Scroll down to bottom
			browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			# Wait to load page
			time.sleep(SCROLL_PAUSE_TIME)

			# Calculate new scroll height and compare with last scroll height
			new_height = browser.execute_script("return document.body.scrollHeight")
			if new_height == last_height:
					break
			last_height = new_height

# --------------- Get list of all friends on page ---------------
def scan_friends():
	print('Scanning page for friends...')
	friends = []
	friend_names = browser.find_elements(By.XPATH, '//span[@class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u"]')

	for friend_name in friend_names:
		print(friend_name.text)
		friend_active = 1

		friends.append({
			'name': friend_name.text.encode('utf-8', 'ignore'),
			'active': friend_active
			})

	print('Found %r friends on page!' % len(friends))
	return friends

# ----------------- Load list from CSV -----------------
def load_csv(filename):
	inact = 0
	myfriends = []
	with open(filename, 'rt', encoding="utf-8") as input_csv:
		reader = csv.DictReader(input_csv)
		for idx,row in enumerate(reader):
			if row['active'] is '1':
				myfriends.append({
					"name":row['B_name'],
					"uid":row['B_id']
					})
			else:
				print("Skipping %s (inactive)" % row['B_name'])
				inact = inact + 1
	print("%d friends in imported list" % (idx+1))
	print("%d ready for scanning (%d inactive)" % (idx-inact+1, inact))
	return myfriends

# --------------- Scrape 1st degree friends ---------------
def scrape_1st_degrees():
	#Prep CSV Output File
	csvOut = '1st-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
	writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
	#writer.writerow(['A_id','A_name','B_id','B_name','active'])
	writer.writerow(['A_id', 'A_name', 'B_name', 'active'])

	#Get your unique Facebook ID
	profile_icon = browser.find_element(By.XPATH, "//div[@class='x1iyjqo2']/ul/li/div/a")
	url_content = profile_icon.get_attribute("href")

	# case 1
	href_content = re.search(r"[^0-9]+", url_content)
	myid = url_content[:href_content.start()] + url_content[href_content.end():]

	if len(myid) == 0:
		# case 2
		start_content = re.search(r"\bcom", url_content)
		# start_content = re.search(r"[a-z]", content)
		new_url = url_content[:start_content.start()] + url_content[start_content.end():]
		size = len(new_url)
		other_myid = new_url[start_content.end() - (start_content.end() - start_content.start()):size]

		unique_myid = other_myid
	else:
		unique_myid = myid

	#Scan your Friends page (1st-degree friends)
	print("Opening Friends page...")
	browser.get("https://www.facebook.com/" + unique_myid + "/friends")
	scroll_to_bottom()
	myfriends = scan_friends()

	#Write friends to CSV File
	for friend in myfriends:
			writer.writerow([myid, "Me", friend['name'], friend['active']])

	print("Successfully saved to %s" % csvOut)

# --------------- Scrape 2nd degree friends. ---------------
#This can take several days if you have a lot of friends!!
def scrape_2nd_degrees():
	#Prep CSV Output File
	csvOut = '2nd-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
	writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
	writer.writerow(['A_id', 'B_id', 'A_name','B_name','active'])

	#Load friends from CSV Input File
	script, filename = argv
	print("Loading list from %s..." % filename)
	myfriends = load_csv(filename)
	print("------------------------------------------")
	for idx,friend in enumerate(myfriends):
		#Load URL of friend's friend page
		scrape_url = "https://www.facebook.com/"+ friend['uid'] + "/friends?source_ref=pb_friends_tl"
		browser.get(scrape_url)

		#Scan your friends' Friends page (2nd-degree friends)
		print("%d) %s" % (idx+1, scrape_url))
		scroll_to_bottom()
		their_friends = scan_friends()

		#Write friends to CSV File
		print('Writing friends to CSV...')
		for person in their_friends:
			writer.writerow([friend['uid'],person['id'],friend['name'],person['name'],person['active']])

# --------------- Start Scraping ---------------
now = datetime.now()
configPath = "config.txt"
if configPath:
	configObj = configparser.ConfigParser()
	configObj.read(configPath)
	email = configObj.get('credentials', 'email')
	password = configObj.get('credentials', 'password')
else:
	print('Enter the config path')
fb_login(configObj)

if len(argv) is 1:
	scrape_1st_degrees()
elif len(argv) is 2:
	scrape_2nd_degrees()
else:
	print("Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the CSV file as the first argument.")
