from flask import Blueprint, current_app, make_response
from flask_wtf import csrf

# 提供静态文件的蓝图
html = Blueprint('web_html', __name__)

@html.route("/<re(r'.*'):html_file_name>")
def get_html(html_file_name):
    '''提取静态文件'''
    # html文件的路径为/static/html/...
    # 如果直接访问/的话，那么默认访问index.html
    # 文件中含有一个favicon.ico文件，这个文件是对应网站的小图标。浏览网站的时候会默认访问这个小图标
    # 这个小图标的路径为/static/favicon.ico
    if not html_file_name:
        html_file_name = 'index.html'

    # 如果文件资源名不是favicon.ico
    if html_file_name != 'favicon.ico':
        html_file_name = 'html/' + html_file_name

    # 创建一个csrf_token值
    csrf_token = csrf.generate_csrf()

    # flask提供的返回静态文件的方法
    resp = make_response(current_app.send_static_file(html_file_name))

    # 设置cookie值
    resp.set_cookie('csrf_token', csrf_token)
    return resp

