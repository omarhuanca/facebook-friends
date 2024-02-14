import os, time, csv, configparser, re
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
from time import sleep
from random import randint

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
                'active': 1
            })
        print('Found %r friends on page!' % len(friends))
    except NoSuchElementException:
        print("The element does not exist.")
    return friends

# --------------- Get list of all friends on page ---------------
def scan_friends(cleaned_all_names, cleaned_all_links):
    print('Scanning page for friends...')
    friends = []
    try:
        friends = generate_friend_list_dictionary()

        for friend in friends:
            cleaned_all_names.append(friend['name'])
            cleaned_all_links.append(friend['profile'])

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
def scrape_1st_degrees(fb_names, fb_links):
    # Prep CSV Output File
    csvOut = '1st_%s.csv' % now.strftime("%Y_%m_%d_%H%M")
    writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
    writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile', 'B_active'])

    # Get your unique Facebook ID
    profile_icon = browser.find_element(By.XPATH, "//div[@class='x1iyjqo2']/ul/li/div/a")
    url_content = profile_icon.get_attribute("href")
    unique_myid = get_profile_from_url(url_content)

    # Scan your Friends page (1st-degree friends)
    print("Opening Friends page...")
    browser.get("https://www.facebook.com/" + unique_myid + "/friends")
    scroll_to_bottom()
    myfriends = scan_friends(fb_names, fb_links)

    # Write friends to CSV File
    for friend in myfriends:
        writer.writerow([unique_myid, "Me", friend['id'], friend['name'], friend['profile'], friend['active']])

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
def scrape_2nd_degrees(fb_names, fb_links):
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
                writer.writerow(['A_id', 'A_name', 'B_id', 'B_name', 'B_profile','B_active'])

                # Load URL of friend's friend page
                scrape_url = "https://www.facebook.com/" + friend['uid'] + "/friends?source_ref=pb_friends_tl"
                browser.get(scrape_url)

                # Scan your friends' Friends page (2nd-degree friends)
                #print("%d) %s" % (idx + 1, scrape_url))
                print("name is found in your %d contact" % (idx + 1))
                scroll_to_bottom()
                their_friends = scan_friends(fb_names, fb_links)

                # Write friends to CSV File
                print('Writing friends to CSV...')
                for person in their_friends:
                    writer.writerow([friend['uid'], friend['name'], person['id'], person['name'], person['profile'], person['active']])
            else:
                print("name is not found in your %d contact" % (idx + 1))
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
            else:
                browser.get(url=f"{each_link}/about_contact_and_basic_info")

            sleep(randint(1, 3))
            information_list = browser.find_elements(By.XPATH, "//div[@class='x78zum5 xdt5ytf xz62fqu x16ldp7u']/div[1]/span")
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
        except NoSuchElementException:
            print("No Details")
            continue
    return all_friends_phone_number, all_friends_email, all_friends_gender, all_friends_date, all_friends_year, all_friends_language

def containkeyInDictionary(key, dictionary_array):
    flag = False
    for item in dictionary_array:
        if key in item:
            flag = True

    return flag

def getValueDictionary(key, dictionary_array):
    response = ""
    for item in dictionary_array:
        if key in item:
            response = item[key]

    return response


def generate_basic_info(item_array):
    dictionary_list = generate_friend_list_dictionary()
    fb_numbers, fb_emails, fb_genders, fb_birth_dates, fb_birth_years, fb_languages = get_data_info()
    sleep(randint(4, 8))

    if len(dictionary_list) > 0:
        csvOut = 'basic_info_%s.csv' % datetime.now().strftime("%Y_%m_%d_%H%M")
        writer = csv.writer(open(csvOut, 'w', encoding="utf-8"))
        writer.writerow(['Name', 'Link', 'Mobile', 'Email', 'Gender', 'Birthday', 'Year', 'Language'])
        for dictionary in dictionary_list:
            username = dictionary['id']
            fb_name_i = ""
            fb_link_i = ""
            fb_number_i = ""
            fb_email_i = ""
            fb_gender_i = ""
            fb_birth_date_i = ""
            fb_birth_year_i = ""
            fb_language_i = ""

            fb_name_i = dictionary['name']
            fb_link_i = dictionary['profile']
            if containkeyInDictionary(username, fb_numbers):
                fb_number_i = getValueDictionary(username, fb_numbers)
            if containkeyInDictionary(username, fb_emails):
                fb_email_i = getValueDictionary(username, fb_emails)
            if containkeyInDictionary(username, fb_genders):
                fb_gender_i = getValueDictionary(username, fb_genders)
            if containkeyInDictionary(username, fb_birth_dates):
                fb_birth_date_i = getValueDictionary(username, fb_birth_dates)
            if containkeyInDictionary(username, fb_birth_years):
                fb_birth_year_i = getValueDictionary(username, fb_birth_years)
            if containkeyInDictionary(username, fb_languages):
                fb_language_i = getValueDictionary(username, fb_languages)

            item_array.append([fb_name_i, fb_link_i, fb_number_i, fb_email_i, fb_gender_i, fb_birth_date_i, fb_birth_year_i,
                  fb_language_i])

            writer.writerow([fb_name_i, fb_link_i, fb_number_i, fb_email_i, fb_gender_i, fb_birth_date_i, fb_birth_year_i,
                  fb_language_i])


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

fb_names = []
fb_links = []

item_array = []

if item_option == "1":
    scrape_1st_degrees(fb_names, fb_links)
    generate_basic_info(item_array)
elif item_option == "2":
    scrape_2nd_degrees(fb_names, fb_links)
    generate_basic_info(item_array)
else:
    print(
        "Invalid # of arguments specified. Use none to scrape your 1st degree connections, or specify the name of the CSV file as the first argument.")
