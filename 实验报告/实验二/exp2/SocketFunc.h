#ifndef SOCK_FUNC_H
#define SOCK_FUNC_H
#include<unistd.h>
#include<sys/types.h>
#include<sys/socket.h>
#include<arpa/inet.h>
#include <errno.h>
#include"../apue.h"
/*
 *  对socket连接需要的函数的简单封装
 *      对于出错，都是直接exit，对于其他函数，exit也是通常做法
 *      不过accept出错，如果对于多进程可以exit，但线程应该使用pthread_exit() TODO
 *      
 *      Note:   这里封装的函数大写首字母是因为在vim中可以用shift+k查看manpage(大小写不敏感)
*/

int Socket(int domain, int type, int protocol);

int Bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen);

int Listen(int sockfd, int backlog);

int Accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);

int Connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
#endif