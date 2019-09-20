from . import api
from Ihome import db, models
from flask import current_app

@api.route("/index")
def index():
    # current_app.logger.error("一级错误")
    # current_app.logger.warn("一级错误")

    return "哈　罗"
