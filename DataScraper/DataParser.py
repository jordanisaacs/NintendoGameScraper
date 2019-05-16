from selenium import webdriver
import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from collections import defaultdict
import pandas as pd
from time import strftime, gmtime
import numpy as np
import re

# DataScraper.py is the backbones of the data scraping of games. It gets all of to populate the CSV file

# Set the requests session retries. Retries 10 times, waits 0.1 seconds after each try
s = requests.Session()
retries = Retry(total=10, backoff_factor=0.1,status_forcelist=[500, 502, 503, 504])
s.mount('https://', HTTPAdapter(max_retries=retries))

# Generate all of the game categories
def category_parser():
    # Get the page source for inital game-guide
    driver = webdriver.Chrome('chromedriver')
    start_url = 'https://www.nintendo.com/games/game-guide/'
    driver.get(start_url)
    page = driver.page_source
    driver.quit()
    # Parse the page source using BeautifulSoup
    category_tag = BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('input', {'data-filter-group':'categories'}))
    category_name_list = []
    for category in category_tag:
        category_name = category['data-filter-name']
        # Replace First Person category with First-Person
        if re.match('First Person', category_name):
            category_name = 'First-Person'
        category_name_list.append(category_name)
    # These categories are searchable in the game-guide so they are manually added in
    manual_categories = ['Multiplayer', 'Camera', 'Platformer', 'Fighting', 'Lifestyle', 'Undefined', 'Board Game', 'Arcade', 'Edutainment', 'Dance', 'Trivia', 'Shooter', 'Casual', 'Fishing Game', 'Interactive Theme Park', 'Creature Creator', 'Other', 'Communication', 'Hidden Object', 'Mental Training', 'Gambling']
    # Extend the auto generated category list with the manual categories
    category_name_list.extend(manual_categories)
    return category_name_list

