import configparser
import csv
import os
import re
import time
import sys

from datetime import datetime
from random import randint
from time import sleep
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver import ActionChains

print("\n" * 100)

os.environ["DEBUSSY"] = "1"

# Configure browser session
wd_options = Options()
wd_options.add_argument("--disable-notifications")
wd_options.add_argument("--disable-infobars")
wd_options.add_argument("--mute-audio")
# wd_options.add_argument("--headless")
browser = webdriver.Chrome(options=wd_options)
browser.implicitly_wait(45)


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
def generate_numerator(xpath_first_page_friend):
    numerator = 0
    try:
        if len(xpath_first_page_friend) > 0:
            numerator = browser.find_elements(By.XPATH, xpath_first_page_friend).__sizeof__()
    except NoSuchElementException:
        print("No Details")

    return numerator


def generate_numerator_css(xpath_first_page_friend):
    numerator = 0
    try:
        if len(xpath_first_page_friend) > 0:
            numerator = len(browser.find_elements(By.CSS_SELECTOR, xpath_first_page_friend))
    except NoSuchElementException:
        print("No Details")

    return numerator


def scroll_to_bottom(xpath_first_page_friend, denominator, scrollPauseTime):
    numerator = generate_numerator(xpath_first_page_friend)
    quantity = numerator // denominator

    counter = 0
    # Get scroll height
    while quantity > counter:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(scrollPauseTime)

        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        counter = counter + 1


def scroll_to_bottom_two(css_first_page_friend, scrollPauseTime):
    numerator = generate_numerator_css(css_first_page_friend)
    counter = 0
    # Get scroll height
    while numerator >= counter:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scrollPauseTime)
        counter = generate_numerator_css(css_first_page_friend)
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")


