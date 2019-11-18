#include <arpa/inet.h>
#include <error.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include "./SocketFunc.h"

#define PROTOCOL AF_INET
#define END_STR "bye"

/* 处理SIGCHLD */
void pr_exit(int status);
void sigchld_handler(int signo);

int main(int argc, char *argv[]) {
  unsigned int port;
  int server_sock_listen, server_sock_data;
  struct sockaddr_in server_addr;
  char recv_msg[BUFSIZ], tmp;
  int i;
  unsigned int msg_len;
  pid_t child_id;
  struct sigaction child_act;  //#define _XOPEN_SOURCE
  sigset_t sigchld_mask;

  /*
   * 使用sigaction注册SIGCHLD处理函数
   *  目的是获取结束的子进程的结束状态从而判断执行结果
   */
  sigemptyset(&sigchld_mask);
  child_act.sa_handler = sigchld_handler;
  child_act.sa_mask = sigchld_mask;
  child_act.sa_flags = 0;
  if (sigaction(SIGCHLD, &child_act, NULL) == -1) {
    err_sys("sigaction error");
    exit(1);
  }

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
  Listen(server_sock_listen, 0);

  /*
   *    服务器处理循环
   *    外层循环保证能接收多个客户端的连接
   *    内层循环处理一个客户端的多个请求
   */
  while (1) {
    server_sock_data = Accept(server_sock_listen, NULL, NULL);
    printf("new client connected\n");
    /* 接收并显示消息 */
    memset(recv_msg, 0, sizeof(recv_msg));

    /*
     * 使用fork产生子进程
     */
    if ((child_id = fork()) < 0) {
      printf("fork new process error\n");
      close(server_sock_data);
    } else if (child_id == 0) {
      // 子进程关闭server_sock_listen
      close(server_sock_listen);
    } else if (child_id > 0) {
      // 父进程关闭server_sock_data
      close(server_sock_data);
    }
    /*
     *   子进程和客户端进行交互
     *   任务结束后关闭连接然后子进程终止，调用exit(0);
     */
    if (child_id == 0) {
      while (recv(server_sock_data, recv_msg, sizeof(recv_msg), 0)) {
        printf("Recv: %s\n", recv_msg);

        /* 处理消息 */
        msg_len = strlen(recv_msg) - 1;
        for (i = msg_len / 2; i >= 0; --i) {
          tmp = recv_msg[i];
          recv_msg[i] = recv_msg[msg_len - i];
          recv_msg[msg_len - i] = tmp;
        }

        /* 发送消息 */
        printf("Send: %s\n", recv_msg);
        send(server_sock_data, recv_msg, strlen(recv_msg), 0);
        memset(recv_msg, 0, sizeof(recv_msg));  //接收数组置零
      }
      /* 关闭数据socket */
      close(server_sock_data);
      exit(0);
    }
  }

  /* 关闭监听socket */
  close(server_sock_listen);

  return 0;
}

void pr_exit(int status) {
  // 这个函数的编写来自APUE
  if (WIFEXITED(status)) {
    printf("normal termination, exit status: %d\n", WEXITSTATUS(status));
  } else if (WIFSIGNALED(status)) {
    printf("abnormal termation, signal number = %d\n", WTERMSIG(status));
  }
}

void sigchld_handler(int signo) {
  pid_t pid;
  int status;
  /*
   *   注意：这里使用while而非if
   *       当信号已经进入处理的时候，可能会有多个信号发生，由于是不可靠信号
   *       因此可能出现信号发生多次而只进入处理函数处理一次
   *       好在可以使用waitpid循环处理，从而避免僵尸进程
   */
  while ((pid = waitpid(0, &status, WNOHANG)) > 0) {
    pr_exit(status);
    sleep(2);
  }
}