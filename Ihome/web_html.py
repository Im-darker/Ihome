from flask_wtf import csrf
from flask import Blueprint, current_app, make_response

# 提供静态文件处理的蓝图
html = Blueprint("web_html", __name__)


@html.route("/<re(r'.*'):html_file_name>")
def get_html(html_file_name):
    """提供html文件"""
    # 如果html_file_name为'', 表示访问路径为/,返回主页
    if not html_file_name:
        html_file_name = "index.html"

    # 如果资源名不是favicon.ico
    if html_file_name != 'favicon.ico':
        html_file_name = "html/" + html_file_name
    # 生成csrf_token值
    csrf_token = csrf.generate_csrf()

    # flask提供了一个返回静态资源的方法,类似django中的rednder()
    response = make_response(current_app.send_static_file(html_file_name))

    # 设置cookie值
    response.set_cookie("csrf_token", csrf_token)

    return response
