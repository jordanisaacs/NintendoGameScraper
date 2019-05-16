# Nintendo Game Scraper

## Introduction
This is my first webscraping project. The goal of it is to get data on games from the nintendo game store (nintendo.com/games). There is no comprehensive manipulatable database of switch games that I could find with reliable data. So I created my own.

## LinkScraper.py
This file runs through the game guide on nintendo's website (nintendo.com/games/game-guide) to index links to each specific video game. This must be run before GameScraper.py as it generates a csv that contains the links that the gamescraper file uses.

There is one function that should be run by the user:

init() --- will begin the process of generating the links.

## GameScraper.py
This file runs through the links provided by LinkScraper.py and parses the website to obtain data about each game. It collects everything from the name of the game, to its categories, to whether there is DLC.

There are two functions that can be run by the user:

new_link_data_scraper() --- This will scrape only links that have not been scraped before. Fast and doesn't refresh old data

entire_data_scraper() --- This will scrape every link regardless of whether it has already been scraped. Slow and refreshes old data
