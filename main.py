import argparse
import requests
import os
import pathlib
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
    book_cover =soup.find('div', class_='bookimage').find('img')['src']
    all_comment = soup.find_all('div', class_='texts')
    book_ganres = soup.find_all('span', class_='d_book')
    return name_book, book_cover, all_comment, book_ganres


def download_image(id, book_url):
    img_url = urljoin(url, parse_book_page(book_url)[1])
    name_img = sanitize_filename(parse_book_page(book_url)[0]).strip()
    folder_name = os.path.join('img', f'{id}.{name_img}{extract_file_extension(img_url)}')
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


def search_comment(all_comment):
    for comment in all_comment:
        print(comment.find('span').text)


def search_genres(book_genres):
    bo_genres = []
    for genres in book_genres:
        genres = genres.find_all('a')
        for genre in genres:
            bo_genres.append(genre.text)
    return bo_genres


def download_txt(start_id, end_id, url):
    for id in range(start_id,end_id):
        try:
            book_url = f'{url}b{id}/'
            response = request_tululu(book_url)
            check_for_redirect(response)
            download_image(id, book_url)
            name_book = sanitize_filename(parse_book_page(book_url)[0]).strip()
            print('Заголовок:', name_book)
            book_genres = parse_book_page(book_url)[3]
            print(search_genres(book_genres))
            # all_comment = parse_a_book(book_url)[2]
            # search_comment(all_comment)
            folder_name = os.path.join('books',f'{id}.{name_book}.txt')
            pathlib.Path('books').mkdir(
                parents=True,
                exist_ok=True
            )
            download_url = f'{url}txt.php?id={id}'
            response = request_tululu(download_url)
            with open(folder_name, 'wb') as file:
                file.write(response.content)
        except requests.HTTPError:
            continue


if __name__ == '__main__':
    url = 'https://tululu.org/'
    args = input_parsing_command_line()
    start_id = args.start_id
    end_id = args.end_id + 1
    download_txt(start_id, end_id, url)
