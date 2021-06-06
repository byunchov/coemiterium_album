#!/usr/bin/env python3

import socket

EXIT_MSG = b'#!:exit:'
ERROR_MSG = b'!#error:'

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 50555        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    records = []
    s.connect((HOST, PORT))
    query = input("Enter query> ")
    s.sendall(bytes(query, 'utf-8'))
    while True:
        data = s.recv(1024)
        if EXIT_MSG == data:
            print(data)
            break
        elif ERROR_MSG in data:
            print(data)
            break
        # records.append(data)
        print(data)
    s.close()

# print('Received', repr(content))

rows = []

for record in records:
    rows.append(record.decode('utf-8').split('|'))

print(rows)