# --------------- Get list of all friends on page ---------------
def generate_friend_list_dictionary():
    friends = []
    try:
        xpath_first_page_friend = '//div[@class="x1iyjqo2 x1pi30zi"]/div/a'
        list_friend = browser.find_elements(By.XPATH, xpath_first_page_friend)

        for friend in list_friend:
            friend_name = friend.find_element(By.TAG_NAME, 'span')
            friend_id_value = friend.get_attribute("href")
            friend_username = get_profile_from_url(friend_id_value)

            friends.append({
                'name': friend_name.text,
                'id': friend_username,
                'profile': friend_id_value,
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
            myfriends.append({
                "name": row['B_name'],
                "uid": row['B_id'],
                "profile": row['B_profile']
            })
    print("%d friends in imported list" % (idx + 1))
    return myfriends


def load_csv_two(filename):
    myfriends = []
    with open(filename, 'rt', encoding="utf-8") as input_csv:
        reader = csv.DictReader(input_csv)
        for idx, row in enumerate(reader):
            myfriends.append({
                "name": row['B_name'],
                "profile": row['B_profile'],
                "username": get_profile_from_url(row['B_profile'])
            })
    print("%d friends in imported list" % (idx + 1))
    return myfriends

def loadCustomCsv(filename, lastname, secondLastname, firstname, middlename):
    arrayPotential = []
    with open(filename, 'rt', encoding="utf-8") as inputCsv:
        reader = csv.DictReader(inputCsv)
        for idx, row in enumerate(reader):
            potentialContact = PotentialContact(row[lastname], row[secondLastname], row[firstname], row[middlename])
            arrayPotential.append(potentialContact)

    print("%d quantity of item" % (idx + 1))
    return arrayPotential

# --------------- Scrape 1st degree friends ---------------
def scrape_1st_degrees(prefix):
    if len(prefix) > 0:
        # Prep CSV Output File
        csvOut = prefix + "%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile'])

        csvOutGroup = prefix + "group_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writerGroup = csv.writer(open(csvOutGroup, 'w', encoding="utf-8"))
        writerGroup.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile'])

        try:
            # Get your unique Facebook ID
            profile_icon = browser.find_element(By.XPATH, '//div[@class="x1iyjqo2"]/ul/li/div/a')
            url_content = profile_icon.get_attribute("href")
            unique_myid = get_profile_from_url(url_content)

            # Scan your Friends page (1st-degree friends)
            print("Opening Friends page...")
            browser.get("https://www.facebook.com/" + unique_myid + "/friends")
            scroll_to_bottom('//div[@class="x1iyjqo2 x1pi30zi"]/div/a', 2, 0.5)
            # myfriends = scan_friends()
            myfriends = generate_friend_list_dictionary()

            # Write friends to CSV File
            for friend in myfriends:
                if "groups" in friend['profile']:
                    writerGroup.writerow([unique_myid, "Me", friend['id'], friend['name'], friend['profile']])
                else:
                    writer.writerow([unique_myid, "Me", friend['id'], friend['name'], friend['profile']])

            print("Successfully saved to %s" % csvOut)
            print("Successfully saved to %s" % csvOutGroup)

        except NoSuchElementException:
            print("No Details")


def get_profile_from_url(url_value):
    unique_myid = ""
    profile = filter_string(r"com{1}", url_value)
    if "=" in profile:
        username = filter_string(r"[?]", profile)
    else:
        username = profile

    if len(username) > 0:

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
            split_response = split_string[regex_string.end() + 1 - (regex_string.end() - regex_string.start()):]

    return split_response

def filter_string_two(regex, potential_string):
    split_response = ''
    if len(potential_string) > 0 and len(regex) > 0:
        regex_string = re.search(regex, potential_string)
        if regex_string is not None:
            split_string = potential_string[:regex_string.start()] + potential_string[regex_string.end():]
            split_response = split_string[:regex_string.end() -1]

    return split_response


# --------------- Scrape 2nd degree friends. ---------------
# This can take several days if you have a lot of friends!!
def scrape_2nd_degrees(prefix):
    # Load friends from CSV Input File
    filenameReader = input("Enter the filename .csv from the contact list: ")
    if len(filenameReader) > 0 and len(prefix):
        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv(filenameReader)
        print("------------------------------------------")
        search_name = input("Enter name you want search in your contact list: ")
        search_name = search_name.strip().lower()

        # Prep CSV Output File
        csvOut = prefix + "%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile'])

        for idx, friend in enumerate(myfriends):
            if search_name in friend['name'].lower():
                try:
                    # Load URL of friend's friend page
                    scrape_url = "https://www.facebook.com/" + friend['uid'] + "/friends?source_ref=pb_friends_tl"
                    browser.get(scrape_url)

                    # Scan your friends' Friends page (2nd-degree friends)
                    # print("%d) %s" % (idx + 1, scrape_url))
                    print("name is found in your %d contact" % (idx + 1))
                    scroll_to_bottom('//div[@class="x1iyjqo2 x1pi30zi"]/div/a', 2, 0.5)
                    their_friends = generate_friend_list_dictionary()

                    # Write friends to CSV File
                    print('Writing friends to CSV...')
                    for person in their_friends:
                        writer.writerow(
                            [friend['uid'], friend['name'], person['id'], person['name'], person['profile']])
                except NoSuchElementException:
                    print("No Details")
            else:
                print("name is not found in your %d contact" % (idx + 1))

        print("Successfully saved to %s" % csvOut)
    else:
        print("Invalid filename .csv from the first contact list")


def getListFriendFromFile(prefix):
    # Load friends from CSV Input File
    filenameReader = input("Enter the filename .csv from the contact list: ")
    if len(filenameReader) > 0 and len(prefix):
        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)
        print("------------------------------------------")

        # Prep CSV Output File
        csvOut = prefix + "user_friend_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_name', 'B_name', 'B_like'])

        for idx, friend in enumerate(myfriends):
            try:
                # Load URL of friend's friend page

                scrape_url = "https://www.facebook.com/" + friend['username'] + "/friends?source_ref=pb_friends_tl"
                browser.get(scrape_url)

                # Scan your friends' Friends page (2nd-degree friends)
                # print("%d) %s" % (idx + 1, scrape_url))
                print("name is found in your %d contact" % (idx + 1))
                scroll_to_bottom('//div[@class="x1iyjqo2 x1pi30zi"]/div/a', 2, 0.5)
                their_friends = generate_friend_list_dictionary()

                # Write friends to CSV File
                print('Writing friends to CSV...')
                for person in their_friends:
                    writer.writerow([friend['name'], person['name'], person['profile']])
                    # print([friend['name'], person['name'], person['profile']])
            except NoSuchElementException:
                print("No Details")

        print("Successfully saved to %s" % csvOut)
    else:
        print("Invalid filename .csv from the first contact list")


# Collecting FB data: [ Names, FB Profile Links, Phone Number, Gender, Birth Day ]
def get_data_info():
    all_friends_phone_number = []
    all_friends_email = []
    all_friends_gender = []
    all_friends_date = []
    all_friends_year = []
    all_friends_language = []
    # Have to separate each link, because some of profile links have username, and others just default fb numbers

    for friend in generate_friend_list_dictionary():
        each_link = friend['profile']
        try:
            if "profile.php" in each_link:
                browser.get(url=f"{each_link}&sk=about_contact_and_basic_info")
                get_info_basic_info(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                                    all_friends_phone_number, all_friends_year, friend)

            elif "groups" not in each_link:
                browser.get(url=f"{each_link}/about_contact_and_basic_info")
                get_info_basic_info(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                                    all_friends_phone_number, all_friends_year, friend)

        except NoSuchElementException:
            print("No Details")


def getDataInfoFromFile(prefix):
    all_friends_phone_number = []
    all_friends_email = []
    all_friends_gender = []
    all_friends_date = []
    all_friends_year = []
    all_friends_language = []
    all_friends_website = []
    # Have to separate each link, because some of profile links have username, and others just default fb numbers

    csvOut = prefix + "basic_info_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
    writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
    writer.writerow(['Name', 'Mobile', 'Email', 'Gender', 'Birthday', 'Year', 'Language', 'Website'])

    filenameReader = input("Enter the filename .csv: ")
    print("Loading list from %s..." % filenameReader)
    myfriends = load_csv_two(filenameReader)

    for friend in myfriends:
        each_link = friend['profile']
        try:
            if "profile.php" in each_link:
                browser.get(url=f"{each_link}&sk=about_contact_and_basic_info")
                readBasicInfo(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                              all_friends_phone_number, all_friends_year, all_friends_website, friend)

            elif "groups" not in each_link:
                browser.get(url=f"{each_link}/about_contact_and_basic_info")
                readBasicInfo(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                              all_friends_phone_number, all_friends_year, all_friends_website, friend)

        except NoSuchElementException:
            print("No Details")

    for friend in myfriends:
        username = friend['username']
        date = getValueFromArray(username, all_friends_date)
        email = getValueFromArray(username, all_friends_email)
        gender = getValueFromArray(username, all_friends_gender)
        language = getValueFromArray(username, all_friends_language)
        phoneNumber = getValueFromArray(username, all_friends_phone_number)
        year = getValueFromArray(username, all_friends_year)
        website = getValueFromArray(username, all_friends_website)
        # print([username, phoneNumber, email, gender, date, year, language, website])
        writer.writerow([username, phoneNumber, email, gender, date, year, language, website])


def get_info_basic_info(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                        all_friends_phone_number, all_friends_year, friend):
    sleep(randint(1, 3))
    information_list = browser.find_elements(By.XPATH,
                                             '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
    ph_list = []
    url_value = friend['id']
    for pn_item in information_list:
        if len(pn_item.text) > 0:
            ph_list.append(pn_item.text)
    for pn_item in ph_list:
        if pn_item == "Mobile":
            item_id = ph_list.index(pn_item) - 1
            all_friends_phone_number.append({url_value: ph_list[item_id]})
        if pn_item == "Email":
            item_id = ph_list.index(pn_item) - 1
            all_friends_email.append({url_value: ph_list[item_id]})
        if pn_item == "Gender":
            item_info = ph_list.index(pn_item) - 1
            all_friends_gender.append({url_value: ph_list[item_info]})
        if pn_item == "Birth date":
            item_date = ph_list.index(pn_item) - 1
            all_friends_date.append({url_value: ph_list[item_date]})
        if pn_item == "Birth year":
            item_year = ph_list.index(pn_item) - 1
            all_friends_year.append({url_value: ph_list[item_year]})
        if pn_item == "Languages":
            item_year = ph_list.index(pn_item) - 1
            all_friends_language.append({url_value: ph_list[item_year]})
    sleep(2)


def readBasicInfo(all_friends_date, all_friends_email, all_friends_gender, all_friends_language,
                  all_friends_phone_number, all_friends_year, all_friends_website, friend):
    information_list = browser.find_elements(By.XPATH,
                                             '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
    ph_list = []
    username = friend['username']
    for pn_item in information_list:
        if len(pn_item.text) > 0:
            ph_list.append(pn_item.text)
    for pn_item in ph_list:
        if pn_item == "Mobile":
            item_id = ph_list.index(pn_item) - 1
            all_friends_phone_number.append({username: ph_list[item_id]})
        if pn_item == "Email":
            item_id = ph_list.index(pn_item) - 1
            all_friends_email.append({username: ph_list[item_id]})
        if pn_item == "Gender":
            item_info = ph_list.index(pn_item) - 1
            all_friends_gender.append({username: ph_list[item_info]})
        if pn_item == "Birth date":
            item_date = ph_list.index(pn_item) - 1
            all_friends_date.append({username: ph_list[item_date]})
        if pn_item == "Birth year":
            item_year = ph_list.index(pn_item) - 1
            all_friends_year.append({username: ph_list[item_year]})
        if pn_item == "Languages":
            item_language = ph_list.index(pn_item) - 1
            all_friends_language.append({username: ph_list[item_language]})
        if pn_item == "Website":
            itemWebsite = ph_list.index(pn_item) - 1
            all_friends_website.append({username: ph_list[itemWebsite]})


def generate_user_like_from_list(prefix):
    filenameReader = input("Enter the filename .csv from contact list: ")
    if len(filenameReader) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv(filenameReader)
        response_list = []

        for friend in myfriends:
            each_link = friend['profile']
            item_list = []
            try:
                if "groups" not in each_link:
                    if "profile.php" in each_link:
                        browser.get(url=f"{each_link}&sk=likes")
                    else:
                        browser.get(url=f"{each_link}/likes")

                    scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 2, 0.5)
                    information_list = browser.find_elements(By.XPATH,
                                                             '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
                    ph_list = []
                    for pn_item in information_list:
                        if len(pn_item.text) > 0:
                            ph_list.append(pn_item.text)
                    for pn_item in ph_list:
                        if not filter_no_like(pn_item):
                            item_list.append(pn_item)

                response_list.append(item_list)
            except NoSuchElementException:
                print("No Details")

        write_list_like(response_list, prefix)


def getLikeFromFile(prefix):
    filenameReader = input("Enter the filename .csv from contact list: ")
    if len(filenameReader) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)
        response_list = []

        for friend in myfriends:
            each_link = friend['profile']
            try:
                if "groups" not in each_link:
                    if "profile.php" in each_link:
                        browser.get(url=f"{each_link}&sk=likes")
                    else:
                        browser.get(url=f"{each_link}/likes")

                    scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 2, 0.5)
                    # scroll_to_bottom_two('div[class="xyamay9 x1pi30zi x1l90r2v x1swvt13"] > div[class="x78zum5 x1q0g3np x1a02dak"] > div', 1)
                    # information_list = browser.find_elements(By.XPATH, '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
                    information_list = browser.find_elements(By.CSS_SELECTOR,
                                                             'div[class="xyamay9 x1pi30zi x1l90r2v x1swvt13"] > div[class="x78zum5 x1q0g3np x1a02dak"] > div')
                    for pn_item in information_list:
                        item = pn_item.find_element(By.CSS_SELECTOR, 'div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]')
                        #print(item.text)
                        response_list.append(Like(friend['name'], item.text))

                # response_list.append(item_list)

            except NoSuchElementException:
                print("No Details")

        csvOut = prefix + "user_like_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Like'])

        for itemLike in response_list:
            print(itemLike)
            writer.writerow([itemLike.getName(), itemLike.getNameLink()])

        print("Successfully saved to %s" % csvOut)


def splitUsernameGroup(valueLink):
    username = ""
    if len(valueLink) > 0:
        if "profile.php" in valueLink:
            username = filter_string_two(r"[&]", valueLink)
        else:
            username = filter_string_two(r"[?]", valueLink)

    return username

def getLikeFromFileGroup(prefix):
    filenameReader = input("Enter the filename .csv from contact list: ")
    if len(filenameReader) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)
        response_list = []
        csvOut = prefix + "user_like_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['name', 'B_name','B_like'])

        try:
            for friend in myfriends:
                userProfile = getValidUserLink(friend['profile'])
                if len(userProfile) > 0:
                    if "profile.php" in userProfile:
                        browser.get(url=f"{userProfile}&sk=likes")
                    else:
                        browser.get(url=f"{userProfile}/likes")

                selectorPublisher = 'div[class="xyamay9 x1pi30zi x1l90r2v x1swvt13"] > div[class="x78zum5 x1q0g3np x1a02dak"] > div[class="x9f619 x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1n2onr6"] > div'
                scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 2, 0.5)
                numberPublisher = generate_numerator_css(selectorPublisher)
                if numberPublisher > 0:
                    if findElement(browser, selectorPublisher):
                        information_list = browser.find_elements(By.CSS_SELECTOR, selectorPublisher)
                        for pn_item in information_list:
                            selectorSpan = 'div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]'
                            valueSpan = ""
                            if findElement(pn_item, selectorSpan):
                                item = pn_item.find_element(By.CSS_SELECTOR, selectorSpan)
                                valueSpan = item.text
                            selectorLink = 'a[class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g xt0b8zv"]'
                            valueLink = ""
                            if findElement(pn_item, selectorLink):
                                item = pn_item.find_element(By.CSS_SELECTOR, selectorLink)
                                valueLink = item.get_attribute("href")

                            #print([friend['name'], valueSpan, valueLink])
                            writer.writerow([friend['name'], valueSpan, valueLink])

        except NoSuchElementException:
            print("No Details")


