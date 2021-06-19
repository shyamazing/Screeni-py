'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for handling networking for fetching stock codes and data
'''

import sys
import urllib.request
import csv
import requests
import random
import os
import yfinance as yf
import pandas as pd
from nsetools import Nse
from classes.ColorText import colorText
from classes.SuppressOutput import SuppressOutput

nse = Nse()

# Exception class if yfinance stock delisted


class StockDataEmptyException(Exception):
    pass

# This Class Handles Fetching of Stock Data over the internet


class tools:

    def __init__(self, configManager):
        self.configManager = configManager
        pass

    def fetchCodes(self, tickerOption):
        listStockCodes = []
        if tickerOption == 12:
            return list(nse.get_stock_codes(cached=False))[1:]
        tickerMapping = {
            1: "https://www1.nseindia.com/content/indices/ind_nifty50list.csv",
            2: "https://www1.nseindia.com/content/indices/ind_niftynext50list.csv",
            3: "https://www1.nseindia.com/content/indices/ind_nifty100list.csv",
            4: "https://www1.nseindia.com/content/indices/ind_nifty200list.csv",
            5: "https://www1.nseindia.com/content/indices/ind_nifty500list.csv",
            6: "https://www1.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
            7: "https://www1.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
            8: "https://www1.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
            9: "https://www1.nseindia.com/content/indices/ind_niftymidcap50list.csv",
            10: "https://www1.nseindia.com/content/indices/ind_niftymidcap100list.csv",
            11: "https://www1.nseindia.com/content/indices/ind_niftymidcap150list.csv"}

        url = tickerMapping.get(tickerOption)

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as res:
                lines = [l.decode('utf-8') for l in res.readlines()]
                cr = csv.reader(lines)
                next(cr)  # skipping first line
                for row in cr:
                    listStockCodes.append(row[2])
        except Exception as error:
            print(error)

        return listStockCodes

    # Fetch all stock codes from NSE
    def fetchStockCodes(self, tickerOption):
        listStockCodes = []
        if tickerOption == 0:
            stockCode = None
            while stockCode == None or stockCode == "":
                stockCode = str(input(colorText.BOLD + colorText.BLUE +
                                      "[+] Enter Stock Code(s) for screening (Multiple codes should be seperated by ,): ")).upper()
            stockCode = stockCode.replace(" ", "")
            listStockCodes = stockCode.split(',')
        else:
            print(colorText.BOLD +
                  "[+] Getting Stock Codes From NSE... ", end='')
            listStockCodes = self.fetchCodes(tickerOption)
            if len(listStockCodes) > 10:
                print(colorText.GREEN + ("=> Done! Fetched %d stock codes." %
                                         len(listStockCodes)) + colorText.END)
                if self.configManager.shuffleEnabled:
                    random.shuffle(listStockCodes)
                    print(colorText.BLUE +
                          "[+] Stock shuffling is active." + colorText.END)
                else:
                    print(colorText.FAIL +
                          "[+] Stock shuffling is inactive." + colorText.END)
                if self.configManager.stageTwo:
                    print(
                        colorText.BLUE + "[+] Screening only for the stocks in Stage-2! Edit User Config to change this." + colorText.END)
                else:
                    print(
                        colorText.FAIL + "[+] Screening only for the stocks in all Stages! Edit User Config to change this." + colorText.END)

            else:
                input(
                    colorText.FAIL + "=> Error getting stock codes from NSE! Press any key to exit!" + colorText.END)
                sys.exit("Exiting script..")

        return listStockCodes

    # Fetch stock price data from Yahoo finance
    def fetchStockData(self, stockCode, period, duration, proxyServer, screenResultsCounter, screenCounter, totalSymbols, printCounter=False):
        with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
            data = yf.download(
                tickers=stockCode+".NS",
                period=period,
                duration=duration,
                proxy=proxyServer,
                progress=False,
            )
        if printCounter:
            sys.stdout.write("\r\033[K")
            try:
                print(colorText.BOLD + colorText.GREEN + ("[%d%%] Screened %d, Found %d. Fetching data & Analyzing %s..." % (
                    int((screenCounter.value/totalSymbols)*100), screenCounter.value, screenResultsCounter.value, stockCode)) + colorText.END, end='')
            except ZeroDivisionError:
                pass
            if len(data) == 0:
                print(colorText.BOLD + colorText.FAIL +
                      "=> Failed to fetch!" + colorText.END, end='\r', flush=True)
                raise StockDataEmptyException
                return None
            print(colorText.BOLD + colorText.GREEN + "=> Done!" +
                  colorText.END, end='\r', flush=True)
        return data

    # Load stockCodes from the watchlist.xlsx
    def fetchWatchlist(self):
        createTemplate = False
        data = pd.DataFrame()
        try:
            data = pd.read_excel('watchlist.xlsx')
        except FileNotFoundError:
            print(colorText.BOLD + colorText.FAIL +
                  f'[+] watchlist.xlsx not found in f{os.getcwd()}' + colorText.END)
            createTemplate = True
        try:
            if not createTemplate:
                data = data['Stock Code'].values.tolist()
        except KeyError:
            print(colorText.BOLD + colorText.FAIL +
                  '[+] Bad Watchlist Format: First Column (A1) should have Header named "Stock Code"' + colorText.END)
            createTemplate = True
        if createTemplate:
            sample = {'Stock Code': ['SBIN', 'INFY', 'TATAMOTORS', 'ITC']}
            sample_data = pd.DataFrame(sample, columns=['Stock Code'])
            sample_data.to_excel('watchlist_template.xlsx',
                                 index=False, header=True)
            print(colorText.BOLD + colorText.BLUE +
                  f'[+] watchlist_template.xlsx created in {os.getcwd()} as a referance template.' + colorText.END)
            return None
        return data
