import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pprint import pformat
import json


def parse_category(url):
    books_urls = []
    for id in range(1, 5):
        fantasy_url = f'{url}l55/{id}'
        response = requests.get(fantasy_url)
        soup = BeautifulSoup(response.text, 'lxml')
        all_books_urls = soup.select('.d_book')
        for book_url in all_books_urls:
            books_urls.append(urljoin(url, book_url.select_one('a')['href']))
    return books_urls