def getValidUserLink(each_link):
    partUsername = ""
    browser.get(url=f"{each_link}")
    selectorPublication = 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div div[class="x1cy8zhl x78zum5 x1q0g3np xod5an3 x1pi30zi x1swvt13 xz9dl7a"] > div[class="x1iyjqo2"] > div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"] > div';
    numberSelectorScroll = generate_numerator_css(selectorPublication)
    if numberSelectorScroll > 0 and numberSelectorScroll != 2:
        scroll_to_bottom_two(selectorPublication, 1)
    listPublication = browser.find_elements(By.CSS_SELECTOR, selectorPublication)
    selectorName = 'a[class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f"]'
    try:
        for publication in listPublication:
            if findElement(publication, selectorName):
                link = publication.find_element(By.CSS_SELECTOR, selectorName)
                if link.get_attribute("href") is not None:
                    valueLink = link.get_attribute("href")
                    partUsername = splitUsernameGroup(valueLink)
    except NoSuchElementException:
        sys.stdout.write("")

    return partUsername

def generate_user_like_1st(prefix):
    item_list = generate_like_1st()
    write_list_like(item_list, prefix)


def write_list_like(item_list, prefix):
    if len(item_list) > 0 and len(prefix) > 0:
        csvOut = prefix + "user_like_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', '[Like]'])
        for item in item_list:
            writer.writerow(item)

        print("Successfully saved to %s" % csvOut)


