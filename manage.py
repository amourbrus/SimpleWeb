import multiprocessing
import socket

import re


class WebServer(object):
    def __init__(self):
        # 创建套接字 tcp  注意 建立链接
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 端口复用
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 作为服务器 必须固定ip地址 注意 参数是一个元组
        self.tcp_socket.bind(("", 8080))

        # 改变套接字的状态  因为是服务器 进行监听
        self.tcp_socket.listen(128)

    def __del__(self):
        self.tcp_socket.close()

    def handler_client(self, client_socket):
        client_data = client_socket.recv(4096)
        client_data = client_data.decode()

        data_list = client_data.split("\r\n")

        name = data_list[0]

        file_name = ""
        result = re.match(r"[^/]+(/[^ ]*)", name)
        if result:
            file_name = result.group(1)

            if file_name == "/":
                file_name = "/index.html"

        file_path = "./static"+file_name
        # if not file_name.endswith(".html"):
        try:
            f = open(file_path, "rb")
        except:
            # 没有这个文件 发送应答信息 not found
            response_line = "HTTP/1.1 404 NOT FOUND\r\n"
            response_body = "%s 404 not found we will rock you.." % file_name
            response_data = response_line + "\r\n" + response_body
            client_socket.send(response_data.encode())
        else:
            # 成功后返回的信息 找到这个文件了
            response_body = f.read()
            # 关闭文件
            f.close()
            # 应答数据是文件读取出来的  二进制格式
            # 4 组织发送应答信息
            # 应答行
            response_line = "HTTP/1.1 200 OK\r\n"
            response_headers = "Server:python02\r\n"
            # response_headers += "Content-Type: text/html; charset=utf-8\r\n"
            # 组成应答头 注意要有空行
            response_header = response_line + response_headers + "\r\n"
            # 应答头是需要编码
            client_socket.send(response_header.encode())

            # 应答体是二进制的 不需要编码
            client_socket.send(response_body)

        finally:
            # 为了告诉浏览器我的数据发送完毕了
            client_socket.close()
        # else:
        #     # 动态文件
        #     # env = dict()
        #     # env["url"] = file_name
        #     pass


    def run_forever(self):
        # 套接字 注意 收发数据
        new_socket, client_addr = self.tcp_socket.accept()
        # 多进程 注意 参数是元组
        # handler_client(client_socekt)
        p = multiprocessing.Process(target=self.handler_client, args=(new_socket,))
        p.start()
        # 多进程之间是不共享资源的 进程是分配资源的最小单位
        new_socket.close()


def main():
    my_web_server = WebServer()
    my_web_server.run_forever()


if __name__ == '__main__':
    main()