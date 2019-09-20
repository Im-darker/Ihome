import functools
from flask import session, jsonify, g
from werkzeug.routing import BaseConverter
from Ihome.utils.response_code import RET


# 定义正则转换器
class ReConverter(BaseConverter):
    def __init__(self, url_map, regex):

        super(ReConverter, self).__init__(url_map)
        # 保存正则表达式
        self.regex = regex


# 验证用户登陆的装饰器
def login_required(view_func):
    # 还原被装饰的函数名
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        # 把user_id放到全局g变量中,以便被装饰函数调用
        g.user_id = user_id

        if user_id:
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    return wrapper

