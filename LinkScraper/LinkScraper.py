from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from collections import defaultdict
import pandas as pd
import time
import re

# LinkScraper portion of the NintendoWebScrape project
# This file has one function a user can run: init()
# init() will generate a list of nintendo.com/games/game-guide/ URLs with a variety of filters and sorts
# It will then run through each link, loading the webpage using selenium, until all game links have been obtained
# KEY NOTE: The switch game database on nintendo's website is off by 1 game. The game may or may not exist

# Call this to generate the game_links
def init():
    guide_link_list, guide_total_links, platform_list = guide_link_creator()
    game_link_dict = game_dict_generator(guide_link_list, guide_total_links, platform_list)
    game_link_df = pd.DataFrame.from_dict(game_link_dict, orient='index').transpose()
    game_link_df.to_csv('../game_links.csv', index=False)

# Generates the dictionary that contains all the game links for each platform
def game_dict_generator(guide_link_list, guide_num_links, platform_list):
    game_link_dict = defaultdict(list)
    # Iterate through all the game platforms
    for platform in range(len(platform_list)):
        platform_name = platform_list[platform]
        # Get the total number of game_links able to be found for each platform
        if platform == 'Nintendo Switch':
            total_game_links = int(guide_num_links[platform]) - 1
        else:
            total_game_links = int(guide_num_links[platform])
        # Iterate through each filter group (platform filter + 1 other filter)
        for platform_links in guide_link_list[platform]:
            # Iterate through each sort group (the filter link + one type of sort applied)
            for guide_link in platform_links:
                # Return the new game links and the total number of game links parsed
                game_link_extension, num_new_game_links = game_link_parser(guide_link, game_link_dict[platform_name])
                # Extend the existing dictionary with the new game links
                game_link_dict[platform_name].extend(game_link_extension)
                # The number of game links actually found
                total_game_links_found = len(game_link_dict[platform_name])
                print('Current platform link list length: ', total_game_links_found , 'out of ', guide_num_links[platform], 'games')
                print('\n')
                time.sleep(0.3)
                # If found every game for the platform OR there were less than 999 links found, break and move to next filter type -- Nintendo loads up to 999 or 1000 links per page, if less than that don't need to run through different sort types
                if total_game_links_found >= total_game_links:
                    break
                elif num_new_game_links < 999:
                    break
                else:
                    continue
            # Break the iteration of each filter group if found a game link for every game on the platform
            total_game_links_found = len(game_link_dict[platform_name])
            if total_game_links_found >= total_game_links:
                break
            else:
                continue
    # Return the dictionary of all the game links
    return game_link_dict

# Parse the game-guide link to get all the game links
def game_link_parser(guide_link, game_link_list):
    # Generate the website
    print('Generating: ', guide_link)
    page = generate_website(guide_link)
    content = BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('a'))
    num_all_links = len(content)
    print('Processing total links: ', num_all_links)
    # Parse only links with class=main-link (game links)
    game_link_content = content.find_all(class_='main-link')
    num_game_links = len(game_link_content)
    print('Processing game links: ', num_game_links)
    processed_link_list = []
    # Iterate through all the game links
    for link in game_link_content:
        raw_link = str.strip(str(link.get('href')))
        # Add the root of the link to the link
        process_link = 'https://www.nintendo.com' + raw_link
        # Check if the link is already indexed, if it has go to next iteration of loop, otherwise append link to the list
        if process_link in game_link_list or process_link in processed_link_list:
            continue
        else:
            processed_link_list.append(process_link)
    num_new_game_links = len(processed_link_list)
    print('Found: ', num_new_game_links)
    for game_link in processed_link_list:
        print(game_link)
    # Return the number of game links processed & the list of game links found
    return processed_link_list, num_game_links

# Generate and return a variety of game-guide links (with various filters, and sorts)
def guide_link_creator():
    # Get the page source for inital game-guide
    driver = webdriver.Chrome('chromedriver')
    start_url = 'https://www.nintendo.com/games/game-guide/'
    driver.get(start_url)
    page = driver.page_source
    driver.quit()
    # Parse the page source using BeautifulSoup
    soup = BeautifulSoup(page, 'html.parser')
    # Call total_links_parser which returns the number of total games available to index
    total_links = guide_total_links_parser(soup)
    # Call filter_parser which returns a dictionary of all filters, plus a list of each platform filter
    filter_dict, platform_list = guide_filter_parser(soup)
    # Call sort_parser which returns a list of each type of sort
    sort_list = guide_sort_parser(soup)
    # Call game_guide_link_list_generator which returns a list of game-guide urls with a variety of sort/filters applied
    link_list = guide_link_list_generator(filter_dict, platform_list, sort_list)
    return link_list, total_links, platform_list