def generate_like_1st():
    response_list = []

    for friend in generate_friend_list_dictionary():
        each_link = friend['profile']
        item_list = []
        try:
            if "groups" not in each_link:
                if "profile.php" in each_link:
                    browser.get(url=f"{each_link}&sk=likes")
                else:
                    browser.get(url=f"{each_link}/likes")

                scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 2, 0.5)
                information_list = browser.find_elements(By.XPATH,
                                                         '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
                ph_list = []
                for pn_item in information_list:
                    if len(pn_item.text) > 0:
                        ph_list.append(pn_item.text)
                for pn_item in ph_list:
                    if not filter_no_like(pn_item):
                        item_list.append(pn_item)
            response_list.append(item_list)
        except NoSuchElementException:
            print("No Details")

    return response_list


def filter_no_like(string):
    flag = False
    day_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    for day in day_week:
        if day in string:
            flag = True

    return flag


def contain_key_dictionary(key, dictionary_array):
    flag = False
    for item in dictionary_array:
        if key in item:
            flag = True

    return flag


def get_value_dictionary(key, dictionary_array):
    response = ""
    for item in dictionary_array:
        if key in item:
            response = item[key]

    return response


def generate_basic_info(prefix):
    dictionary_list = generate_friend_list_dictionary()
    fb_numbers, fb_emails, fb_genders, fb_birth_dates, fb_birth_years, fb_languages = get_data_info()
    sleep(randint(4, 8))

    if len(dictionary_list) > 0 and len(prefix) > 0:
        csvOut = prefix + "basic_info_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Link', 'Mobile', 'Email', 'Gender', 'Birthday', 'Year', 'Language'])
        for dictionary in dictionary_list:
            username = dictionary['id']

            fb_name_i = dictionary['name']
            fb_link_i = dictionary['profile']
            fb_number_i = getValueFromArray(username, fb_numbers)
            fb_email_i = getValueFromArray(username, fb_emails)
            fb_gender_i = getValueFromArray(username, fb_genders)
            fb_birth_date_i = getValueFromArray(username, fb_birth_dates)
            fb_birth_year_i = getValueFromArray(username, fb_birth_years)
            fb_language_i = getValueFromArray(username, fb_languages)

            writer.writerow(
                [fb_name_i, fb_link_i, fb_number_i, fb_email_i, fb_gender_i, fb_birth_date_i, fb_birth_year_i,
                 fb_language_i])

        print("Successfully saved to %s" % csvOut)


def getValueFromArray(username, arrayValue):
    itemValue = ""
    if contain_key_dictionary(username, arrayValue):
        itemValue = get_value_dictionary(username, arrayValue)
    return itemValue


def getBasicInfoFromFile(prefix):
    dictionary_list = generate_friend_list_dictionary()
    fb_numbers, fb_emails, fb_genders, fb_birth_dates, fb_birth_years, fb_languages = get_data_info()
    sleep(randint(4, 8))

    if len(prefix) > 0:
        csvOut = prefix + "basic_info_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        # writer.writerow(['Name', 'Link', 'Mobile', 'Email', 'Gender', 'Birthday', 'Year', 'Language'])
        for dictionary in dictionary_list:
            username = dictionary['id']
            fb_number_i = ""
            fb_email_i = ""
            fb_gender_i = ""
            fb_birth_date_i = ""
            fb_birth_year_i = ""
            fb_language_i = ""

            fb_name_i = dictionary['name']
            fb_link_i = dictionary['profile']
            if contain_key_dictionary(username, fb_numbers):
                fb_number_i = get_value_dictionary(username, fb_numbers)
            if contain_key_dictionary(username, fb_emails):
                fb_email_i = get_value_dictionary(username, fb_emails)
            if contain_key_dictionary(username, fb_genders):
                fb_gender_i = get_value_dictionary(username, fb_genders)
            if contain_key_dictionary(username, fb_birth_dates):
                fb_birth_date_i = get_value_dictionary(username, fb_birth_dates)
            if contain_key_dictionary(username, fb_birth_years):
                fb_birth_year_i = get_value_dictionary(username, fb_birth_years)
            if contain_key_dictionary(username, fb_languages):
                fb_language_i = get_value_dictionary(username, fb_languages)

        print("Successfully saved to %s" % csvOut)


def scan_list_member():
    try:
        xpath_first_page_friend = '//span[@class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv ' \
                                  'xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen ' \
                                  'xk50ysn xzsf02u x1yc453h"]/span/span/a '
        list_friend = browser.find_elements(By.XPATH, xpath_first_page_friend)
        return list_friend
    except NoSuchElementException:
        print("The elements does not exist.")


def scan_list_member_follower(xpath_first_page_friend):
    try:
        list_friend = []
        if len(xpath_first_page_friend) > 0:
            list_friend = browser.find_elements(By.XPATH, xpath_first_page_friend)

        return list_friend
    except NoSuchElementException:
        print("The elements does not exist.")


def generate_group_member(prefix):
    filename = input("Enter the filename .csv from the contact group list: ")
    if len(filename) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filename)
        myfriends = load_csv(filename)
        print("------------------------------------------")
        # Prep CSV Output File
        csvOut = prefix + 'group_%s.csv' % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_group_name', 'B_member_name'])

        for idx, friend in enumerate(myfriends):

            scrape_url = "https://www.facebook.com/" + friend['uid'] + "members"
            browser.get(scrape_url)
            scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 1, 0.5)
            their_friends = scan_list_member()

            # Write friends to CSV File
            for person in their_friends:
                writer.writerow([friend['name'], person.text])

        print("Successfully saved to %s" % csvOut)

    else:
        print("Invalid filename .csv from the first contact list")

def getUsernameFromGroup(url_value):
    valueNumber = ""
    if len(url_value):
        valueUsername = filter_string(r"user{1}", url_value)
        valueNumber = valueUsername.replace("/", "")

    return valueNumber

def existItemProfileIntoArray(link, arrayMember):
    arrayFlag = []
    for item in arrayMember:
        #arrayFlag.append(item.verifySameProfile(link))
        arrayFlag.append(item == link)

    flag = True in arrayFlag

    return flag

def existItemProfileIntoArrayTwo(link, arrayMember):
    arrayFlag = []
    for item in arrayMember:
        arrayFlag.append(item.verifySameProfile(link))

    flag = True in arrayFlag

    return flag



