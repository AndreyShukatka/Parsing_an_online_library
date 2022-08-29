import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
import pathlib
from more_itertools import chunked
from math import ceil

def get_book_pages(path_file):
    with open(path_file, "r", encoding='utf-8') as books:
        books_pages = books.read()
    books = json.loads(books_pages)
    number_pages = ceil(len(books)/20)
    print(number_pages)
    chunked_books = chunked(books, 20)
    return chunked_books, number_pages


def on_reload():
    chunked_books, number_pages = get_book_pages(path_file)
    for number, books in enumerate(chunked_books):
        env = Environment(
            loader=FileSystemLoader('template'),
            autoescape=select_autoescape(['html'])
        )
        template = env.get_template('template.html')
        print(number, number_pages)
        rendered_page = template.render(
            number_page=number,
            books=books,
            number_pages=number_pages
        )
        with open(os.path.join('pages',f'index{number+1}.html'), 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    path_file = os.path.join('library', 'books_pages.json')
    pathlib.Path('pages').mkdir(
        parents=True,
        exist_ok=True
    )
    on_reload()
    server = Server()
    server.watch('template/template.html', on_reload)
    server.serve(root='.')