# Find the number of game links available to index for each platform
def guide_total_links_parser(soup):
    total_links_soup = soup.find_all('label',attrs={'data-attribute':'platform'})
    total_links = []
    for platform in total_links_soup:
        num_links = platform.find('span').text
        total_links.append(num_links)
    return total_links

# Find the all the filters available
def guide_filter_parser(soup):
    filter_soup = soup.find_all('label',attrs={'data-attribute':True})
    filter_dict = defaultdict(list)
    platform_list = []
    # Iterate through each available filter
    for item in filter_soup:
        category_name = str(item['data-attribute'])
        label = str.strip(str(item.find(text=True)))
        # if the filter category is platform, it goes into the platform_list, otherwise it goes into the general filter list
        if category_name == 'platform':
            platform_list.append(label)
        else:
            # Do some general cleaning of the filters so they are compatible with being turned into a URL
            if re.search('\+', label):
                label = re.sub('\+', '%2B', label)
                filter_dict[category_name].append(label)
            elif re.search('\$', label):
                label = re.sub('\$', '%24', label)
                filter_dict[category_name].append(label)
            elif re.search('First-person action', label):
                label = re.sub('First-person action', 'First Person', label)
                filter_dict[category_name].append(label)
            else:
                filter_dict[category_name].append(label)
    return filter_dict, platform_list

# Get all the available sort options ex. A-Z, price descending, etc.
def guide_sort_parser(soup):
    sort_soup = soup.find('select', id="sort-by")
    tag_list = soup.find_all('option')
    sort_list = []
    for tag in tag_list:
        sort_name = tag['value']
        sort_list.append(sort_name)
    return sort_list

# Using all the sort, filter, and platform data parsed from the website, generate a list of game-guide links that can be used to obtain game links
def guide_link_list_generator(filter_dict,platform_list,sort_list):
    base_link = 'https://www.nintendo.com/games/game-guide/#filter/:q='
    link_list = []
    num_filter_categories = len(filter_dict.keys())
    index = 0
    subindex = 0
    # Create a list (each platform) within a list (each filter category) within a list (each sort type).
    # Start this list by just having it filtered by platform, not extra filter
    for platform in platform_list:
        link_list.append([])
        link_list[index].append([])
        platform_link = '&dFR[platform][0]=' + platform
        for sort in sort_list:
            sort_link = '&indexName=' + sort
            link = base_link + platform_link + sort_link
            link_list[index][subindex].append(link)
        index += 1
    index = 0
    subindex += 1

    # Append to the list a link for each platform, filter, and sort type
    for platform in platform_list:
        platform_link = '&dFR[platform][0]=' + platform
        for filter_category in filter_dict:
            for filter_name in filter_dict[filter_category]:
                filter_link = '&dFR[' + filter_category + '][0]=' + filter_name
                link_list[index].append([])
                for sort in sort_list:
                    sort_link = '&indexName=' + sort
                    link = base_link + platform_link + filter_link + sort_link
                    link_list[index][subindex].append(link)
                subindex += 1
        index += 1
        subindex = 1
    return link_list

# Generate the website for obtaining game links, return the page_source
def generate_website(link):
    driver = webdriver.Chrome('chromedriver')
    driver.get(link)
    time.sleep(2)
    # Call the load_more function
    load_more(driver)
    page = driver.page_source
    driver.quit()
    return page

# Presses the load more button until all possible game links are loaded onto the screen
def load_more(driver):
    while True:
        try:
            wait_button = WebDriverWait(driver, 2)
            button = wait_button.until(EC.element_to_be_clickable((By.ID, 'btn-load-more')))
            button.click()
            wait_visible = WebDriverWait(driver, 3)
            wait_visible.until(EC.invisibility_of_element((By.ID, 'loader-container')))
            time.sleep(0.1)
        except Exception as e:
            break

init()