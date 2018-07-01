import pymysql
import re
import urllib.parse as urp

FUNC_URL_LIST = {}


def application(environ, start_response):
    file_name = environ["url"]
    start_response("200 ok")  # 这是写死的啊，有什么用？？传回去也是一个定值
    for key, value in FUNC_URL_LIST.items():
        ret = re.match(key, file_name)
        if ret:
            return value(ret)
    else:    # 特别要注意位置，如果错，就会一直弹出404 not found------
        return "%s 404 not found------ " % file_name  # 如果没找到,就返回
        # 请求的内容,写代码的过程中需要,如只写了index, 则在点击添加按钮时就知道了请求的函数名（样式）


def route(my_data):
    def func_out(func):
        FUNC_URL_LIST[my_data] = func
        return func

    return func_out


@route(r"/index.html")  # file_name
def index(ret):
    # 读取文件（数据库本地）
    with open('./templates/index.html') as f:
        content = f.read()
    # 连接数据库
    # db = pymysql.connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db',
    #                      charset='utf8')
    # cursor = db.cursor()
    db, cursor = db_connect()
    # sql语句
    sql = "select * from info;"
    cursor.execute(sql)
    my_stock = cursor.fetchall()
    # 模板
    temp = """
<tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
            <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s">
        </td>
        </tr>
    """
    html = ""
    for i in my_stock:
        html += temp % (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[1],)
    content = re.sub(r"{%content%}", html, content)
    cursor.close()
    db.close()
    return content


@route(r"/center.html")
def center(ret):
    # 读取文件（数据库本地）
    with open('./templates/center.html') as f:
        content = f.read()
    # 连接数据库
    db,cursor = db_connect()
    # sql语句
    sql = "select * from info as i inner join focus as f on i.id=f.id;"
    # line 99, in center   若sql语句错误,出现报错
    #     html += temp % (i[1], i[2], i[3], i[4], i[5], i[6], i[9], i[1], i[1])
    # IndexError: tuple index out of range
    cursor.execute(sql)
    my_stock = cursor.fetchall()
    # 模板
    temp = """<tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>

                <td>
                    <a type="button" class="btn btn-default btn-xs" href="/update/%s.html">
                    <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
                </td>
                <td>
                    <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
                </td>
            </tr>
    """
    html = ""
    for i in my_stock:
        html += temp % (i[1], i[2], i[3], i[4], i[5], i[6], i[9], i[1], i[1])
    content = re.sub(r"{%content%}", html, content)
    cursor.close()
    db.close()
    return content


def db_connect():
    db = pymysql.connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db',
                         charset='utf8')
    cursor = db.cursor()
    return db, cursor


def is_exist_focus(cursor, stock_code):
    sql = "select * from info where code = %s;"
    cursor.execute(sql, [stock_code])
    my_stock = cursor.fetchall()
    if not my_stock:
        return "%s is not existing" % stock_code

    sql = "select * from focus where id = (select id from info where code = %s);"
    cursor.execute(sql, [stock_code])
    my_focus = cursor.fetchall()
    if my_focus:
        return "%s have focused" % my_focus

    return ""


@route(r"/add/(\d+).html")
def add_stock(ret):
    stock_code = ret.group(1)
    db, cursor = db_connect()
    rets = is_exist_focus(cursor, stock_code)
    if rets:
        return rets
    sql = "insert into focus(id) select id from info where code=%s;"
    cursor.execute(sql, [stock_code])

    db.commit()
    cursor.close()
    db.close()

    return "%s add success " % stock_code


@route(r"/del/(\d+).html")
def del_stock(ret):
    stock_code = ret.group(1)
    db, cursor = db_connect()

    sql = "delete from focus where id = (select id from info where code = %s);"
    cursor.execute(sql, [stock_code])

    db.commit()
    cursor.close()
    db.close()
    return "%s delete finish" % stock_code

@route(r"/update/(\d+).html")
def update(ret):
    with open("./templates/update.html") as f:
        content = f.read()
    stock_code = ret.group(1)
    db,cursor = db_connect()
    sql="select note_info from focus where id=(select id from info where code=%s);"
    cursor.execute(sql,[stock_code])
    stock_note_info = cursor.fetchall()

    content = re.sub(r"{%code%}",stock_code,content)
    content = re.sub(r"{%note_info%}",stock_note_info[0][0],content)
    cursor.close()
    db.close()
    return content


@route(r"/update/(\d+)/(.*).html")
def change_stock(ret):
    stock_code = ret.group(1)
    change_info = urp.unquote(ret.group(2))

    db, cursor = db_connect()
    sql = "update focus set note_info = %s where id = (select id from info where code = %s);"
    cursor.execute(sql,[change_info, stock_code])

    db.commit()
    cursor.close()
    db.close()
    return "%s changed success" % stock_code
