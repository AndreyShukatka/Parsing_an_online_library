import argparse
import os
import pathlib
import logging
from time import sleep
import json

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit


def input_parsing_command_line():
    parser = argparse.ArgumentParser(
        description='Программа скачивает книги с сайта https://tululu.org/'
    )
    parser.add_argument(
        '--start_page',
        help='укажите номер страницы с которой нужно начать скачивать',
        default=1,
        type=int
    )
    parser.add_argument(
        '--end_page',
        help='укажите номер старницы до которой нужно скачивать',
        default=701,
        type=int
    )
    parser.add_argument(
        '--dest_folder',
        default='library',
        help='Укажите папку для скачивания'
    )
    parser.add_argument(
        '--skip_imgs',
        help='Не скачивать картинки',
        action='store_true'
    )
    parser.add_argument(
        '--skip_txt',
        help='Не скачивать книгу',
        action='store_true'
    )
    parser.add_argument(
        '--json_path',
        help='укажите своё имя для *.json файла с результатами',
        default='books_pages'
    )
    args = parser.parse_args()
    return args


def parse_category(url, start_page, end_page):
    books_urls = []
    for id in range(start_page, end_page):
        fantasy_url = f'{url}l55/{id}'
        response = requests.get(fantasy_url)
        soup = BeautifulSoup(response.text, 'lxml')
        all_books_urls = soup.select('.d_book')
        for book_url in all_books_urls:
            books_urls.append(urljoin(url, book_url.select_one('a')['href']))
    return books_urls


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    book_name, book_author = soup.select_one('h1').text.split(sep='::')
    book_cover = soup.select_one('.bookimage img')['src']
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genres.text for genres in soup.select('span.d_book a')]
    id = soup.select_one('.r_comm input[name="bookid"]')['value']
    book_page = {
        'id': id,
        'title': book_name.strip(),
        'author': book_author.strip(),
        'img_src': os.path.join('img', extract_file_extension(book_cover)),
        'book_path': os.path.join('books', f'{book_name.strip()}.txt'),
        'cover': book_cover,
        'comments': comments,
        'genres': genres
    }
    return book_page


def download_image(url, book_page, folder):
    img_url = urljoin(url, book_page['cover'])
    folder_name = os.path.join(
        folder, 'img', extract_file_extension(img_url)
        )
    pathlib.Path(folder, 'img').mkdir(
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


def download_txt(url, book_page, folder):
    book_name = sanitize_filename(book_page['title']).strip()
    folder_name = os.path.join(folder, 'books', f'{book_name}.txt')
    pathlib.Path(folder, 'books').mkdir(
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


def add_json(list, json_folder, json_name):
    book_page_json = json.dumps(list, ensure_ascii=False)
    folder_name = os.path.join(json_folder, f"{json_name}.json")
    pathlib.Path(json_folder).mkdir(
        parents=True,
        exist_ok=True
    )
    with open(folder_name, "a", encoding='utf8') as my_file:
        my_file.write(book_page_json)


if __name__ == '__main__':
    list = []
    url = 'https://tululu.org/'
    args = input_parsing_command_line()
    start_page = args.start_page
    end_page = args.end_page
    folder = args.dest_folder
    json_name = args.json_path
    seconds = int(10)
    books_urls = parse_category(url, start_page, end_page)
    for book_url in books_urls:
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            book_page = parse_book_page(response)
            if not args.skip_txt:
                download_txt(url, book_page, folder)
            if not args.skip_imgs:
                download_image(url, book_page, folder)
            book_page.pop('cover')
            book_page.pop('id')
            list.append(book_page)
        except requests.HTTPError:
            logging.warning(f'книги "{book_page["title"]}" нет на сервере')
            continue
        except requests.exceptions.ConnectionError:
            logging.warning(
                'Нет соединения с сервером, повторная попытка через 10 секунд.'
            )
            sleep(seconds)
            continue
    add_json(list, folder, json_name)
