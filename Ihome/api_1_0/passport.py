import re

from flask import session
from sqlalchemy.exc import IntegrityError

from Ihome import redis_store, db
from Ihome.models import User
from Ihome.utils import constants
from Ihome.utils.response_code import RET
from . import api
from flask import request, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash


@api.route("/users", methods=["POST"])
def register():
    """注册
    请求参数：手机号,短信验证码,密码
    参数格式：json
    """
    # 一次性把json数据转换成字典
    json_dict = request.get_json()
    sms_code = json_dict.get("sms_code")
    mobile = json_dict.get("mobile")
    password = json_dict.get("password")
    password2 = json_dict.get("password2")

    if not all([mobile, password, sms_code, password2]):
        return jsonify(errno=RET.DATAERR, errmsg="缺少必要参数")

    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机格式错误")

    if password != password2:
        print(password)
        print(password2)
        return jsonify(errno=RET.DATAERR, errmsg="输入的密码不一致")

    # 从redis中获取短信验证码
    try:
        server_redis_sms_code = redis_store.get("sms_code_%s" % mobile)
        print(server_redis_sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取短息验证码异常")

    # 验证短息验证码是否失效
    print(server_redis_sms_code)
    if server_redis_sms_code is None:
        return jsonify(errno=RET.DBERR, errmsg="短息验证码失效")

    # 删除短息验证码,防止同一短息验证码反复校验
    try:

        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 验证短息验证码是否一致
    if server_redis_sms_code.decode() != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短息验证出错")

    # 判断手机号是否注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="查询数据库的手机号出错")
    #
    # if user is not None:
    #     return jsonify(errno=RET.DATAEXIST, errmsg="此手机号已注册")
    #
    # 保存用户注册的数据到db中
    user = User(mobile=mobile, name=mobile)
    # 对明文密码进行hash加密
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()

    # 这是一个捕获同一手机存有多个值报错的类
    except IntegrityError as e:
        # 如果数据保存出错,就进行事务回滚
        # 如果出错，说明这个手机号已经注册过了
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误,手机号以存在")
    except Exception as e:
        # 如果数据保存出错,就进行事务回滚
        # 如果出错，说明这个手机号已经注册过了
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询出现错误")

    # 使用session来保持用户登陆状态
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回数据结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """用户登录"""
    # 获取参数
    json_dict = request.get_json()
    mobile = json_dict.get("mobile")

    password = json_dict.get("password")

    #校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmasg="缺少参数")

    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式错误")

    # 为了防止用户暴力测试,登陆次数超过限制次数，　限制其禁止访问１０分钟
    user_ip = request.remote_addr   # 获取用户登陆的ＩＰ
    try:
        access_num = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        print(access_num)
        if access_num is not None and int(access_num.decode()) >= constants.LOGIN_ERROR_MAX_TIME:
            return jsonify(errno=RET.REQERR, errmsg="登陆次数过多")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息错误")
    # 用户验证失败
    # res = user.check_password(password)
    # print(res)
    # print(user is None)
    if user is None or not user.check_password(password):
        try:
            # 计算这个ip登陆的次数，并设置禁止时间１０分钟
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg="密码或用户错误")

    # 用户验证成功
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登陆成功")


@api.route("/session", methods=["GET"])
def Check_User_Login():
    """从session中检测是否有name值,
    从而判断用户是否登陆"""
    name = session.get("name")
    if name:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    """
    用户退出登陆,
    清除session数据
    """
    session.clear()
    return jsonify(errno=RET.OK, errmsg="数据已清除")








