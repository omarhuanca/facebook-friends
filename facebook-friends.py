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
    SCROLL_PAUSE_TIME = 0.5

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
            #print(friend_name.text)
            friend_id_value = friend.get_attribute("href")
            friend_username = get_profile_from_url(friend_id_value)
            #print('username ' + friend_username)
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
            if row['B_active'] is '1':
                myfriends.append({
                    "name": row['B_name'],
                    "uid": row['B_id']
                })
    print("%d friends in imported list" % (idx + 1))
    return myfriends


# --------------- Scrape 1st degree friends ---------------
def scrape_1st_degrees():
    # Prep CSV Output File
    csvOut = '1st_%s.csv' % now.strftime("%Y_%m_%d_%H%M")
    writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
    writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_active'])

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
    unique_myid = ''
    profile = filter_string(r"com{1}", url_value)
    if "=" in profile:
        username = filter_string(r"[?]", profile)
    else:
        username = profile

    string_dot = filter_string(r"[0-9]+", username)
    number = filter_string(r"[a-z\\.]+", username)

    username = change_value_string(username)
    string_dot = change_value_string(string_dot)

    if len(username) > len(string_dot):
        if len(username) > len(number):
            unique_myid = username
    elif len(string_dot) > len(number):
        unique_myid = string_dot
    elif len(number) > len(username):
        unique_myid = number

    return unique_myid


def change_value_string(potential_string):
    if "=" in potential_string:
        potential_string = ''
    return potential_string

def filter_string(regex, potential_string):
    split_response = ''
    if len(potential_string) > 0 and len(regex) > 0:
        regex_string = re.search(regex, potential_string)
        if regex_string is not None:
            split_string = potential_string[:regex_string.start()] + potential_string[regex_string.end():]
            split_response = split_string[regex_string.end() +1 - (regex_string.end() - regex_string.start()):]

    return split_response

# --------------- Scrape 2nd degree friends. ---------------
# This can take several days if you have a lot of friends!!
def scrape_2nd_degrees():
    # Load friends from CSV Input File
    filename = input("Enter the filename .csv from the first contact list: ")
    if "1st_" in filename and len(filename) > 0:
        print("Loading list from %s..." % filename)
        myfriends = load_csv(filename)
        print("------------------------------------------")
        search_name = input("Enter name you want search in your contact list: ")
        search_name = search_name.strip().lower()
        for idx, friend in enumerate(myfriends):
            if search_name in friend['name'].lower():

                # Prep CSV Output File
                csvOut = '2nd_%s.csv' % now.strftime("%Y_%m_%d_%H%M")
                writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
                writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_active'])

                # Load URL of friend's friend page
                scrape_url = "https://www.facebook.com/" + friend['uid'] + "/friends?source_ref=pb_friends_tl"
                browser.get(scrape_url)

                # Scan your friends' Friends page (2nd-degree friends)
                #print("%d) %s" % (idx + 1, scrape_url))
                print("name is found in your %d contact" % (idx + 1))
                scroll_to_bottom()
                their_friends = scan_friends()

                # Write friends to CSV File
                print('Writing friends to CSV...')
                for person in their_friends:
                    writer.writerow([friend['uid'], friend['name'], person['id'], person['name'], person['active']])
            else:
                print("name is not found in your %d contact" % (idx + 1))
    else:
        print("Invalid filename .csv from the first contact list")

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

item_option = input("Enter number value 1 or 2 to generate list: ")

if item_option == "1":
    scrape_1st_degrees()
elif item_option == "2":
    scrape_2nd_degrees()
else:
    print(
        "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the CSV file as the first argument.")
