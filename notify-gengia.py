#!/usr/bin/python
import socket

'''
notify-gengia
Notifies the gengia background service via UDP to start listening for voice commands
'''

def send_command():
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    addr = ("127.0.0.1", 49173)
    msg = "start".encode()
    s.sendto(msg, addr)
    

if __name__ == "__main__":
    send_command()

