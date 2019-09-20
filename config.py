# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
import redis
# from flask_wtf import CSRFProtect
# from flask_session import Session


class Config(object):
    """配置信息`"""
    DEBUG = True
    SECRET_KEY = "ASDDFG*GHJGHJ&^97XVX"
    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/Ihome_flask"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask_session的设置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 2*3600   # 对session数据的有效期设置


class DevelopmentConfig(Config):
    """开发模式配置"""
    DEBUG = True


class ProdunctionConfig(Config):
    """生产上线模式"""
    # DEBUG = False
    pass

config_map = {
    "deve": DevelopmentConfig,
    "prod": ProdunctionConfig,
}