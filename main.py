from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import sleep
from datetime import datetime
import urllib.parse
import pathlib
import mimetypes
import socket
import json


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        # data_parse = urllib.parse.unquote_plus(data.decode())
        # data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        simple_client("localhost", 5000, data)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def echo_server(host, port):
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        try:
            while True:
                s.listen(1)
                conn, addr = s.accept()
                print(f"Connected by {addr}")
                with open("storage/data.json", "r") as fh:
                    data_lst = json.load(fh)
                    if not data_lst:
                        data_lst = []
                with conn:
                    while True:
                        data = conn.recv(1024)
                        print(f'From client: {data}')
                        if not data:
                            break
                        data_parse = urllib.parse.unquote_plus(data.decode())
                        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        data_dict = {time:{key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}
                        data_lst.append(data_dict)
                with open("storage/data.json", "w") as fh:
                    json.dump(data_lst, fh)
        except KeyboardInterrupt:
            print(f'Destroy server')


def simple_client(host, port, message):
    with socket.socket() as s:
        while True:
            try:
                s.connect((host, port))
                s.sendall(message)
                break
            except ConnectionRefusedError:
                sleep(0.5)
        s.close()


if __name__ == '__main__':
    thread_http = Thread(target=run)
    thread_http.start()
    thread_echo = Thread(target=echo_server, args=("localhost", 5000))
    thread_echo.start()
    thread_http.join()
    thread_echo.join()