def getMemberFromGroup(prefix):
    os.chdir("./doc")
    filename = input("Enter the filename .csv from the contact group list: ")
    if len(filename) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filename)
        myfriends = load_csv_two(filename)
        print("------------------------------------------")
        os.chdir("../")
        # Prep CSV Output File
        csvOut = prefix + 'group_%s.csv' % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_name', 'B_name', 'B_profile'])
        for idx, friend in enumerate(myfriends):

            scrape_url = "https://www.facebook.com/" + friend['username'] + "/members"
            browser.get(scrape_url)
            scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 1, 0.5)
            #scroll_to_bottom_two('div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w xx6bls6 x1jx94hy"] > div > div > div[class="html-div xe8uvvx x11i5rnm x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1oo3vh0 x1rdy4ex"] > div[data-visualcompletion="ignore-dynamic"]', 3)
            listMember = browser.find_elements(By.CSS_SELECTOR,
                                               'div[class="html-div xe8uvvx x11i5rnm x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1oo3vh0 x1rdy4ex"] > div[data-visualcompletion="ignore-dynamic"] > div[class="x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq"] > div[class="x6s0dn4 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r xeuugli x18d9i69 x1sxyh0 xurb0ha xexx8yu x1n2onr6 x1ja2u2z x1gg8mnh"] > div[class="x6s0dn4 xkh2ocl x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x18d9i69 x4uap5 xkhd6sd xexx8yu x1n2onr6 x1ja2u2z"] > div[class="x1qjc9v5 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x4uap5 xkhd6sd xz9dl7a xsag5q8 x1n2onr6 x1ja2u2z"]> div div[class="xu06os2 x1ok221b"]')

            # Write friends to CSV File
            arrayMember = []
            for item in listMember:
                selectorName = 'span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xk50ysn xzsf02u x1yc453h"]'
                if findElement(item, selectorName):
                    memberName = item.find_element(By.CSS_SELECTOR, selectorName)
                    selectorLink = 'span a[class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f"]'
                    memberProfile = memberName.find_element(By.CSS_SELECTOR, selectorLink)
                    link = getUsernameFromGroup(memberProfile.get_attribute("href"))
                    linkUrl = "https://www.facebook.com/" + link
                    if not existItemProfileIntoArray(link, arrayMember):
                        #arrayMember.append(Member(friend['name'], memberName.text, linkUrl))
                        arrayMember.append([friend['name'], memberName.text, linkUrl])

            for member in arrayMember:
                writer.writerow(member)

            arrayMember = []

        print("Successfully saved to %s" % csvOut)

    else:
        print("Invalid filename .csv from the first contact list")


def generate_follower(prefix):
    filename = input("Enter the filename .csv from the contact list: ")
    if len(filename) > 0 and len(prefix) > 0:
        print("Loading list from %s..." % filename)
        myfriends = load_csv(filename)

        # Prep CSV Output File
        csvOut = prefix + 'follower_%s.csv' % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_following_name', 'B_follower_name'])

        for friend in myfriends:

            if "profile.php" in friend['profile']:
                scrape_url = friend['profile'] + "&sk=followers"
            else:
                scrape_url = friend['profile'] + "/followers"

            browser.get(scrape_url)
            their_friends = scan_list_member_follower('//div[@class="x1iyjqo2 x1pi30zi"]/div[1]/a/span')

            # Write friends to CSV File
            for person in their_friends:
                writer.writerow([friend['name'], person.text])

        print("Successfully saved to %s" % csvOut)

    else:
        print("Invalid filename .csv from the first contact list")


def generate_following(prefix):
    try:
        profile_icon = browser.find_element(By.XPATH, '//div[@class="x1iyjqo2"]/ul/li/div/a')
        url_profile = profile_icon.get_attribute("href")
        unique_myid = get_profile_from_url(url_profile)

        if "profile" in url_profile:
            browser.get(url_profile + "&sk=following")
        else:
            browser.get(url_profile + "/following")

        # Prep CSV Output File
        csvOut = prefix + "following_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile'])

        following_list = browser.find_elements(By.XPATH, '//div[@class="x1iyjqo2 x1pi30zi"]/div[1]/a')
        for item in following_list:
            friend_url = item.get_attribute("href")
            friend_uid = get_profile_from_url(friend_url)
            writer.writerow([unique_myid, "Me", item.text, friend_uid, friend_url])

        print("Successfully saved to %s" % csvOut)
    except NoSuchElementException:
        print("No Details")


def findElementChild(item, selectorName, selectorOtherName):
    try:
        content = item.find_element(By.CSS_SELECTOR, selectorOtherName)
    except NoSuchElementException:
        content = item.find_element(By.CSS_SELECTOR, selectorName)

    return content


def findElement(item, selectorName):
    flag = False
    try:
        item.find_element(By.CSS_SELECTOR, selectorName)
        return not flag
    except NoSuchElementException:
        sys.stdout.write("")

    return flag

def existProperty(item, property):
    flag = False
    try:
        item.get_attribute(property)
        return not flag
    except Exception:
        sys.stdout.write("")

def existItemNameIntoArray(content, arrayPost):
    arrayFlag = []
    for post in arrayPost:
        arrayFlag.append(post.verifySameName(content))

    flag = True in arrayFlag

    return flag

def existItemNameIntoArrayTwo(content, arrayPost):
    arrayFlag = []
    for index in range(len(arrayPost)):
        arrayFlag.append(arrayPost[index] == content)

    flag = True in arrayFlag

    return flag



def generatePostFromList(prefix, numberIteration):
    os.chdir("./doc")
    filenameReader = input("Enter the filename .csv: ")
    if len(filenameReader) > 0 and len(prefix) > 0:

        csvOut = prefix + "user_publication_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Publication'])

        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)

        os.chdir("../")
        try:
            for friend in myfriends:
                each_link = friend['profile']

                if "groups" not in each_link:
                    if "profile.php" in each_link:
                        browser.get(url=f"{each_link}&v=timeline")
                    else:
                        browser.get(url=f"{each_link}?v=timeline")

                    posts = 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div'
                    counter = 0
                    arrayPublication = []
                    while counter <= int(numberIteration):
                        counter = counter + 1
                        scroll_to_bottom_two(posts, 3)

                        listPost = browser.find_elements(By.CSS_SELECTOR,
                                                         'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div')
                        for post in listPost:
                            content = getTextPublication(post)
                            if content is not None:
                                if not existItemNameIntoArray(content.text, arrayPublication):
                                    arrayPublication.append(Publication(friend['name'], content.text))

                    for publication in arrayPublication:
                        writer.writerow([publication])

                    arrayPublication = []
        except NoSuchElementException:
            sys.stdout.write("")

def getTextPublication(post):
    try:
        selectorName = 'blockquote[class="xckqwgs x26u7qi x7g060r x1gslohp x11i5rnm xieb3on x1pi30zi x1swvt13 x1d52u69"]'
        selectorOtherName = 'div[data-ad-comet-preview="message"]'
        selector = ''
        sleep(1)
        if findElement(post, selectorName):
            selector = selectorName
        if findElement(post, selectorOtherName):
            selector = selectorOtherName
        if len(selector) > 0:
            return post.find_element(By.CSS_SELECTOR, selector)

    except NoSuchElementException:
        sys.stdout.write("")

def generateListContactPublication(namePerson, arrayNameContact, arrayLinkContact, arrayPublication, publication):
    if len(arrayNameContact) > 0 and len(arrayLinkContact) > 0:
        for index in range(len(arrayNameContact)):
            publicationContact = PublicationContact(namePerson, publication, arrayNameContact[index], arrayLinkContact[index])
            arrayPublication.append(publicationContact)

