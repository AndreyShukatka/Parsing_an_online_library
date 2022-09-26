import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
import pathlib
from more_itertools import chunked
from math import ceil


def get_book_pages(path_file):
    with open(path_file, "r", encoding='utf-8') as books:
        books=json.load(books)
    number_pages = ceil(len(books)/20)
    chunked_books = chunked(books, 20)
    return chunked_books, number_pages


def on_reload():
    chunked_books, pages_number = get_book_pages(path_file)
    env = Environment(
        loader=FileSystemLoader(''),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')
    for number, books in enumerate(chunked_books, start=1):
        rendered_page = template.render(
            page_number=number,
            books=books,
            pages_number=pages_number
        )
        with open(os.path.join(
                'pages', f'index{number}.html'
                ), 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    path_file = os.path.join('library', 'books_pages.json')
    pathlib.Path('pages').mkdir(
        parents=True,
        exist_ok=True
    )
    on_reload()
    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='', default_filename='index.html')
