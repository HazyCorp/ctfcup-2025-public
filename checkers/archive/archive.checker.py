#!/usr/bin/env python3
import sys
import os
import random
import traceback

from archive_lib import ArchiveClient, generateLibrary, generateFlagLibrary, alph

from gornilo import CheckRequest, Verdict, PutRequest, GetRequest, VulnChecker, NewChecker

checker = NewChecker()

def gen_random_password():
    return ''.join(random.choices(alph, k = random.randint(8, 32)))

def gen_random_library_name():
    return ''.join(random.choices(alph, k = random.randint(4, 16)))

class ErrorChecker:
    def __init__(self):
        self.verdict = Verdict.OK()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type in {Verdict}:
            self.verdict = exc_value
        elif exc_type in {TimeoutError, ConnectionError, ConnectionRefusedError}:
            self.verdict = Verdict.DOWN("Service is down")
        elif exc_type in {EOFError}:
            self.verdict = Verdict.MUMBLE("Got EOF in communication")
        
        if exc_type:
            print(exc_type)
            print(exc_value.__dict__)
            traceback.print_tb(exc_traceback, file=sys.stdout)

        return True

@checker.define_check
def check_service(request: CheckRequest) -> Verdict:
    with ErrorChecker() as ec:
        host, port = request.hostname.split(':')
        port = int(port, 10)
        cli = ArchiveClient(host, port)
        cli.connection()
        cli.read_menu()

        # create password protected lib and try to get book from it
        password_prot_lib_name = gen_random_library_name()
        password = gen_random_password()
        password_prot_books_cnt = random.randrange(1, 40)
        password_prot_books = generateLibrary(password_prot_lib_name, password_prot_books_cnt)

        cli.upload_library(password_prot_lib_name, True, password)
        cli.read_menu()

        try:
            os.remove(f"/tmp/{password_prot_lib_name}")
        except:
            pass

        cli.select_library(password_prot_lib_name, password)
        cli.read_menu()

        random_book = password_prot_books[random.randint(0, password_prot_books_cnt - 1)]
        book = cli.view_book(random_book['title'])
        cli.read_menu()

        if book != random_book:
            cli.exit()
            return Verdict.MUMBLE('Service book data is not valid!')

        # create unprotected lib and try to get book from it
        lib_name = gen_random_library_name()
        books_cnt = random.randrange(1, 40)
        books = generateLibrary(lib_name, books_cnt)

        cli.upload_library(lib_name, False)
        cli.read_menu()

        try:
            os.remove(f"/tmp/{lib_name}")
        except:
            pass

        cli.select_library(lib_name)
        cli.read_menu()

        random_book = books[random.randint(0, books_cnt - 1)]
        book = cli.view_book(random_book['title'])
        cli.read_menu()

        if book != random_book:
            cli.exit()
            return Verdict.MUMBLE('Service book data is not valid!')
        
        # select invalid book from lib
        invalid_book_name = gen_random_library_name()
        book = cli.view_book(invalid_book_name)
        cli.read_menu()

        if book['title'] != '' or book['author'] != '' or book['year'] != 0:
            cli.exit()
            return Verdict.MUMBLE('Service invalid book name check error!')

        cli.exit()
        ec.verdict = Verdict.OK('OK!')
            
    return ec.verdict

@checker.define_vuln("flag_id is an library name")
class ArchiveChecker(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        with ErrorChecker() as ec:
            host, port = request.hostname.split(':')
            port = int(port, 10)
            cli = ArchiveClient(host, port)
            cli.connection()
            cli.read_menu()
            
            _flag = request.flag
            flag_lib_name = gen_random_library_name()
            flag_lib_password = gen_random_password()

            generateFlagLibrary(flag_lib_name, _flag)
            cli.upload_library(flag_lib_name, True, flag_lib_password)
            cli.read_menu()

            # cleare file with flag
            try:
                os.remove(f"/tmp/{flag_lib_name}")
            except:
                pass

            cli.select_library(flag_lib_name, flag_lib_password)
            cli.read_menu()

            # check if flag is puted
            book = cli.view_book(_flag)
            if 'title' in book.keys():
                if book['title'] == _flag:
                    cli.exit()
                    return Verdict.OK_WITH_FLAG_ID(flag_lib_name, flag_lib_password)
                else:
                    ec.verdict = Verdict.MUMBLE("Can't put flag!")
            else:
                ec.verdict = Verdict.MUMBLE("Can't put flag!")

            cli.exit()

        return ec.verdict

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        with ErrorChecker() as ec:
            host, port = request.hostname.split(':')
            port = int(port, 10)
            cli = ArchiveClient(host, port)
            cli.connection()
            cli.read_menu()
            
            lib_name = request.public_flag_id
            lib_password = request.flag_id
            _flag = request.flag

            cli.select_library(lib_name, lib_password)
            cli.read_menu()

            book = cli.view_book(_flag)

            if 'title' in book.keys():
                if book['title'] == _flag:
                    cli.exit()
                    return Verdict.OK()
                else:
                    ec.verdict = Verdict.CORRUPT("Can't get flag!")
            else:
                ec.verdict = Verdict.CORRUPT("Can't get flag!")
            
            cli.exit()
        return ec.verdict

if __name__ == '__main__':
    checker.run()
