import os, time, csv, sys
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
from time import sleep

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
    SCROLL_PAUSE_TIME = 0.8

    xpath_first_page_friend = '//div[@class="x1iyjqo2 x1pi30zi"]/div/a'
    numerator = browser.find_elements(By.XPATH, xpath_first_page_friend).__sizeof__()
    denominator = 2
    quantity = numerator // denominator
    counter = 0
    # Get scroll height
    while quantity > counter:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        counter = counter + 1


# --------------- Get list of all friends on page ---------------
def scan_friends():
    print('Scanning page for friends...')
    friends = []
    # friend_names = browser.find_elements(By.XPATH, '//span[@class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x3x7a5m x1lkfr7t x1lbecb7 x1s688f xzsf02u"]')
    try:
        xpath_first_page_friend = '//div[@class="x1iyjqo2 x1pi30zi"]/div/a'
        list_friend = browser.find_elements(By.XPATH, xpath_first_page_friend)

        for friend in list_friend:
            friend_name = friend.find_element(By.TAG_NAME, 'span')
            print(friend_name.text)
            friend_id_value = friend.get_attribute("href")
            friend_username = get_profile_from_url(friend_id_value)
            print('username ' + friend_username)
            friend_active = 1

            friends.append({
                'name': friend_name.text,
                'id': friend_username,
                'active': friend_active
            })

        print('Found %r friends on page!' % len(friends))
    except NoSuchElementException:
        print("The element does not exist.")
    return friends

# ----------------- Load list from CSV -----------------
def load_csv(filename):
    myfriends = []
    with open(filename, 'rt', encoding="utf-8") as input_csv:
        reader = csv.DictReader(input_csv)
        for idx, row in enumerate(reader):
            if row['active'] is '1':
                myfriends.append({
                    "name": row['B_name'],
                    "uid": row['B_id']
                })
    print("%d friends in imported list" % (idx + 1))
    return myfriends

# --------------- Scrape 1st degree friends ---------------
def scrape_1st_degrees():
    # Prep CSV Output File
    csvOut = '1st-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
    writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
    writer.writerow(['A_id','A_name','B_id','B_name','active'])

    # Get your unique Facebook ID
    profile_icon = browser.find_element(By.XPATH, "//div[@class='x1iyjqo2']/ul/li/div/a")
    url_content = profile_icon.get_attribute("href")
    unique_myid = get_profile_from_url(url_content)

    # Scan your Friends page (1st-degree friends)
    print("Opening Friends page...")
    browser.get("https://www.facebook.com/" + unique_myid + "/friends")
    scroll_to_bottom()
    myfriends = scan_friends()

    # Write friends to CSV File
    for friend in myfriends:
        writer.writerow([unique_myid, "Me", friend['id'], friend['name'], friend['active']])

    print("Successfully saved to %s" % csvOut)

def get_profile_from_url(url_value):
    # case 1
    myid = get_number_profile_from_url(url_value)

    if len(myid) == 0:
        # case 2
        unique_myid = get_name_profile_from_url(url_value)
    else:
        unique_myid = myid

    return unique_myid


def get_number_profile_from_url(url_value):
    response = ''
    if len(url_value) > 0:
        href_content = re.search(r"[^0-9]+", url_value)
        response = url_value[:href_content.start()] + url_value[href_content.end():]

    return response

def get_name_profile_from_url(url_value):
    response = ''
    if len(url_value) > 0:
        start_content = re.search(r"\bcom", url_value)
        new_url = url_value[:start_content.start()] + url_value[start_content.end():]
        size = len(new_url)
        response = new_url[start_content.end() +1 - (start_content.end() - start_content.start()):size]

    return response

# --------------- Scrape 2nd degree friends. ---------------
# This can take several days if you have a lot of friends!!
def scrape_2nd_degrees():
    # Prep CSV Output File
    csvOut = '2nd-degree_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
    writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
    writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'active'])

    # Load friends from CSV Input File
    #script, filename = argv
    script = argv
    filename = '1st-degree_2024-02-07_1609.csv'
    print("Loading list from %s..." % filename)
    myfriends = load_csv(filename)
    print("------------------------------------------")
    for idx, friend in enumerate(myfriends):
        # Load URL of friend's friend page
        scrape_url = "https://www.facebook.com/" + friend['uid'] + "/friends?source_ref=pb_friends_tl"
        browser.get(scrape_url)

        # Scan your friends' Friends page (2nd-degree friends)
        print("%d) %s" % (idx + 1, scrape_url))
        scroll_to_bottom()
        their_friends = scan_friends()

        # Write friends to CSV File
        print('Writing friends to CSV...')
        for person in their_friends:
            writer.writerow([friend['uid'], friend['name'], person['id'], person['name'], person['active']])

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
    print(
        "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the CSV file as the first argument.")
