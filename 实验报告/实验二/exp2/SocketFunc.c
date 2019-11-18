#include"./SocketFunc.h"

int Socket(int domain, int type, int protocol) {
    int ret;
    if((ret = socket(domain, type, protocol)) == -1) {
        err_sys("socket error");
        exit(1);
    }
    return ret;
}

int Bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    int ret;
    if((ret = bind(sockfd, addr, addrlen)) == -1) {
        err_sys("bind error");
        exit(1);
    }
    return ret;
}

int Listen(int sockfd, int backlog) {
    int ret;
    if((ret = listen(sockfd, backlog)) == -1) {
        err_sys("listen error");
        exit(1);
    }
    return ret;
}

int Accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    int ret;
again:
    if((ret = accept(sockfd, addr, addrlen)) < 0) {
        if ((errno == ECONNABORTED) || (errno == EINTR)) {
            goto again;
        }
        err_sys("accept error");
        exit(1);
    }
    return ret;
}

int Connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    int ret;
    if((ret = connect(sockfd, addr, addrlen)) == -1) {
        err_sys("connect error");
        exit(1);
    }
    return ret;
}