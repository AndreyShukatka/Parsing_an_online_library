import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from http.server import HTTPServer, SimpleHTTPRequestHandler

path_file = os.path.join('library', 'books_pages.json')

def get_book_pages():
    with open(path_file, "r", encoding='utf-8') as books:
        books_pages = books.read()
    books = json.loads(books_pages)
    return books

env = Environment(
    loader=FileSystemLoader('library'),
    autoescape=select_autoescape(['html'])
)
template = env.get_template('template.html')
rendered_page = template.render(
    books = get_book_pages()
)
with open('index.html', 'w', encoding="utf8") as file:
    file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()