from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import re
import threading

#url = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_230_7&infinite=1"
numberOfLoads = 500
firstWrite = True
lock = threading.Lock()

def requestGetter(url: str):
    counter = 0
    while True:
        counter += 1
        try:
            if counter >= 20:
                print("Sir we are stuck in the getter request, url=\"" + url +"\"")
            return requests.get(url, timeout=0.5)
        except:
                counter = 0
                print('[' + str(threading.get_native_id()) + '] thread log: Request to: ' + url + ' failed, trying again')

def getSumOfAllResults(url: str):
    r = requestGetter(url)
    data = dict(r.json())
    total = data['total_count']
    return int(total)



def getHtmlData(url:str):
    r = requestGetter(url)
    data = dict(r.json())
    return data['results_html']



def parseReviews(reviewUnParsed: list) -> list:
    reviewInfo = []
    if not reviewUnParsed:
        return [0, 0]
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
    if reviewInfo[0] == 0:
        return 0
    return (
        100 * (
                int(reviewInfo[1].replace(r',', '')) + 1
                )) / int(reviewInfo[0])


def getGamesTags(url: str)->list:
    #print(url)
    page = requestGetter(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find_all('a', {'class': 'app_tag'})
    tags = [x.text.strip() for x in tags]
    if len(tags) == 0:
        tags = ['n/a','n/a','n/a']
    elif len(tags) == 1:
        tags = [tags[0],'n/a','n/a']
    elif len(tags) == 2:
        tags = [tags[0],tags[1],'n/a']
    return tags

def parse(data):
    gameslist = []
    reviewReg = re.compile('(\d*)%|([\d,]*) user reviews')
    
    soup = BeautifulSoup(data, 'html.parser')
    games = soup.find_all('a')
    for game in games:
        title = game.find('span', {'class': 'title'}).text
        prices = game.find('div', {'class': 'search_price'}).text.strip().split('zł')
        reviewHtml = game.find('span', {'class': 'search_review_summary'})

        reviewInfo = parseReviews(reviewReg.findall(str(reviewHtml)))
        price, discountPrice = parsePrice(prices)
        allReviews = getNumberOfAllReviews(reviewInfo)
        tags = getGamesTags(game['href'])

        #print(title, price, discountPrice, reviewInfo, prices, tags[0], tags[1], tags[2])
        mygame = {
            'title': title,
            'price': str(price).replace(r',', r'.'),
            'discountPrice': str(discountPrice).replace(r',', r'.'),
            'review': str(reviewInfo[0]),
            'numberOfPositiveReviews': str(reviewInfo[1]).replace(r',', ''),
            'numberOfAllReviews': int(allReviews + 1),
            'tag1': tags[0],
            'tag2': tags[1],
            'tag3': tags[2]
        }
        gameslist.append(mygame)
    return gameslist


def firsTimeOutput(results):
    gamesdf = pd.concat([pd.DataFrame(g) for g in results])
    gamesdf.to_csv('gamesInfo.csv', index=False)
    #print('Saved to CSV')
    return

def everyNextOutput(results):
    gamesdf = pd.concat([pd.DataFrame(g) for g in results])
    gamesdf.to_csv('gamesInfo.csv', header=False, index=False, mode='a')
    return


def writeToCsvNext50Games(x: int):
    results = []
    data = getHtmlData(
        f'https://store.steampowered.com/search/results/?query&start={x}&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_7000_7&filter=topsellers&tags=19&infinite=1')
    results.append(parse(data))
    with lock:
        everyNextOutput(results)
    results.clear()

def app():
    t = []
    results = []
    data = getHtmlData(
        f'https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_7000_7&filter=topsellers&tags=19&infinite=1')
    results.append(parse(data))
    firsTimeOutput(results)
    results.clear()


    print("\n\n\n CREATING THREADS\n\n\n\n")
    for i in range(1, numberOfLoads):
        t.append(threading.Thread(target=writeToCsvNext50Games, args=[i*50]))

    print("\n\n\n STARTING THREADS\n\n\n\n")
    for i in t:
        i.start()

    print("\n\n\n THREADS STARTED \n\n\n\n")

    for i in t:
        i.join()




if __name__ == '__main__':
    app()
