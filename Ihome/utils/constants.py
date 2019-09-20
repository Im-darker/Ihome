# coding:utf-8


# 图片验证码的redis有效期, 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有效期, 单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的间隔, 单位：秒
SEND_SMS_CODE_INTERVAL = 60

# 登陆错误尝试的次数
LOGIN_ERROR_MAX_TIME = 5

# 登陆错误的所限制的时间
LOGIN_ERROR_TIME = 600

# 七牛云的ＵＲＬ
QI_NIU_URL = "http://pw4b5uqiy.bkt.clouddn.com/"

# 城区的缓存时间
AREA_INFO_TIME = 2*3600

# 首页图片的最大数量
home_page_max = 6

# 房子的图片缓存时间
HOME_PAGE_CACHE_TIME = 1.5*3600

# 房屋搜说界面一页的最大数量
HOUSE_PAGE_MAX_NUMBER = 3

# 房屋搜说列表的数据缓存时间
HOUSE_LIST_CACHE_DATA_TIME = 7200

# 返还订单列表的数据个数
ORDER_LIAT_MAX_NB = 5

# 支付宝的网关地址
ALIPAY_URL_PREFIX = "https://openapi.alipaydev.com/gateway.do?"