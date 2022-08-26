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
    for book_number in range(start_page, end_page):
        try:
            fantasy_url = f'{url}l55/{book_number}'
            response = requests.get(fantasy_url)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            all_books_urls = soup.select('.d_book')
            for book_url in all_books_urls:
                books_urls.append(urljoin(
                    fantasy_url, book_url.select_one('a')['href']
                ))
        except requests.HTTPError:
            logging.warning(f'книги  с ID "{book_number}" нет на сервере')
            continue
        except requests.exceptions.ConnectionError:
            logging.warning(
                'Нет соединения с сервером, повторная попытка через 10 секунд.'
            )
            sleep(seconds)
            continue
    return books_urls


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    book_name, book_author = soup.select_one('h1').text.split(sep='::')
    book_cover = urljoin(
        response.url, soup.select_one('.bookimage img')['src']
    )
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genres.text for genres in soup.select('span.d_book a')]
    book_number = soup.select_one('.r_comm input[name="bookid"]')['value']
    book_page = {
        'id': book_number,
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
    img_url = book_page['cover']
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


def write_json_file(books_json, json_folder, json_name):
    folder_name = os.path.join(json_folder, f"{json_name}.json")
    pathlib.Path(json_folder).mkdir(
        parents=True,
        exist_ok=True
    )
    with open(folder_name, "a", encoding='utf8') as file:
        json.dump(books_json, file, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    books_info = []
    url = 'https://tululu.org/'
    args = input_parsing_command_line()
    start_page = args.start_page
    end_page = args.end_page
    folder = args.dest_folder
    json_name = args.json_path
    seconds = 10
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
            books_info.append(book_page)
        except requests.HTTPError:
            logging.warning(f'книги "{book_page["title"]}" нет на сервере')
            continue
        except requests.exceptions.ConnectionError:
            logging.warning(
                'Нет соединения с сервером, повторная попытка через 10 секунд.'
            )
            sleep(seconds)
            continue
    write_json_file(books_info, folder, json_name)
