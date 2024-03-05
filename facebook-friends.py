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

print("\n" * 100)

os.environ["DEBUSSY"] = "1"

# Configure browser session
wd_options = Options()
wd_options.add_argument("--disable-notifications")
wd_options.add_argument("--disable-infobars")
wd_options.add_argument("--mute-audio")
# wd_options.add_argument("--headless")
browser = webdriver.Chrome(options=wd_options)
#browser.implicitly_wait(10)


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
                        writer.writerow([friend['uid'], friend['name'], person['id'], person['name'], person['profile']])
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
                    #print([friend['name'], person['name'], person['profile']])
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
        #print([username, phoneNumber, email, gender, date, year, language, website])
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
            item_list = []
            try:
                if "groups" not in each_link:
                    if "profile.php" in each_link:
                        browser.get(url=f"{each_link}&sk=likes")
                    else:
                        browser.get(url=f"{each_link}/likes")

                    scroll_to_bottom('//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]', 2, 0.5)
                    #scroll_to_bottom_two('div[class="xyamay9 x1pi30zi x1l90r2v x1swvt13"] > div[class="x78zum5 x1q0g3np x1a02dak"] > div', 1)
                    #information_list = browser.find_elements(By.XPATH, '//div[@class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]/div[1]/span')
                    information_list = browser.find_elements(By.CSS_SELECTOR, 'div[class="xyamay9 x1pi30zi x1l90r2v x1swvt13"] > div[class="x78zum5 x1q0g3np x1a02dak"] > div')
                    print(len(information_list))
                    for pn_item in information_list:
                        item = pn_item.find_element(By.CSS_SELECTOR, 'div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]')
                        print(item.text)
                        response_list.append(Like(friend['name'], item.text))

                #response_list.append(item_list)

            except NoSuchElementException:
                print("No Details")

        csvOut = prefix + "user_like_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Like'])

        for itemLike in response_list:
            #print(itemLike)
            writer.writerow([itemLike])

        print("Successfully saved to %s" % csvOut)

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
        #writer.writerow(['Name', 'Link', 'Mobile', 'Email', 'Gender', 'Birthday', 'Year', 'Language'])
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


def filterPublication(content, arrayPost):
    arrayFlag = []
    for post in arrayPost:
        arrayFlag.append(post.verifySamePublication(content))

    flag = True in arrayFlag

    return flag


def generatePostFromList(prefix, numberIteration):
    filenameReader = input("Enter the filename .csv: ")
    if len(filenameReader) > 0 and len(prefix) > 0:

        csvOut = prefix + "user_publication_%s.csv" % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Publication'])

        print("Loading list from %s..." % filenameReader)
        myfriends = load_csv_two(filenameReader)

        for friend in myfriends:
            each_link = friend['profile']

            if "groups" not in each_link:
                if "profile.php" in each_link:
                    browser.get(url=f"{each_link}&v=timeline")
                else:
                    browser.get(url=f"{each_link}?v=timeline")

                posts = 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div'
                #posts = 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div > div[class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"] > div div[class="x1cy8zhl x78zum5 x1q0g3np xod5an3 x1pi30zi x1swvt13 xz9dl7a"]'
                counter = 0
                arrayPublication = []
                while counter <= int(numberIteration):
                    counter = counter + 1
                    scroll_to_bottom_two(posts, 3)

                    listPost = browser.find_elements(By.CSS_SELECTOR, 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div')
                    #listPost = browser.find_elements(By.CSS_SELECTOR, 'div[class="x9f619 x1n2onr6 x1ja2u2z xeuugli xs83m0k x1xmf6yo x1emribx x1e56ztr x1i64zmx xjl7jj x19h7ccj xu9j1y6 x7ep2pv"] > div:not(.x1yztbdb) > div > div[class="x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z"]')
                    for post in listPost:
                        selectorName = 'blockquote[class="xckqwgs x26u7qi x7g060r x1gslohp x11i5rnm xieb3on x1pi30zi x1swvt13 x1d52u69"]'
                        selectorOtherName = 'div[data-ad-comet-preview="message"]'
                        #selectorOtherName = 'span[class="x193iq5w xeuugli x13faqbe x1vvkbs x10flsy6 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x41vudc x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h"]'

                        selector = ''

                        if findElement(post, selectorName):
                            selector = selectorName
                        if findElement(post, selectorOtherName):
                            selector = selectorOtherName

                        if len(selector) > 0:
                            content = post.find_element(By.CSS_SELECTOR, selector)
                            if not filterPublication(content.text, arrayPublication):
                                arrayPublication.append(Publication(friend['name'], content.text))

                    #arrayFriend.append(arrayPublication)

                for publication in arrayPublication:
                    #print(publication, end="\n\n")
                    writer.writerow([publication])

                arrayPublication = []


class Publication:

    def __init__(self, name, publicationName):
        self._name = name
        self._publicationName = publicationName

    def verifySamePublication(self, potencialPublication):
        return self._publicationName == potencialPublication


    def __str__(self):
        return self._name + ',' + self._publicationName

class Like:
    def __init__(self, name, nameLike):
        self._name = name
        self._nameLike = nameLike

    def __str__(self):
        return self._name + ',' + self._nameLike

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

item_option = input("Enter number value 1 or 2 or 3 or 4 or 5 or 6 or 7 or 8 or 9 or 10 or 11 or 12 to generate list: ")


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
    generatePostFromList("7_1_", 20)
elif item_option == "10":
    getListFriendFromFile("8_1_")
elif item_option == "11":
    getDataInfoFromFile("11_1_")
elif item_option == "12":
    getLikeFromFile("12_1_")
else:
    print(
        "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the "
        "CSV file as the first argument.")
