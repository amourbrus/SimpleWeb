import socket
import re
import multiprocessing
import dynamic.frame

# 1 socket套接字(创建套接字、端口复用) 绑定(bind) 监听(listen) >> 在init内,基本不变
# main  接受数据(accept) >>>  handle_client  recv  >> 也基本不变，这是tcp协议的流程，not change
# 2 接受的http协议格式的数据 client_data
# 2.1 分析请求数据   split获得请求行（首行） get /index.html http/1.1  通过正则获取文件的名字 re.match
# 2.2对文件路径做一些操作，如默认网页等
# 2.3由得到的文件名打开文件， 应答体的内容即是读取到的内容/ 同时，要符合http协议，所以要设置response_line/ 格式和内容也基本不变
# >> 为了分开处理(框架，分文件处理)， 在打开文件时做个判断， 动态文件(.html)else 处理
# 2.4重点是else 的内容， 创建了一个接口:(需要注意的是接口函数的参数，还要def一个函数，回传)(这里的思想是要理解的,
# 具体服务器内容因为工作以不用写，但感觉这里的思想有用)
# response_body = dynamic.mini_frame.application(env, self.set_response_header)
# 2.5接口返回的数据就作为包体内容， else 其他内容就是做一些和前面一样的工作：http协议格式
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
        """用来处理客户端的数据的"""
        # 客户端的数据
        client_data = client_socket.recv(4096)
        # 符合http协议的请求信息
        client_data = client_data.decode()

        # 5 数据分析 获取数据路径, \r\n回车换行
        data_list = client_data.split("\r\n")

        name = data_list[0]
        # get /index.html http/1.1
        # 通过正则获取文件的名字
        file_name = ""
        result = re.match(r"[^/]+(/[^ ]*)", name)
        # 获取文件名
        if result:
            file_name = result.group(1)

            if file_name == "/":
                file_name = "/index.html"

        # ./static/index.html
        # 获取路径信息
        file_path = "./static" + file_name
        if not file_name.endswith(".html"):
            # 进行检测看看有没有这个文件  静态
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
        else:
            # 动态

            env = dict()    # env ={}
            env["url"] = file_name
            # 这个要在前面， 因为要产生statue
            # 要def 一个函数set_response_header, 具体看application内的名字， 名字可以换的
            response_body = dynamic.frame.application(env, self.set_response_header)

            response_line = "http/1.1 %s\r\n" % self.statue
            # for i in self.headers:
            #     response_line += "%s:%s\r\n" % (i[0], i[1])

            response_data = response_line + "\r\n" + response_body
            client_socket.send(response_data.encode())

            client_socket.close()

    def set_response_header(self, statue):
        self.statue = statue
        # self.headers = headers

    def run_forever(self):
        while True:
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
    # 程序的入口
    main()

