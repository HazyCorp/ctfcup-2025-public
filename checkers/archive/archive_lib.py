#!/usr/bin/env python3
import socket
import ssl
import random
import subprocess
import string
import base64
from typing import Optional

import gornilo

alph = string.ascii_letters + string.digits

valid_banner = b'===== Kek Archive ======\n1. Upload library\n2. Select library\n3. View book\n> '
valid_enter_library_name = b'[+] Enter library name: '
valid_enter_library_data = b'[?] Enter base64 encoded library data: '
valid_password_protection = b'[?] Do you want to protect this library with a password? (y/n): '
valid_enter_password = b'[?] Enter password for library: '
valid_library_protected = b'[+] Library will be password protected!\n'
valid_library_not_found = b'[-] Library not found!\n'
valid_enter_book_name = b'[+] Enter book name: '
valid_enter_password_protected = b'[+] This library is password protected!\n[?] Enter password: '
valid_password_verified = b'[+] Password verified!\n'
valid_incorrect_password = b'[-] Incorrect password!\n'
valid_no_such_book = b'[-] No such book!\n'

DEFAULT_RECV_SIZE = 4096
TCP_CONNECTION_TIMEOUT = 10
TCP_OPERATIONS_TIMEOUT = 10    

def generateFlagLibrary(libName: str, flag: str):
    bookAuthor = ''.join(random.choices(alph, k = random.randint(10, 32)))
    bookYear = random.randint(1700, 2025)

    inputData = libName + '\n'
    inputData += flag + ' ' + bookAuthor + ' ' + str(bookYear) + ' '
    inputData += 'exit\n'
    p = subprocess.Popen(["./libgen"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(input=inputData)

    p.terminate()

def generateLibrary(libName: str, booksCount: int):
    books = []
    inputData = libName + '\n'

    for _ in range(booksCount):
        bookTitle = ''.join(random.choices(alph, k = random.randint(4, 16)))
        bookAuthor = ''.join(random.choices(alph, k = random.randint(10, 32)))
        bookYear = random.randint(1700, 2025)

        books.append({
            'title': bookTitle,
            'author': bookAuthor,
            'year': bookYear,
        })
        inputData += bookTitle + ' ' + bookAuthor + ' ' + str(bookYear) + ' '

        if _ == booksCount - 1:
            inputData += 'exit\n'
        else:
            inputData += 'next\n'
    
    p = subprocess.Popen(["./libgen"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(input=inputData)

    p.terminate()
    return books

class ArchiveClient:
    def __init__(self, host, port):
        self.host_ = host
        self.port_ = port
    
    def connection(self):
        raw_sock = socket.socket()
        raw_sock.settimeout(TCP_CONNECTION_TIMEOUT)
        # Wrap socket in TLS for SNI-based routing through Envoy
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.sock = context.wrap_socket(raw_sock, server_hostname=self.host_)
        server = (self.host_, self.port_)
        self.sock.connect(server)
        self.sock.settimeout(TCP_OPERATIONS_TIMEOUT)
    
    def read_menu(self):
        data = self.recvuntil(b"> ")
        if valid_banner not in data:
            raise gornilo.Verdict.MUMBLE('Invalid service protocol')
        return data
    
    def sendline(self, data):
        return self.send(data + b'\n')
    
    def send(self, data):
        nbytes = self.sock.send(data)
        return nbytes
    
    def recv(self):
        data = self.sock.recv(DEFAULT_RECV_SIZE)
        return data

    def recvuntil(self, until_data):
        data = self.recv()
        while until_data not in data:
            t = self.recv()
            if t == b'':
                break
            data += t
        return data

    def recvline(self):
        data = self.sock.recv(1)
        while b'\n' not in data:
            t = self.sock.recv(1)
            if t == b'':
                break
            data += t
        return data

    # send generated lib_name, with password or not
    def upload_library(self, lib_name: str, protected: bool, password: str = '') -> None:
        self.sendline(b'1')
        data = self.recvuntil(b': ')

        # check service enter library name prompt
        if data != valid_enter_library_name:
            raise gornilo.Verdict.MUMBLE('Service enter library name prompt is not valid!')
        
        self.sendline(lib_name.encode())
        data = self.recvuntil(b': ')
        
        # check service enter library data prompt
        if data != valid_enter_library_data:
            raise gornilo.Verdict.MUMBLE('Service enter library data prompt is not valid!')

        library_data = open('/tmp/' + lib_name, 'rb').read()
        library_data = base64.b64encode(library_data)

        self.sendline(library_data)
        data = self.recvuntil(b': ')

        # check service password protection prompt
        if data != valid_password_protection:
            raise gornilo.Verdict.MUMBLE('Service password protection prompt is not valid!')

        if not protected:
            self.sendline(b'n')
            return

        self.sendline(b'y')
        data = self.recvuntil(b': ')

        # check service enter password prompt
        if data != valid_enter_password:
            raise gornilo.Verdict.MUMBLE('Service enter password prompt is not valid!')

        self.sendline(password.encode())
        data = self.recvline()

        # check service library protected prompt
        if data != valid_library_protected:
            raise gornilo.Verdict.MUMBLE('Service library protected prompt is not valid!')

    def select_library(self, lib_name: str, password: str = '') -> bytes:
        self.sendline(b'2')
        data = self.recvuntil(b': ')
        
        if data != valid_enter_library_name:
            raise gornilo.Verdict.MUMBLE('Service enter library name prompt is not valid!')

        self.sendline(lib_name.encode())

        if password != '':
            data = self.recvuntil(b": ")

            if data in valid_enter_password_protected:
                self.sendline(password.encode())
                return None
                
        return data
    
    def view_book(self, book_name: str) -> dict:
        self.sendline(b'3')
        data = self.recvuntil(b': ')

        if data != valid_enter_book_name:
            raise gornilo.Verdict.MUMBLE('Service enter book name prompt is not valid!')

        self.sendline(book_name.encode())
        data = self.recvline()
        
        if data == b"[-] No such book!\n":
            return {'title':'', 'author':'', 'year': 0}
        
        try:
            title, author, year = data.decode().split(', ')
            title = title.split(': ')[1]
            author = author.split(': ')[1]
            year = year.split(': ')[1].strip()
        except:
            return {'title':'', 'author':'', 'year': 0}
        
        return {'title':title, 'author':author, 'year': int(year)}
    
    def exit(self):
        self.sendline(b"4") # send invalid option
        self.sock.close()
        self.sock = None