def generateListContactPublicationTwo(arrayNameContact, arrayLinkContact, arrayContact, publication):
    arrayItem = [publication, "", ""]
    arrayContact.append(arrayItem)
    print(arrayItem)


def generateListContactPublicationThree(arrayNameContact, arrayLinkContact, arrayContact):

    if len(arrayNameContact) > 0 and len(arrayLinkContact) > 0:
        for index in range(len(arrayNameContact)):
            contact = Contact(arrayNameContact[index], arrayLinkContact[index])
            arrayContact.append(contact)
            #print(contact)


def getListContactPublication(prefix, numberIteration):
    filenameReader = input("Enter the filename .csv: ")
    os.chdir("./doc")
    if len(filenameReader) > 0 and len(prefix) > 0:

        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)
        os.chdir("../")

        for friend in myfriends:
            each_link = friend['profile']

            if "groups" not in each_link:
                if "profile.php" in each_link:
                    browser.get(url=f"{each_link}&v=timeline")
                else:
                    browser.get(url=f"{each_link}?v=timeline")

                posts = 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div'
                counter = 0

                csvOut = prefix + "user_publication_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
                writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
                writer.writerow(['B_name', 'B_profile'])

                while counter <= int(numberIteration):
                    counter = counter + 1
                    scroll_to_bottom_two(posts, 10)

                    listPost = browser.find_elements(By.CSS_SELECTOR, 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div > div[class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"] > div[class="x1n2onr6 x1ja2u2z"] > div div[class="x78zum5 xdt5ytf"] > div[class="x9f619 x1n2onr6 x1ja2u2z"] > div[class="x78zum5 x1n2onr6 xh8yej3"]')
                    #listPost = browser.find_elements(By.CSS_SELECTOR, 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div')
                    print(len(listPost))

                    selector = 'div div[class="x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz"]'
                    #selector = 'div[class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"] > div[class="x1n2onr6 x1ja2u2z"] > div div[class="x78zum5 xdt5ytf"] > div[class="x9f619 x1n2onr6 x1ja2u2z"] > div[class="x78zum5 x1n2onr6 xh8yej3"] > div div[class="x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x1q0g3np x87ps6o x1lku1pv x1a2a7pz"]'

                    selectorContact = 'span div[class="x1rg5ohu"]'
                    selectorContactLink = 'span div[class="x1rg5ohu"] a[class="x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f"]'

                    selectorCloseDiv = 'div[class="x1i10hfl x1ejq31n xd10rxx x1sy0etr x17r0tee x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x16tdsg8 x1hl2dhg xggy1nq x87ps6o x1lku1pv x1a2a7pz x6s0dn4 x14yjl9h xudhj91 x18nykt9 xww2gxu x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xl56j7k xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 xc9qbxq x14qfxbe x1qhmfi1"]'
                    arrayContact = []
                    try:
                        for post in listPost:

                            arrayLinkContact = []
                            arrayNameContact = []

                            openDivGetContact(arrayLinkContact, arrayNameContact, post, selector, selectorContact, selectorContactLink)

                            content = getTextPublication(post)

                            closeDivContact(selectorCloseDiv)


                            if content is not None:
                                #generateListContactPublicationTwo(arrayNameContact, arrayLinkContact, arrayContact, content.text)
                                generateListContactPublication(friend['name'], arrayNameContact, arrayLinkContact, arrayContact, content.text)

                            arrayLinkContact = []
                            arrayNameContact = []

                        for contactPublication in arrayContact:
                            #print(contactPublication)
                            writer.writerow([contactPublication.getNameAccount(), contactPublication.getPublication(), contactPublication.getNameContact(), contactPublication.getProfileContact()])

                        arrayContact = []
                        sleep(45)
                    except NoSuchElementException:
                        sys.stdout.write("")

def closeDivContact(selectorCloseDiv):
    if findElement(browser, selectorCloseDiv):
        closeDivLike(selectorCloseDiv)


def openDivGetContact(arrayLinkContact, arrayNameContact, post, selector, selectorContact, selectorContactLink):
    if findElement(post, selector):
        openDivLike(post, selector)

        getNameContactPublication(arrayNameContact, selectorContact)

        getLinkContactPublication(arrayLinkContact, selectorContactLink)

def searchAccountFromFile(prefix):
    filenameReader = input("Enter the filename .csv: ")
    if len(filenameReader) > 0:
        listFileRow = loadCustomCsv(filenameReader, "B_lastname", "B_second_lastname", "B_firstname", "B_middlename")

        try:
            csvOut = prefix + "found_user_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
            writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
            writer.writerow(['B_name', 'B_profile'])

            for fileRow in listFileRow:
                #print(fileRow)
                browser.get(url=f"https://www.facebook.com/search/top/?q={fileRow}")
                sleep(5)
                arrayPotentialContact = []
                selectorList = 'div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w xwib8y2 x1y1aw1k"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x1iyjqo2 x2lwn1j"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w"]'
                if findElement(browser, selectorList):
                    listPotentialContact = browser.find_elements(By.CSS_SELECTOR, selectorList)
                    selectorName = 'div span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"]'
                    selectorLink = 'div span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"] > div > a'
                    for potentialContact in listPotentialContact:
                        if findElement(potentialContact, selectorName):
                            nameContact = potentialContact.find_element(By.CSS_SELECTOR, selectorName)
                            urlLink = potentialContact.find_element(By.CSS_SELECTOR, selectorLink)
                            valueUrl = urlLink.get_attribute("href")
                            if "groups" not in valueUrl:
                                if not existItemNameIntoArray(valueUrl, arrayPotentialContact):
                                    #print(PotentialContactProfile(fileRow.toString(), valueUrl))
                                    arrayPotentialContact.append(PotentialContactProfile(nameContact.text, valueUrl))

                    for potentialContactProfile in arrayPotentialContact:
                        #print(potentialContactProfile)
                        writer.writerow([potentialContactProfile.getFullname(), potentialContactProfile.getProfile()])



        except NoSuchElementException:
            sys.stdout.write("")


def searchAccountFromFile(prefix):
    os.chdir("./doc")
    filenameReader = input("Enter the filename .csv: ")
    if len(filenameReader) > 0:
        listFileRow = loadCustomCsv(filenameReader, "B_lastname", "B_second_lastname", "B_firstname", "B_middlename")

        try:
            csvOut = prefix + "found_user_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
            writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
            writer.writerow(['B_name', 'B_profile'])

            for fileRow in listFileRow:
                #print(fileRow)
                browser.get(url=f"https://www.facebook.com/search/top/?q={fileRow}")
                sleep(5)
                arrayPotentialContact = []
                selectorList = 'div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w xwib8y2 x1y1aw1k"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x1iyjqo2 x2lwn1j"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w"]'
                if findElement(browser, selectorList):
                    listPotentialContact = browser.find_elements(By.CSS_SELECTOR, selectorList)
                    selectorName = 'div span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"]'
                    selectorLink = 'div span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"] > div > a'
                    for potentialContact in listPotentialContact:
                        if findElement(potentialContact, selectorName):
                            nameContact = potentialContact.find_element(By.CSS_SELECTOR, selectorName)
                            urlLink = potentialContact.find_element(By.CSS_SELECTOR, selectorLink)
                            valueUrl = urlLink.get_attribute("href")
                            if "groups" not in valueUrl:
                                if not existItemNameIntoArray(valueUrl, arrayPotentialContact):
                                    arrayPotentialContact.append(PotentialContactProfile(nameContact.text, valueUrl))

                    for potentialContactProfile in arrayPotentialContact:
                        writer.writerow([potentialContactProfile.getFullname(), potentialContactProfile.getProfile()])



        except NoSuchElementException:
            sys.stdout.write("")


def verifyExistWord(nameCountry, textSearch):
    responseFlag = False
    if len(nameCountry) > 0 and len(textSearch) > 0:
        if nameCountry in textSearch:
            responseFlag = True

    return responseFlag


def searchAccountFilter(prefix, numberIteration):
    os.chdir("./doc")
    filenameReader = input("Enter the filename .csv: ")
    if len(filenameReader) > 0:
        listFileRow = loadCustomCsv(filenameReader, "B_lastname", "B_second_lastname", "B_firstname", "B_middlename")

        try:
            os.chdir("../")
            csvOut = prefix + "found_user_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
            writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))

            for fileRow in listFileRow:
                print(fileRow)
                browser.get(url=f"https://www.facebook.com/search/people/?q={fileRow}")
                selectorTwo = 'div[class="x9f619 x193iq5w x1miatn0 xqmdsaz x1gan7if x1xfsgkm"] > div[class="x193iq5w x1xwk8fm"] > div[class="x1yztbdb"]'
                counter = 0

                selector = 'div[class="x9f619 x193iq5w x1miatn0 xqmdsaz x1gan7if x1xfsgkm"] > div[class="x193iq5w x1xwk8fm"] > div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w xz9dl7a"]'
                page = browser.find_elements(By.CSS_SELECTOR, selector)

                while counter < int(numberIteration) or counter < len(page):
                    counter = counter + 1
                    sizeSelectorTwo = generate_numerator_css(selectorTwo)
                    if sizeSelectorTwo > len(page) and len(page) == 0:
                        scroll_to_bottom_two(selectorTwo, 3)

                listItem = browser.find_elements(By.CSS_SELECTOR, selectorTwo)

                selectorItem = 'div[class="x78zum5 x1n2onr6 xh8yej3"] > div[class="x9f619 x1n2onr6 x1ja2u2z x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd xh8yej3 x6ikm8r x10wlt62 xquyuld"] > div > div[class="x1xmf6yo x1e56ztr"] > div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x1iyjqo2 x2lwn1j"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[data-visualcompletion="ignore-dynamic"] > div[class="x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq"] > div[class="x6s0dn4 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r xeuugli x18d9i69 x1sxyh0 xurb0ha xexx8yu x1n2onr6 x1ja2u2z x1gg8mnh"] > div[class="x6s0dn4 xkh2ocl x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x18d9i69 x4uap5 xkhd6sd xexx8yu x1n2onr6 x1ja2u2z"] > div[class="x1qjc9v5 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x4uap5 xkhd6sd xz9dl7a xsag5q8 x1n2onr6 x1ja2u2z"] > div > div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"] > div[class="xu06os2 x1ok221b"] > span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xo1l8bm xi81zsa x1yc453h"]'
                selectorNameContact = 'div[class="x78zum5 x1n2onr6 xh8yej3"] > div[class="x9f619 x1n2onr6 x1ja2u2z x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd xh8yej3 x6ikm8r x10wlt62 xquyuld"] > div > div[class="x1xmf6yo x1e56ztr"] > div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x1iyjqo2 x2lwn1j"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[data-visualcompletion="ignore-dynamic"] > div[class="x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq"] > div[class="x6s0dn4 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r xeuugli x18d9i69 x1sxyh0 xurb0ha xexx8yu x1n2onr6 x1ja2u2z x1gg8mnh"] > div[class="x6s0dn4 xkh2ocl x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x18d9i69 x4uap5 xkhd6sd xexx8yu x1n2onr6 x1ja2u2z"] > div[class="x1qjc9v5 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x4uap5 xkhd6sd xz9dl7a xsag5q8 x1n2onr6 x1ja2u2z"] > div > div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"] > div[class="xu06os2 x1ok221b"] > span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"]'
                selectorLinkContact = 'div[class="x78zum5 x1n2onr6 xh8yej3"] > div[class="x9f619 x1n2onr6 x1ja2u2z x1jx94hy x1qpq9i9 xdney7k xu5ydu1 xt3gfkd xh8yej3 x6ikm8r x10wlt62 xquyuld"] > div > div[class="x1xmf6yo x1e56ztr"] > div[class="x1n2onr6 x1ja2u2z x9f619 x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x1iyjqo2 x2lwn1j"] > div[class="x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w"] > div[data-visualcompletion="ignore-dynamic"] > div[class="x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq"] > div[class="x6s0dn4 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r xeuugli x18d9i69 x1sxyh0 xurb0ha xexx8yu x1n2onr6 x1ja2u2z x1gg8mnh"] > div[class="x6s0dn4 xkh2ocl x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1q0g3np x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x18d9i69 x4uap5 xkhd6sd xexx8yu x1n2onr6 x1ja2u2z"] > div[class="x1qjc9v5 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x4uap5 xkhd6sd xz9dl7a xsag5q8 x1n2onr6 x1ja2u2z"] > div > div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"] > div[class="xu06os2 x1ok221b"] > span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1tu3fi x41vudc x1lkfr7t x1lbecb7 xk50ysn xzsf02u x1yc453h"] > div a'

                #sleep(5)
                arrayPotentialContact = []
                arrayDuplicate = []
                for item in listItem:
                    if findElement(item, selectorItem):
                        country = item.find_element(By.CSS_SELECTOR, selectorItem)
                        if verifyExistWord("Uruguay", country.text):
                            nameContact = ""
                            if findElement(item, selectorNameContact):
                                nameContact = item.find_element(By.CSS_SELECTOR, selectorNameContact)
                                #print(nameContact.text)
                            valueLinkContact = ""
                            if findElement(item, selectorLinkContact):
                                linkContact = item.find_element(By.CSS_SELECTOR, selectorLinkContact)
                                valueLinkContact = linkContact.get_attribute("href")
                                #print(valueLinkContact)

                            if not existItemNameIntoArray(valueLinkContact, arrayDuplicate):
                                arrayDuplicate.append(PotentialContactProfile(nameContact.text, valueLinkContact))
                
                        if len(arrayDuplicate) > 0:
                            arrayPotentialContact.extend(arrayDuplicate)
                            arrayDuplicate = []

                for potentialContactProfile in arrayPotentialContact:
                    writer.writerow([potentialContactProfile.getFullname(), potentialContactProfile.getProfile()])
                    #print([potentialContactProfile.getFullname(), potentialContactProfile.getProfile()])

        except NoSuchElementException:
            sys.stdout.write("")


