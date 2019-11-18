import socket
import json
import time
import sched
from multiprocessing import Process, Queue
from multiprocessing.managers import BaseManager
from copy import deepcopy

"""
三个类
    ShareManager    用于注册进程共享的类
    Users           用于管理用户 用户数据包括地址和用户名
    UDPLink         用于管理UDP连接，即server_link
                        提供send，recv以及广播等基本方法
"""
class ShareManager(BaseManager):
    pass

class Users:

    def __init__(self):
        self.clients = dict({})
        self.names = set({})

    def user(self, addr):
        if addr not in self.clients.keys():
            self.clients[addr] = dict({})
            return False
        return self.clients[addr].get("name") is not None
    
    def is_name_used(self, name):
        return name in self.names

    def regist(self, cli, name):
        if self.clients[cli].get("name") is None:
            self.clients[cli]['name'] = name
            self.names |= {name}
            return True
        return False

    def name(self, addr):
        try:
            return self.clients.get(addr).get("name")
        except Exception as e:
            pass
        return None
    
    def leave(self,addr):
        self.clients.pop(addr)

    def get_users(self):
        return deepcopy(self.clients)

class UDPLink:
    BUFSIZ = 1024

    def __init__(self, ip, port):
        self.server_socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))
        self.server_socket.settimeout(3)

    def send(self, to_, msg):
        self.server_socket.sendto(msg, to_)

    def recv(self):
        # data, addr
        return self.server_socket.recvfrom(self.BUFSIZ)
    
    def boardcast(self, users, msg):
        for addr_to in users.keys():
            self.send(addr_to, msg)

"""
    ShareManager    Users和UDPLink注册到共享类中，实现进程间共享
    msg_            向客户端发送的几类消息
"""
ShareManager.register('Users', Users)
ShareManager.register('UDPLink', UDPLink)

msg_ = {
    "hello":"hello",
    "registed":"registed",
    "unregisted":"unregisted",
    "welcome": "    欢迎 {} 进入聊天室",
    "leave": "    {} 离开了聊天室",
    "msg": "{}\t: {}"
}

""" 
工具类函数,包括了：
    初始化manger
    发送数据的编码和解码
    发送具体的消息，比如心跳包，认证用户名，广播消息等
"""
def init_manager():
    m = ShareManager()
    m.start()
    return m
def new_msg(tp, msg = None):
    return {
        "type": tp,
        "msg": msg
    }
def parse_recv_data(data):
    msg = None
    try:
        msg = json.loads(str(data, encoding = 'utf8').replace("\'", "\""))
    except Exception as e:
        print(e)
    return msg
def encode_data(data):
    return bytes(str(data), encoding = 'utf8')
def conform_link(link, addr):
    print("[", time.asctime( time.localtime(time.time()) ), "]\t", "conform msg from: ", addr)
    link.send(addr, encode_data(new_msg('c', msg_['hello'])))
def conform_name(link, addr):
    link.send(addr, encode_data(new_msg('c', msg_['registed'])))
def heart_beat(link, addr):
    link.send(addr, encode_data(new_msg('h', '')))
def bad_name(link, addr):
    link.send(addr, encode_data(new_msg('c', msg_['unregisted'])))
def welcome_new(link, users, addr):
    name = users[addr]["name"]
    print("[", time.asctime( time.localtime(time.time()) ), "]\t", "新用户: ", name, "信息：", addr)
    users.pop(addr)
    link.boardcast(users, encode_data(new_msg('b', msg_["welcome"].format(name))))
def chat(link, users, addr, text):
    name = users[addr]["name"]
    users.pop(addr)
    link.boardcast(users, encode_data(new_msg('b', msg_["msg"].format(name, text))))
def goodbye(link, users, name):
    link.boardcast(users, encode_data(new_msg('q', msg_["leave"].format(name))))

""" 
四个进程：
    server_proc     只负责接收连接，将消息存到msg_queue
    deliver_proc    对消息解码，然后根据消息中的控制信息分发到verify_queue或chat_queue
    verify_proc     处理verify_queue中的消息，负责连接认证，用户注册，心跳包，用户离开等
    msg_proc        处理chat_queue中的消息，即对每个用户进行消息广播
"""
def server_proc(link, msg_queue):
    # 接受连接，放入处理队列
    while True:
        try:
            msg, addr = link.recv()
        except Exception as e:
            continue
        msg_queue.put((addr, msg))
def deliver_proc(users, msg_queue, verify_queue, chat_queue):
    # 从处理队列获取，分发消息
    while True:
        addr, msg = msg_queue.get()
        data = parse_recv_data(msg)
        if data is None:
            print("err, recv msg: ", msg)
            continue
        if users.user(addr):
            # 已经注册过
            if data["type"] == 'b':
                chat_queue.put((addr, data))
            elif data["type"] == 'h' or data["type"] == 'q':
                verify_queue.put((addr, data))
            else:
                print("todo")
        else:
            verify_queue.put((addr, data))
def verify_proc(users, link, verify_queue):
    while True:
        # 验证连接
        addr, data = verify_queue.get()
        if data['type'] == "t":
            conform_link(link, addr)
            continue
        # 心跳包
        if data['type'] == "h":
            heart_beat(link, addr)
        # 用户注册
        if (not data['type'] == 'r' and not users.user(addr)) \
            or (data['type'] == 'r' and users.is_name_used(data['msg'])):
            # 不是注册信息且没有指定用户名或用户名已经被注册
            # 需要注册用户名
            bad_name(link, addr)
        elif data['type'] == "r":
            users.regist(addr, data["msg"])
            conform_name(link, addr) # 确认用户名可用
            welcome_new(link, users.get_users(), addr)   # 广播新用户消息
        # 用户离开
        if data["type"] == 'q':
            name = users.name(addr)
            users.leave(addr)
            goodbye(link, users.get_users(), name)
def msg_proc(users, link, chat_queue):
    # 广播消息
    while True:
        addr, text = chat_queue.get()
        chat(link, users.get_users(), addr, text["msg"])

# Server
host = ''
port = 8800
if __name__ == "__main__":
    # 共享对象 Users UDPlink
    s_manager = init_manager()
    users = s_manager.Users()
    # server 设置
    port = int(input("输入要绑定的端口: "))
    link = s_manager.UDPLink(host, port)
    # 进程间消息队列
    msg_queue = Queue()
    verify_queue = Queue()
    chat_queue = Queue()

    # 启动所有进程
    Process(target=msg_proc, args=(users, link, chat_queue)).start()
    Process(target=deliver_proc, args=(users, msg_queue, verify_queue, chat_queue)).start()
    Process(target=verify_proc, args=(users, link, verify_queue)).start()
    server = Process(target=server_proc, args=(link, msg_queue))
    server.start()
    # 启动完成
    print(">"*6, " Server Launched ", "<"*6)
    server.join()