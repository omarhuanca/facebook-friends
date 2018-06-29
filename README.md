# Facebook Friends Scraper
This script can scrape list of friends from a Facebook's profile in 1st degree connections and 2nd degree connections. 
It save a CSV file from the friends. It requires Python 3, <a href='http://selenium-python.readthedocs.io/installation.html'>Selenium Webdriver</a> and Chrome browser.

## Installation
You'll need to have python, pip, and [Google Chrome](https://www.google.com/chrome/) installed to use this tool. Once that's all set up:

1. Clone this repository
2. `cd` into the cloned folder 
3. `pip install -r requirements.txt`

## Set up its config.txt file
Fill your email and password of Facebook's profile.
```
[credentials]
email=foo@bar.com
password=secret
```

### 1st degree friend connections (your friends)
1. Run ```python facebook-friends.py```
2. It will open a browser window and will fill your username & password automatically.
3. You should see your Facebook friends page scroll to the bottom.
4. A CSV file will be created with the data (1st-degree_YYYY-MM-DD_HHMM.csv)

### 2st degree friend connections (your friend's friends)
Note: This could take days if you have lots of friends!

1. Get your 1st degree connections first, so you have the 1st-degree CSV file.
2. Put the 1st-degree CSV in the same folder as **python facebook-friends.py**
3. Run ```python facebook-connections.py 1st-degree_YYYY-MM-DD_HHMM.csv```, with the actual filename from the first step.
4. A browser window will open.
5. You should the script looping through your Facebook friend's friend pages.
6. A CSV file will be created with the data (2nd-degree_YYYY-MM-DD_HHMM.csv)
