
from flask import Blueprint

# 创建蓝图对象
api = Blueprint("api_1_ 0", __name__)


from . import verify, passport, profile, house, orders, alpay
