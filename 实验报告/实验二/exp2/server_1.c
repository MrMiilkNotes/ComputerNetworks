#include <arpa/inet.h>
#include <error.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include "./SocketFunc.h"

#define PROTOCOL AF_INET  // IPv4
#define END_STR "bye"     // 结束消息
#define BACKLOG 1

int main(int argc, char *argv[]) {
  unsigned int port;
  int server_sock_listen, server_sock_data;
  struct sockaddr_in server_addr;
  char recv_msg[BUFSIZ], tmp;
  int i;
  unsigned int msg_len;

  /* 解析参数 */
  if (argc != 2) {
    printf("usage: server_1.exe <port>\n");
    exit(1);
  }
  port = atoi(argv[1]);

  /*
   *  创建socket
   *  socket初始化，错误处理封装在SocketFunc
   */
  server_sock_listen = Socket(PROTOCOL, SOCK_STREAM, 0);
  server_addr.sin_family = PROTOCOL;
  server_addr.sin_port = htons(port);
  server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
  memset(&server_addr.sin_zero, 0, sizeof(server_addr.sin_zero));
  Bind(server_sock_listen, (struct sockaddr *)&server_addr,
       sizeof(server_addr));
  // 端口复用
  int opt = 1;
  setsockopt(server_sock_listen, SOL_SOCKET, SO_REUSEADDR, (const void *)&opt,
             sizeof(opt));
  Listen(server_sock_listen, BACKLOG);

  /*
   *    服务器处理循环
   *    外层循环保证能接收多个客户端的连接
   *    内层循环处理一个客户端的多个请求
   */
  while (1) {
    server_sock_data = Accept(server_sock_listen, NULL, NULL);
    printf("new client connected\n");
    memset(recv_msg, 0, sizeof(recv_msg));  //接收数组置零
    while (recv(server_sock_data, recv_msg, sizeof(recv_msg), 0)) {
      printf("Recv: %s\n", recv_msg);
      /*
       *  处理消息, 若接收到bye或者ESC，则服务器主动关闭
       *  否则对字符串进行翻转
       */
      // if (strcmp(recv_msg, END_STR) == 0 ||
      //     (strlen(recv_msg) && recv_msg[0] == 27)) {
      //   print("closed by client\n");
      //   break;
      // }
      msg_len = strlen(recv_msg) - 1;
      for (i = msg_len / 2; i >= 0; --i) {
        tmp = recv_msg[i];
        recv_msg[i] = recv_msg[msg_len - i];
        recv_msg[msg_len - i] = tmp;
      }

      // 回送消息
      printf("Send: %s\n", recv_msg);
      send(server_sock_data, recv_msg, strlen(recv_msg), 0);
      memset(recv_msg, 0, sizeof(recv_msg));  //接收数组置零
    }

    close(server_sock_data);  // 关闭数据socket
  }

  close(server_sock_listen);  // 关闭监听socket

  return 0;
}
