import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def get_book_pages(path_file):
    with open(path_file, "r", encoding='utf-8') as books:
        books_pages = books.read()
    books = json.loads(books_pages)
    return books


def on_reload():
    env = Environment(
        loader=FileSystemLoader('template'),
        autoescape=select_autoescape(['html'])
    )
    template = env.get_template('template.html')
    rendered_page = template.render(
        books=get_book_pages(path_file)
    )
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)
    print('asdasdasda')


if __name__ == '__main__':
    path_file = os.path.join('library', 'books_pages.json')
    on_reload()
    server = Server()
    server.watch('template/template.html', on_reload)
    server.serve(root='.')
    
