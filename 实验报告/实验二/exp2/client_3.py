#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import socket
import json
import random

port = 8800
ip = '127.0.0.1'
addr = (ip, port)

def new_msg(tp = 'b', msg = None):
    return {
        "type": tp,
        "msg": msg
    }
class UDPLink:
    BUFSIZ = 1024

    def __init__(self, ip, port):
        self.server = (ip, port)
        self.server_socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.bind(('', random.randint(32768, 65535)))

    def send(self, tp, msg):
        self.server_socket.sendto(bytes(str(new_msg(tp=tp, msg=msg)), encoding = 'utf8'), self.server)

    def recv(self):
        data, addr =  self.server_socket.recvfrom(UDPLink.BUFSIZ)
        msg = ''
        try:
            msg = str(data, encoding = 'utf8')# json.loads(str(data, encoding = 'utf8').replace("\'", "\""))
        except Exception as e:
            print(e)
        return msg, addr

    def regist(self, name):
        self.send('r', name)
        data, _ = self.recv()
        if data == 'registed':
            return True
        return False
    
    def boardcast(self, users, msg):
        pass
    
    def conform_link(self):
        self.send('t', 'hello')
        data, _ = self.recv()
        if data == 'hello':
            return True
        return False

if __name__ == '__main__':
    # client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 指定server的IP: port并验证
    while True:
        ip = input("请输入服务器的ip :")
        port = int(input("请输入服务器绑定的端口号 :"))
        link = UDPLink(ip, port)
        if not link.conform_link():
            print("IP: port出错，请检查")
        else: break
    print("----- 欢迎来到聊天室，退出请输入exit -----")
    # 进行注册
    name = input("输入你的用户名: ")
    while not link.regist(name):
        name = input("该昵称已被使用，请重新输入: ")
    # 进入聊天
    print("-" * 10 + name + '-' * 10)
    print("done")