#!/usr/bin/env python3.6
import socket
import struct

q2header = b'\xff\xff\xff\xff'
q2query = b'query\n\0a'
q2servers = b'servers '
HOST = '127.0.0.1'    # The remote host
PORT = 27900                     # The same port as used by the server

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(300)
    try:
        print(f"Connecting to {HOST}...")
        s.connect((HOST, PORT))
    except socket.error as msg:
        print("Connection error")
        print(msg)
    else:
        print(f"Query {q2query}...")
        s.send(q2query)
        data = s.recv(1024)
    finally:
        print("Closing.")
        s.close()

if data.startswith(q2header):
    print("Found q2header")
    data = data.replace(q2header, b'')
    if data.startswith(q2servers):
        print("Found q2header + q2servers")
        data = data.replace(q2servers, b'')
        for i in range(0, len(data), 6):
            address = data[i:i+6]
            ip = data[i:i+4]
            port = data[i+4:i+6]
            ip_string = '.'.join([str(_) for _ in ip])
            print(f"{ip_string}:{struct.unpack('!H', port)}")
