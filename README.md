# Nintendo Game Scraper

## Introduction
This is my first webscraping project. The goal of it is to get data on games from the nintendo game store (nintendo.com/games). There is no comprehensive manipulatable database of switch games that I could find with reliable data. So I created my own.

## LinkScraper.py
This file runs through the game guide on nintendo's website (nintendo.com/games/game-guide) to index links to each specific video game. This must be run before GameScraper.py as it generates a csv that contains the links that the gamescraper file uses.

## ScrapeEveryLink.py
This file runs through all links provided by LinkScraper.py and parses the website to obtain data about each game. It collects everything from the name of the game, to its categories, to whether there is DLC. It outputs a CSV file encoded in UTF-8. Data is structured as a pandas dataframe.

## ScrapeNewLinks.py
This file checks the CSV file produced by ScrapeEveryLink.py and the CSV file with links produced by LinkScraper.py to find links that have not been parsed yet. It updates the csv file with data on games that have not been scraped yet.

## DataParser.py
This file is the backbones of the data scraper. It contains the functions that actually extract data from the webpage. Used in both the ScrapeEveryLink.py and ScrapeNewLinks.py 


## Example File of Scraped Data
https://docs.google.com/spreadsheets/d/1xLK53rug1qH0O4Iyxd8fHwWSwq-kDkPrGc6hQqraIWw/edit#gid=2075284628
