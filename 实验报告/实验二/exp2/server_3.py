#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    实时聊天室，不需要记住用户
"""
import socket
import json
import copy
import threading

port = 8800

class Users:

    def __init__(self):
        self.clients = dict({})
        self.names = set({})

    def user(self, addr):
        if addr not in self.clients.keys():
            self.clients[addr] = dict({})
            return False
        return True
    
    def is_name_used(self, name):
        return name in self.names

    def regist(self, cli, name):
        if self.clients[cli]['name'] is None:
            self.clients[cli]['name'] = name
            self.names |= {name}
            return True
        return False

class UDPLink:
    BUFSIZ = 1024
    msg_ = {
        "welcome": "欢迎来到聊天室，退出请输入exit",
        "new_client": "---------- Welcome new client: {} ----------",
        "enter_username": "please spacefy a username:",
        "conflict_username": "conflict_username",
        "msg": "{}\t: {}"
    }
    def __init__(self, ip, port):
        self.server_socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))

    def send(self, to_, msg):
        self.server_socket.sendto(bytes(str(msg), encoding = 'utf8'), to_)

    def recv(self):
        data, addr =  self.server_socket.recvfrom(UDPLink.BUFSIZ)
        try:
            msg = json.loads(str(data, encoding = 'utf8').replace("\'", "\""))
        except Exception as e:
            print(e)
        return msg, addr

    def s_regist(self, addr):
        self.send(addr, UDPLink.msg_['conflict_username'])
    
    def boardcast(self, users, addr, msg):
        for addr_to in users.keys():
            if addr_to != addr:
                self.send(addr_to, msg)

    def new_msg(self, users, addr, msg):
        self.boardcast(users, addr, UDPLink.msg_['msg'].format(users[addr], msg))
    
    def welcome(self, users, addr):
        self.boardcast(users, addr, UDPLink.msg_['new_client'].format(users[addr]))
    
    def conform_link(self, addr):
        self.send(addr, 'hello')

    def conform_name(self, addr):
        self.send(addr, 'registed')


host = ''#socket.gethostname()
link = UDPLink(host, port)
users = Users()
if __name__ == "__main__":
    print('>' * 5 + " Server Info " + '<' * 5)
    print("IP: ", host)
    print("port: ", port)
    while True:
        msg, addr = link.recv()
        # 连接验证消息
        if msg['type'] == "t":
            print("conform msg from: ", addr)
            link.conform_link(addr)
            continue
        # 用户注册
        if (not msg['type'] == 'r' and not users.user(addr)) \
            or (msg['type'] == 'r' and users.is_name_used(msg['msg'])):
            # 不是注册信息且没有指定用户名或用户名已经被注册
            link.s_regist(addr) # 需要注册用户名
        else:
            # parse data
            link.conform_name(addr) # 确认用户名可用
            link.welcome(users.clients, addr)   # 广播新用户消息
