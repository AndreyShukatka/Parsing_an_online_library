import requests
import os
import pathlib
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def request_tululu(url):
    response = requests.get(url)
    response.raise_for_status()
    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def search_name_book(url):
    response = request_tululu(url)
    soup = BeautifulSoup(response.text, 'lxml')
    name_book, book_author = soup.find('h1').text.split(sep='::')
    return name_book



def download_txt(folder='books'):
    for id in range(1,11):
        try:
            book_url = f'https://tululu.org/b{id}/'
            response = request_tululu(book_url)
            check_for_redirect(response)
            name_book = sanitize_filename(search_name_book(book_url)).strip()
            folder_name = os.path.join(folder,f'{id}.{name_book}.txt')
            pathlib.Path(folder).mkdir(
                parents=True,
                exist_ok=True
            )
            download_url = f'https://tululu.org/txt.php?id={id}'
            response = request_tululu(download_url)
            with open(folder_name, 'wb') as file:
                file.write(response.content)
        except requests.HTTPError:
            continue


if __name__ == '__main__':
    download_txt()