
from Ihome.utils.commons import ReConverter
import redis
from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from config import config_map
from flask_session import Session


# 创建数据库对象
db = SQLAlchemy()
# 创建redis链接对象
redis_store = None
# 为flask补充csrf防护
csrf = CSRFProtect()


# logging.basicConfig(level=logging.INFO)
# # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
# file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# # 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
# formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# # 为刚创建的日志记录器设置日志记录格式
# file_log_handler.setFormatter(formatter)
# # 为全局的日志工具对象（flask app使用的）添加日记录器
# logging.getLogger().addHandler(file_log_handler)  # 调试debug级(如果级别选为debug级别,
#                                           # 上面的info,warn,error错误信息全部会打印到日志文件中)
# logging.error('')          # 出错级别 (最高级别,由上往下)
# logging.warn('')           # 警告级别
# logging.info('')           # 消息提示级别
# logging.debug('')          # 调试级别





# 工厂模式
def create_app(config_name):
    """
    创建flask的APP对象
    :param config_name:配置模式的类名(develop, produntion)
    :return:
    """

    app = Flask(__name__)
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用init_app初始化db对象
    db.init_app(app)

    # redis初始化
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # 为flask补充CSRF防护
    CSRFProtect(app)

    # 利用flask_session,把session数据保存到redis中
    Session(app)

    # 为flask添加自定义的正则转换器
    app.url_map.converters["re"] = ReConverter
    # 注册蓝图
    from Ihome import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    # 注册提供静态文件的的蓝图
    from Ihome import web_html
    app.register_blueprint(web_html.html)

    return app