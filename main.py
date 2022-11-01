from bs4 import BeautifulSoup as bs
import requests
import json
import pandas as pd

url = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&snr=1_7_7_230_7&infinite=1"


def app():
    soup = bs(html_doc, 'html.parser')


if __name__ == '__main__':
    app()

