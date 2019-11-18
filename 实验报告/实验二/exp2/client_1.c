#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <error.h>
#include <string.h>
#include "SocketFunc.h"

#define PROTOCOL AF_INET
#define END_STR "bye"

int main(int argc, char *argv[])
{
    unsigned int port;
    const char *ip;
	int client_sock;
	struct sockaddr_in server_addr;
	char send_msg[BUFSIZ];
	char recv_msg[255];

    /* 解析参数 */
    if(argc != 3) {
        printf("usage: client_1.exe <ip> <port>\n");
        exit(1);
    } 
    ip = argv[1];
    port = atoi(argv[2]);

	/* 创建socket */
	client_sock = Socket(PROTOCOL, SOCK_STREAM, 0);

	/* 指定服务器地址 */
	server_addr.sin_family = PROTOCOL;
	server_addr.sin_port = htons(port);
	inet_pton(PROTOCOL, ip, &(server_addr.sin_addr.s_addr));
	memset(server_addr.sin_zero, 0, sizeof(server_addr.sin_zero)); //零填充

	/* 连接服务器 */
	connect(client_sock, (struct sockaddr *)&server_addr, sizeof(server_addr));

    while(1) {
        /* 获取信息 */
        printf(">>> ");
        fgets(send_msg, BUFSIZ, stdin);
        send_msg[strlen(send_msg) - 1] = 0;

        /* 发送消息 */
        printf("Send: %s\n", send_msg);
        if(strcmp(send_msg, END_STR) == 0 || (strlen(send_msg) && send_msg[0] == 27)) {
            printf("Bye~\n");
            break;
        }
        if(send(client_sock, send_msg, strlen(send_msg), 0) != strlen(send_msg)) {
            printf("send error, lost server\n");
            break;
        }

        /* 接收并显示消息 */
        memset(recv_msg, 0, sizeof(recv_msg)); //接收数组置零
        recv(client_sock, recv_msg, sizeof(recv_msg), 0);
        printf("Recv: %s\n", recv_msg);
    }

	/* 关闭socket */
	close(client_sock);

	return 0;
}
