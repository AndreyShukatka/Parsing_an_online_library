import argparse
import os
import pathlib
import logging
from time import sleep
import json
from pprint import pformat

import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit
from parse_tululu_category import parse_category

def input_parsing_command_line():
    parser = argparse.ArgumentParser(
        description='Программа скачивает книги с сайта https://tululu.org/'
    )
    parser.add_argument(
        '--start_id',
        help='укажите id с которого нужно начать скачивать',
        default='1',
        type=int
    )
    parser.add_argument(
        '--end_id',
        help='укажите id до которого нужно начать скачивать',
        default='10',
        type=int
    )
    args = parser.parse_args()
    return args


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    book_name, book_author = soup.find('h1').text.split(sep='::')
    book_cover = soup.find('div', class_='bookimage').find('img')['src']
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genres.text for genres in soup.select('span.d_book a')]
    id = soup.find('div', class_="d_comm").find('input', type='hidden')['value']
    book_page = {
        'id': id,
        'title': book_name.strip(),
        'author': book_author.strip(),
        'img_src': os.path.join('img', extract_file_extension(book_cover)),
        'book_path': os.path.join('books', f'{book_name.strip()}.txt'),
        'cover':book_cover,
        'comments': comments,
        'genres': genres
    }
    return book_page


def download_image(url, book_page):
    img_url = urljoin(url, book_page['cover'])
    folder_name = os.path.join(
        'img', extract_file_extension(img_url)
        )
    pathlib.Path('img').mkdir(
        parents=True,
        exist_ok=True
    )
    response = requests.get(img_url)
    response.raise_for_status()
    with open(folder_name, 'wb') as file:
        file.write(response.content)


def extract_file_extension(url):
    path, filename_tail = os.path.split(urlsplit(url).path)
    return filename_tail


def download_txt(url, book_page):
    book_name = sanitize_filename(book_page['title']).strip()
    folder_name = os.path.join('books', f'{book_name}.txt')
    pathlib.Path('books').mkdir(
        parents=True,
        exist_ok=True
    )
    params = {
        'id': book_page['id']
    }
    download_url = f'{url}txt.php'
    response = requests.get(download_url, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    with open(folder_name, 'wb') as file:
        file.write(response.content)

def add_json(list):
    book_page_json = json.dumps(list, ensure_ascii=False)
    with open("books_pages.json", "a", encoding='utf8') as my_file:
        my_file.write(book_page_json)


if __name__ == '__main__':
    list =[]
    url = 'https://tululu.org/'
    args = input_parsing_command_line()
    start_id = args.start_id
    end_id = args.end_id + 1
    seconds = int(10)
    books_urls = parse_category(url)
    for book_url in books_urls:
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            check_for_redirect(response)
            book_page = parse_book_page(response)
            download_txt(url, book_page)
            download_image(url, book_page)
            book_page.pop('cover')
            book_page.pop('id')
            list.append(book_page)
        except requests.HTTPError:
            logging.warning(f'книги "{book_page["title"]}" нет на сервере')
            continue
        except requests.exceptions.ConnectionError:
            logging.warning('Нет соединения с сервером, повторная попытка через 10 секунд.')
            sleep(seconds)
            continue
    add_json(list)
    
