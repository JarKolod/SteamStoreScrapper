from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import time
import re
import csv

#url = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_230_7&infinite=1"
numberOfLoads = 100
firstWrite = True

def totalresults(url):
    r = requests.get(url, timeout=0.5)
    data = dict(r.json())
    totalresults = data['total_count']
    return int(totalresults)



def get_data(url):
    r = requests.get(url, timeout=0.5)
    data = dict(r.json())
    return data['results_html']



def parseReviews(reviewUnParsed: list) -> list:
    reviewInfo = []
    if not reviewUnParsed:
        return ['n/a', 'n/a']
    for pair in reviewUnParsed:
        for element in pair:
            if element:
                reviewInfo.append(element)
    return reviewInfo



def parsePrice(prices: list) -> tuple:
    price = prices[0]
    if not price:
        return -1,-1
    if price == 'Free to Play':
        return 0,0

    try:
        discountPrice = prices[1]
        if discountPrice == '':
            discountPrice = price
    except:
        discountPrice = price

    return price, discountPrice



def getNumberOfAllReviews(reviewInfo: list):
    if reviewInfo[0] == 'n/a':
        return 0
    return (
        100 * (
                int(reviewInfo[1].replace(r',', '')) + 1
                )) / int(reviewInfo[0])


def getGamesTags(url: str)->list:
    print(url)
    page = requests.get(url,timeout=0.5)
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find_all('a', {'class': 'app_tag'})
    return [x.text.strip() for x in tags]

def parse(data):
    gameslist = []
    reviewReg = re.compile('(\d*)%|([\d,]*) user reviews')
    
    soup = BeautifulSoup(data, 'html.parser')
    games = soup.find_all('a')
    for game in games:
        title = game.find('span', {'class': 'title'}).text
        prices = game.find('div', {'class': 'search_price'}).text.strip().split('zł')
        reviewHtml = game.find('span', {'class': 'search_review_summary'})

        isSuccess = False
        while not isSuccess:
            try:
                reviewInfo = parseReviews(reviewReg.findall(str(reviewHtml)))
                price, discountPrice = parsePrice(prices)
                allReviews = getNumberOfAllReviews(reviewInfo)
                tags = getGamesTags(game['href'])
                isSuccess = True
            except:
                print('Timed out connection, trying again')
            

        print(title, price, discountPrice, reviewInfo, prices, tags[0], tags[1], tags[2])
        mygame = {
            'title': title,
            'price': str(price).replace(r',', r'.'),
            'discountPrice': str(discountPrice).replace(r',', r'.'),
            'review': reviewInfo[0],
            'numberOfPositiveReviews': reviewInfo[1].replace(r',', ''),
            'numberOfAllReviews': int(allReviews),
            'tag1': tags[0],
            'tag2': tags[1],
            'tag3': tags[2]
        }
        gameslist.append(mygame)
    return gameslist


def output(results):
    global firstWrite
    gamesdf = pd.concat([pd.DataFrame(g) for g in results])
    if firstWrite:
        gamesdf.to_csv('gamesprices.csv', index=False)
        firstWrite = False
    else:
        gamesdf.to_csv('gamesprices.csv', header=False, index=False, mode='a')
    print('Saved to CSV')
    return



def app():
    results = []
    for x in range(0, numberOfLoads * 50, 50):
        data = get_data(
            f'https://store.steampowered.com/search/results/?query&start={x}&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_7000_7&filter=topsellers&tags=19&infinite=1')
        results.append(parse(data))
        output(results)
        results.clear()



if __name__ == '__main__':
    app()
