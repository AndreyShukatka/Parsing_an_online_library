import requests
import os
import pathlib
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit


def request_tululu(url):
    response = requests.get(url)
    response.raise_for_status()
    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_a_book(book_url):
    response = request_tululu(book_url)
    soup = BeautifulSoup(response.text, 'lxml')
    name_book, book_author = soup.find('h1').text.split(sep='::')
    book_cover =soup.find('div', class_='bookimage').find('img')['src']
    all_comment = soup.find_all('div', class_='texts')
    for comment in all_comment:
        print(comment.find('span').text)
    return name_book, book_cover, all_comment


def download_image(id, book_url):
    img_url = urljoin(url, parse_a_book(book_url)[1])
    name_img = sanitize_filename(parse_a_book(book_url)[0]).strip()
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


def download_txt(url):
    for id in range(1,11):
        try:
            book_url = f'{url}b{id}/'
            response = request_tululu(book_url)
            check_for_redirect(response)
            download_image(id, book_url)
            name_book = sanitize_filename(parse_a_book(book_url)[0]).strip()
            print(name_book)
            parse_a_book(book_url)
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
    download_txt(url)