def page_parser(url, category_name_list):
    # Request the page source and get the time the page is being requested
    time_data_retrieved = strftime('%Y-%m-%d %H:%M:%S', gmtime())
    print('Generating: ', url)
    game_data_dict = defaultdict(str)
    page = s.get(url)
    print('Parsing...')
    soup = BeautifulSoup(page.content, 'html.parser')

    #Set the store link & time data retrieved keys
    game_data_dict['Time Data Retrieved (UTC)'] = time_data_retrieved
    game_data_dict['Store Link'] = url

    #Find the name of the game being scraped, if unable to find set the key to ERROR
    title_container = soup.find(class_='title')
    if title_container is not None:
        title_tag = title_container.find('h1')
        if title_tag is not None:
            game_data_dict['Name'] = title_tag.text.strip()
        else:
            game_data_dict['Name'] = 'ERROR'
    else:
        game_data_dict['Name'] = 'ERROR'

    # Find the MSRP of the game, if can't find set to NaN
    msrp_container = soup.find(class_='msrp')
    if msrp_container is not None:
        game_data_dict['MSRP'] = msrp_container.text.strip()
    else:
        game_data_dict['MSRP'] = np.NaN

    #Sale price is commented out because it only works if javascript loads page
    #sale_price_container = soup.find(class_='sale-price')
    #if sale_price_container is not None:
    #    sale_price = sale_price_container.text.strip()
    #    if sale_price != '':
    #        game_data_dict['Sale Price'] = sale_price
    #
    #if 'Sale Price' not in game_data_dict:
    #    game_data_dict['Sale Price'] = np.NaN
    
    # Find the sale types available. If unable to find set them to nothing, otherwise set the value to true if it can be bought digitally, physically, or there is a demo
    sale_type_container = soup.find(id='purchase-options')
    if sale_type_container is None:
        game_data_dict['Buy Physical'] = np.NaN
        game_data_dict['Buy Digital'] = np.NaN
        game_data_dict['Demo Available'] = np.NaN
    else:
        sale_type_tags = sale_type_container.find_all(attrs={'title': True})
        if sale_type_tags is None:
            game_data_dict['Buy Physical'] = np.NaN
            game_data_dict['Buy Digital'] = np.NaN
            game_data_dict['Demo Available'] = np.NaN
        else:
            for sale_type in sale_type_tags:
                if sale_type['title'] == 'Buy digital' or sale_type['title'] == 'Google play badge' or sale_type['title'] == 'App store':
                    game_data_dict['Buy Digital'] = True
                elif sale_type['title'] == 'Buy physical':
                    game_data_dict['Buy Physical'] = True
                elif sale_type['title'] == 'Demo available':
                    game_data_dict['Demo Available'] = True
    if 'Buy Physical' not in game_data_dict:
        game_data_dict['Buy Physical'] = np.NaN
    if 'Buy Digital' not in game_data_dict:
        game_data_dict['Buy Digital'] = np.NaN
    if 'Demo Available' not in game_data_dict:
        game_data_dict['Demo Available'] = np.NaN

    # The data_container contains most of the important data. If unable to find the container, set all the keys found in this container to ERROR. Otherwise, set the key value if able to find. If unable to find key value to NaN
    # No matter what set the categories to NaN if the game does not fall into that category
    data_container = soup.find(class_='flex')
    if data_container is None:
        game_data_dict['ESRB'] = 'ERROR'
        game_data_dict['Release Date'] = 'ERROR'
        game_data_dict['Platform'] = 'ERROR'
        game_data_dict['No. of Players'] = 'ERROR'
        game_data_dict['Rom File Size'] = 'ERROR'
        game_data_dict['Publisher'] = 'ERROR'
        game_data_dict['Developer'] = 'ERROR'
        for category in category_name_list:
            game_data_dict[category] = np.NaN
    else:
        esrb_container = data_container.find('img')
        if esrb_container is not None:
            game_data_dict['ESRB'] = data_container.find('img')['alt']
        else:
            game_data_dict['ESRB'] = np.NaN
    
        platform_container = data_container.find(attrs={'itemprop': 'isRelatedTo'})
        if platform_container is not None:
            game_data_dict['Platform'] = platform_container.text.strip()
        else:
            game_data_dict['Platform'] = np.NaN
    
        release_date_container = data_container.find(attrs={'itemprop': 'releaseDate'})
        if release_date_container is not None:
            game_data_dict['Release Date'] = release_date_container.text.strip()
        else:
            game_data_dict['Release Date'] = np.NaN
    
        no_of_players_container = data_container.find(class_='num-of-players')
        if no_of_players_container is not None:
            game_data_dict['No. of Players'] = no_of_players_container.text.strip()
        else:
            game_data_dict['No. of Players'] = np.NaN
    
        rom_size_container = data_container.find(attrs={'itemprop': 'romSize'})
        if rom_size_container is not None:
            game_data_dict['Rom File Size'] = rom_size_container.text.strip()
        else:
            game_data_dict['Rom File Size'] = np.NaN
    
        publisher_container = data_container.find(attrs={'itemprop': 'brand'})
        if publisher_container is not None:
            game_data_dict['Publisher'] = publisher_container.text.strip()
        else:
            game_data_dict['Publisher'] = np.NaN
    
        developer_container = data_container.find(attrs={'itemprop': 'manufacturer'})
        if developer_container is not None:
            game_data_dict['Developer'] = developer_container.text.strip()
        else:
            game_data_dict['Developer'] = np.NaN
    
        category_container = str(data_container.find('dl'))
        for category_name in category_name_list:
            category_finder = re.search(category_name, category_container)
            if category_finder:
                game_data_dict[category_name] = True
            else:
                game_data_dict[category_name] = np.NaN

    # Find the game is part of switch online and what features it has. If unable to find the container then set all the values to NaN as it is not part of switch online
    switch_online_features_container = soup.find(class_='nso-support')
    if switch_online_features_container is not None:
        online_features_list = switch_online_features_container.find_all('a')
        for feature_tag in online_features_list:
            feature = feature_tag['title']
            if feature == 'online-play':
                game_data_dict['Switch Online Play'] = True
            elif feature == 'app':
                game_data_dict['Switch Online App'] = True
            elif feature == 'save-data-cloud':
                game_data_dict['Switch Online Save'] = True
    if 'Switch Online Play' not in game_data_dict:
        game_data_dict['Switch Online Play'] = np.NaN
    if 'Switch Online App' not in game_data_dict:
        game_data_dict['Switch Online App'] = np.NaN
    if 'Switch Online Save' not in game_data_dict:
        game_data_dict['Switch Online Save'] = np.NaN

    # Find whether there is DLC available. If unable to find set value to NaN and there is no dlc
    dlc_container = soup.find(class_='dlc-info')
    if dlc_container:
        game_data_dict['DLC Available'] = True
    else:
        game_data_dict['DLC Available'] = np.NaN

    # Find whether there is an official site. If there isn't set value to NaN and there is no official site
    official_site_tag = soup.find(class_='btn btn-white')
    if official_site_tag is not None:
        game_data_dict['Official Site'] = official_site_tag['href']
    else:
        game_data_dict['Official Site'] = np.NaN
    
    print('Parsing complete')
    return game_data_dict