def closeDivLike(selectorCloseDiv):
    elementCloseDiv = browser.find_element(By.CSS_SELECTOR, selectorCloseDiv)
    ActionChains(browser).move_to_element(elementCloseDiv).perform()
    elementCloseDiv.click()


def openDivLike(post, selector):
    elementLike = post.find_element(By.CSS_SELECTOR, selector)
    ActionChains(browser).move_to_element(elementLike).perform()
    elementLike.click()

def getLinkContactPublication(arrayLinkContact, selectorContactLink):
    listContactList = browser.find_elements(By.CSS_SELECTOR, selectorContactLink)
    for contactLink in listContactList:
        valueContactLink = splitUsernameGroup(contactLink.get_attribute("href"))
        arrayLinkContact.append(valueContactLink)


def getNameContactPublication(arrayNameContact, selectorContact):
    listContact = browser.find_elements(By.CSS_SELECTOR, selectorContact)
    for contact in listContact:
        arrayNameContact.append(contact.text)


class PrintObject:
    def verifySameName(self, potencialName):
        pass


class Publication(PrintObject):

    def __init__(self, name, publicationName):
        self._name = name
        self._publicationName = publicationName

    def verifySameName(self, potencialName):
        return self._publicationName == potencialName

    def __str__(self):
        return self._name + ',' + self._publicationName


