import random
import socket
import json
import time
import sched
import signal
from multiprocessing import Process, Queue,Value
from multiprocessing.managers import BaseManager
from copy import deepcopy

"""
两个类
    ShareManager    用于注册进程共享的类
    UDPLink         用于管理UDP连接，即server_link
                        提供send，recv等基本方法以及服务器ip,port设置的方法
"""
class ShareManager(BaseManager):
    pass

class UDPLink:
    BUFSIZ = 1024

    def __init__(self):
        self.server = None
        self.server_socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        self.server_socket.bind(('', random.randint(32768, 65535)))
        self.server_socket.settimeout(3)
    
    def set_server(self, ip, port):
        self.server = (ip, port)

    def send(self, msg):
        self.server_socket.sendto(msg, self.server)

    def recv(self):
        # data, addr
        return self.server_socket.recvfrom(self.BUFSIZ)

"""
    ShareManager    UDPLink注册到共享类中，实现进程间共享
"""
ShareManager.register('UDPLink', UDPLink)

""" 
工具类函数,包括了：
    初始化manger
    发送数据的编码和解码
    发送具体的消息，比如心跳包，注册用户名，发送消息等
"""
def init_manager():
    m = ShareManager()
    m.start()
    return m
def new_msg(tp = 'b', msg = None):
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
def conform_link(link):
    link.send(encode_data(new_msg('t', 'hello')))
    try:
        # signal.signal(signal.SIGALRM, handle)  # 设置信号和回调函数
        # signal.alarm(3)  # 设置 num 秒的闹钟
        msg, _ = link.recv()
    except socket.timeout as e:
        msg = None
    except Exception as e:
        print("客户端接收出错: ", e)
    if(msg is None): return False
    data = parse_recv_data(msg)
    if data["msg"] == 'hello':
        return True
    return False
def regist(link, name):
    link.send(encode_data(new_msg('r', name)))
    msg, _ = link.recv()
    data = parse_recv_data(msg)
    if data["msg"] == 'registed':
        return True
    return False
def chat(link, msg):
    link.send(encode_data(new_msg('b', msg)))
def leave(link):
    link.send(encode_data(new_msg('q', '')))
""" 
两个进程：
    recv_proc     负责接收消息
    heart_proc    发送心跳包，更新服务器是否存活的全局变量
"""
def recv_proc(link, you_there, live):
    while(live.value):
        try:
            msg, _ = link.recv()
        except socket.timeout as e:
            continue
        except Exception as e:
            print("客户端接收出错: ", e)
            continue
        data = parse_recv_data(msg)
        if data["type"] == "b":
            print(data["msg"])
        elif data["type"] == "h":
            you_there.value = True
        elif data["type"] == 'q':
            print(data["msg"])
def heart_proc(link, you_there, live):
    def try_conn():
        you_there.value = False
        link.send(encode_data(new_msg('h', '')))
        scheduler.enter(7, 0, try_recv)
    def try_recv(): #link, you_there, live, scheduler
        if you_there.value:
            scheduler.enter(7, 0, try_conn)
        else: 
            print("服务器掉线...")
            live.value = False
    scheduler = sched.scheduler(time.time,time.sleep)
    scheduler.enter(1, 0, try_recv)
    scheduler.run()

# >>>>>>>>> client <<<<<<<<<<
if __name__ == "__main__":
    # 共享对象 UDPlink
    s_manager = init_manager()
    link = s_manager.UDPLink()
    # 指定server的IP: port并验证
    while True:
        ip = input("请输入服务器的ip :")
        port = int(input("请输入服务器绑定的端口号 :"))
        link.set_server(ip, port)
        if not conform_link(link):
            print("IP: port出错，请检查")
        else: break
    live = Value('b', True)
    you_there = Value('b', True)
    print("----- 欢迎来到聊天室，退出请输入exit -----")
    # 进行注册
    name = input("输入你的用户名: ")
    while not regist(link, name):
        name = input("该昵称已被使用，请重新输入: ")
    # 开启两个进程
    heart_beat = Process(target=heart_proc, args=(link, you_there, live))
    receiver = Process(target=recv_proc, args=(link, you_there, live))
    print("-" * 20 + name + '-' * 20)
    receiver.start()
    heart_beat.start()
    # 进入聊天
    while live.value:   # 直到服务器短线或者主动关闭才退出
        text = input()
        if text == "exit" and live.value:
            leave(link)
            break
        chat(link, text)
    receiver.terminate()
    heart_beat.terminate()
    if not live.value:
        print("服务器断线")
    print("bye~")
