import redis
from ihome import constants

class Config(object):
    '''配置信息'''
    # DEBUG = True
    SECRET_KEY = 'ILOVEXHX'
    # 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@' + constants.VIRTUAL_MACHINE_IP + ':3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis
    REDIS_HOST = constants.VIRTUAL_MACHINE_IP
    REDIS_PORT = 6379
    # flask-session配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True   # 对cookie中的session_id进行隐藏
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期，单位秒

class DevelopmentConfig(Config):
    '''开发模式的配置信息'''
    DEBUG = True

class ProductionConfig(Config):
    '''生产环境配置信息'''
    pass

config_map = {
    'develop': DevelopmentConfig,
    'product': ProductionConfig
}

