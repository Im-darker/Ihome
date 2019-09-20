from flask import session

from Ihome import db
from Ihome.models import User
from Ihome.utils.commons import login_required
from Ihome.utils import constants
from Ihome.utils.image_storage import storage
from Ihome.utils.response_code import RET
from . import api
from flask import g, current_app, jsonify, request


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像
    参数：user_id, 多媒体流的image_data
    """
    # 获取user_id
    user_id = g.user_id
    # 获取图片
    image_file = request.files.get("avatar")


    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="图片获取失败")

    image_data = image_file.read()

    try:
        # 上传七牛云
        file_name = storage(image_data)
        # print(file_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传错误")
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)

        return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

    avatar_url = constants.QI_NIU_URL + file_name
    # session["avatar_url"] = avatar_url

    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})


@api.route("/users/name", methods=["PUT"])
@login_required
def set_users_name():
    """
    设置用户名称
    参数：user_id, user_name
    """
    user_id = g.user_id
    name_dict = request.get_json()
    # name = name_dict.get("name")
    if not name_dict:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    name = name_dict.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    try:
        User.query.filter_by(id=user_id).update({"name": name})
        # db.session.add()
        db.session.commit()

    except Exception as e:
        # 数据回滚
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="设置错误")

    session["name"] = name
    return jsonify(errno=RET.OK, errmsg="修改成功", data={"name": name})


@api.route("/user", methods=["GET"])
@login_required
def info_user():
    """
    显示个人信息
    name,
    mobile
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="操作无效")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """
    获取用户实名认证信息
    real_name,
    id_card
    """
    user_id = g.user_id

    try:
        user = User.query.get(user_id)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    # 判断用户所填的user_id是否存在
    if user is None:
        return jsonify(errno=RET.USERERR, errmsg="参数错误")

    real_name = user.real_name
    id_card = user.id_card
    return jsonify(errno=RET.OK, errmsg="OK", data={"id_card": id_card, "real_name": real_name})



@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    data_dict = request.get_json()
    real_name = data_dict.get("real_name")
    id_card = data_dict.get("id_card")

    if data_dict is None:
        return jsonify(errno=RET.DATAERR, errmsg="数据获取错误")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    user_id = g.user_id
    # try:
    #     user = User.query.get(user_id)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    #
    # if user is None:
    #     return jsonify(errno=RET.USERERR, errmsg="参数错误")

    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None)\
            .update({"real_name": real_name, "id_card": id_card})
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存错误")
    db.session.commit()
    session["real_name"] = real_name
    session["id_card"] = id_card
    return jsonify(errno=RET.OK, errmsg="保存成功")







