import argparse
import os
import pathlib
from datetime import time

import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit


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


def request_tululu(url):
    response = requests.get(url)
    response.raise_for_status()
    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(book_url):
    response = request_tululu(book_url)
    soup = BeautifulSoup(response.text, 'lxml')
    name_book, book_author = soup.find('h1').text.split(sep='::')
    book_cover = soup.find('div', class_='bookimage').find('img')['src']
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genres.text for genres in soup.select('span.d_book a')]
    book_page = {
        'title': name_book,
        'author': book_author,
        'cover': book_cover,
        'comments': comments,
        'genres': genres
    }
    return book_page


def download_image(id, book_url):
    img_url = urljoin(url, parse_book_page(book_url)['cover'])
    name_img = sanitize_filename(parse_book_page(book_url)['title']).strip()
    folder_name = os.path.join(
        'img', f'{id}.{name_img}{extract_file_extension(img_url)}'
        )
    pathlib.Path('img').mkdir(
        parents=True,
        exist_ok=True
    )
    response = request_tululu(img_url)
    with open(folder_name, 'wb') as file:
        file.write(response.content)


def extract_file_extension(url):
    path, filename_tail = os.path.split(urlsplit(url).path)
    return os.path.splitext(filename_tail)[-1]


def download_txt(id, url):
    name_book = sanitize_filename(parse_book_page(book_url)['title']).strip()
    folder_name = os.path.join('books', f'{id}.{name_book}.txt')
    pathlib.Path('books').mkdir(
        parents=True,
        exist_ok=True
    )
    download_url = f'{url}txt.php?id={id}'
    response = request_tululu(download_url)
    with open(folder_name, 'wb') as file:
        file.write(response.content)


if __name__ == '__main__':
    url = 'https://tululu.org/'
    args = input_parsing_command_line()
    start_id = args.start_id
    end_id = args.end_id + 1
    for id in range(start_id, end_id):
        try:
            book_url = f'{url}b{id}/'
            response = request_tululu(book_url)
            check_for_redirect(response)
            download_image(id, book_url)
            download_txt(id, url)
            print('Название:', parse_book_page(book_url)['title'])
            print('Автор:', parse_book_page(book_url)['author'])
        except requests.HTTPError:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(10)
            continue
