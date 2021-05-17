# 虚拟机对应的IP地址
VIRTUAL_MACHINE_IP = '192.168.0.115'

# 图片验证码的redis有效期，单位：秒
IMAGE_CODE_REDIS_EXPIRE = 180

# 短信验证码的redis有效期，单位秒
SMS_CODE_REDIS_EXPIRE = 300

# 发送短信验证码的间隔，单位：秒
SEND_SMS_CODE_INTERVAL = 60

# 登录错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误限制的时间, 单位：秒
LOGIN_ERROR_FORBID_TIME = 600

# 设置fdfs的client_conf文件路径
FDFS_CLIENT_CONF = 'D:/IT学习/python学习练习/Flask-ihome/ihome/utils/fdfs/client.conf'
# 设置fdfs存储服务器上nginx的IP和端口号
FDFS_BASE_URL = 'http://192.168.0.115:8888/'

# 城区信息的缓存时间，单位：秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页展示最多的房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据redis缓存时间， 单位：秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页展示的评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据Redis缓存时间，单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页面页数缓存时间，单位秒
HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# 支付宝的网关地址 (支付地址域名)
ALIPAY_URL_PREFIX = 'https://openapi.alipaydev.com/gateway.do?'

