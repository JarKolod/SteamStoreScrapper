from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import time
import re

#url = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_230_7&infinite=1"


def totalresults(url):
    r = requests.get(url)
    data = dict(r.json())
    totalresults = data['total_count']
    return int(totalresults)



def get_data(url):
    r = requests.get(url)
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
        price = 'Free To Play'

    try:
        discprice = prices[2]
    except:
        discprice = price

    return price, discprice



def getNumberOfAllReviews(reviewInfo: list):
    if reviewInfo[0] == 'n/a':
        return 0
    return (
        100 * (
                int(reviewInfo[1].replace(r',', '')) + 1
                )) / int(reviewInfo[0])



def parse(data):
    gameslist = []
    soup = BeautifulSoup(data, 'html.parser')
    games = soup.find_all('a')
    reviewReg = re.compile('(\d*)%|([\d,]*) user reviews')
    for game in games:
        title = game.find('span', {'class': 'title'}).text
        prices = game.find('div', {'class': 'search_price'}).text.strip().split('zł')
        reviewHtml = game.find('span', {'class': 'search_review_summary'})

        reviewInfo = parseReviews(reviewReg.findall(str(reviewHtml)))
        price, discprice = parsePrice(prices)
        allReviews = getNumberOfAllReviews(reviewInfo)

        print(title, price, discprice, reviewInfo)
        mygame = {
            'title': title,
            'price': price.replace(r',', r'.'),
            'discprice': discprice.replace(r',', r'.'),
            'review': reviewInfo[0],
            'numberOfPositiveReviews': reviewInfo[1].replace(r',', ''),
            'numberOfAllReviews': int(allReviews)
        }
        gameslist.append(mygame)
    return gameslist



def output(results):
    gamesdf = pd.concat([pd.DataFrame(g) for g in results])
    gamesdf.to_csv('gamesprices.csv', index=False)
    print('Saved to CSV')
    # print(gamesdf.head())
    return



def app():
    results = []
    for x in range(0, 100, 50):
        data = get_data(
            f'https://store.steampowered.com/search/results/?query&start={x}&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_7000_7&filter=topsellers&tags=19&infinite=1')
        results.append(parse(data))
        output(results)



if __name__ == '__main__':
    app()