class Like:
    def __init__(self, name, nameLike):
        self._name = name
        self._nameLike = nameLike


    def getName(self):
        return self._name

    def getNameLink(self):
        return self._nameLike

    def __str__(self):
        return self._name + ',' + self._nameLike


class Member(PrintObject):

    def __init__(self, nameGroup, nameMember, profileLink):
        self._nameGroup = nameGroup
        self._nameMember = nameMember
        self._profileLink = profileLink

    def verifySameName(self, potencialName):
        return self._nameMember == potencialName

    def verifySameProfile(self, potencialProfile):
        return self._profileLink == potencialProfile

    def __str__(self):
        return f"{self._nameGroup},{self._nameMember},{self._profileLink}"

class PotentialContact:

    def __init__(self, lastname, secondLastname, firstname, middlename):
        self._lastname = lastname
        self._secondLastname = secondLastname
        self._firstname = firstname
        self._middlename = middlename

    def getLastname(self):
        return self._lastname

    def getSecondLastname(self):
        return self._secondLastname

    def getFirstname(self):
        return self._firstname

    def getMiddlename(self):
        return self._middlename

    def __str__(self):
        return self.toString()

    def toString(self):
        result = ""
        if len(self._middlename) > 0:
            result = self._lastname + ' ' + self._secondLastname + ' ' + self._firstname + ' ' + self._middlename
        else:
            result = self._lastname + ' ' + self._secondLastname + ' ' + self._firstname

        return result


class PotentialContactProfile(PrintObject):

    def __init__(self, fullname, profile):
        self._fullname = fullname
        self._profile = profile

    def getFullname(self):
        return self._fullname

    def getProfile(self):
        return self._profile

    def __str__(self):
        return self._fullname + ',' + self._profile

    def verifySameProfile(self, potentialProfile):
        return self._profile == potentialProfile

class Contact:

    def __init__(self, name, profile):
        self._name = name
        self._profile = profile

    def getName(self):
        return self._name

    def getProfile(self):
        return self._profile


    def __str__(self):
        return self._name + self._profile


class PublicationContact:

    def __init__(self, nameAccount, publication, nameContact, profileContact):
        self._nameAccount = nameAccount
        self._publication = publication
        self._nameContact = nameContact
        self._profileContact = profileContact

    def getNameAccount(self):
        return self._nameAccount

    def getPublication(self):
        return self._publication

    def getNameContact(self):
        return self._nameContact

    def getProfileContact(self):
        return self._profileContact

    #nameAccount, publication, nameContact, profileContact
    def __str__(self):
        return self._nameAccount + ',' + self._publication + ',' + self._nameAccount + ',' + self._profileContact

def write_list_post(item_list, prefix):
    if len(item_list) > 0 and len(prefix) > 0:
        csvOut = prefix + "user_post_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', '[Post]'])
        for item in item_list:
            writer.writerow(item)

        print("Successfully saved to %s" % csvOut)


# --------------- Start Scraping ---------------
configPath = "config.txt"
if configPath:
    configObj = configparser.ConfigParser()
    configObj.read(configPath)
    email = configObj.get('credentials', 'email')
    password = configObj.get('credentials', 'password')
else:
    print('Enter the config path')
fb_login(configObj)

item_option = input(
    "Enter number value 1 or 2 or 3 or 4 or 5 or 6 or 7 or 8 or 9 or 10 or 11 or 12 or 13 or 14 or 15 or 16 or 17 to "
    "generate list: ")

if item_option == "1":
    scrape_1st_degrees("1_1_")
    generate_basic_info("1_2_")
    generate_user_like_1st("1_3_")
elif item_option == "2":
    scrape_2nd_degrees("2_1_")
    generate_basic_info("2_2_")
elif item_option == "3":
    generate_user_like_from_list("2_3_")
elif item_option == "4":
    generate_group_member("3_1_")
elif item_option == "5":
    generate_follower("4_1_")
elif item_option == "6":
    generate_following("5_1_")
elif item_option == "7":
    generate_user_like_from_list("5_2_")
elif item_option == "8":
    generatePostFromList("6_1_", 10)
elif item_option == "9":
    generatePostFromList("7_1_", 5)
elif item_option == "10":
    getListFriendFromFile("8_1_")
elif item_option == "11":
    getDataInfoFromFile("11_1_")
elif item_option == "12":
    getLikeFromFile("12_1_")
elif item_option == "13":
    getMemberFromGroup("13_1_")
elif item_option == "14":
    #browser.implicitly_wait(20)
    getLikeFromFileGroup("14_1_")
elif item_option == "15":
    #browser.implicitly_wait(45)
    getListContactPublication("15_1_", 1)
elif item_option == "16":
    #browser.implicitly_wait(30)
    searchAccountFromFile("16_1_")
elif item_option == "17":
    #browser.implicitly_wait(25)
    searchAccountFilter("17_1_", 1)
else:
    print(
        "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the "
        "CSV file as the first argument.")
