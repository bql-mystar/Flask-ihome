from fdfs_client.client import Fdfs_client, get_tracker_conf
from ihome import constants

# 配置图片存储的基类
# FDFS_BASE_URL = constants.FDFS_BASE_URL
# 客户端的配置文件的路径
FDFS_CLIENT_CONF= constants.FDFS_CLIENT_CONF


class FdfsStorage:
    '''使用单例来定义fdfs文件上传类'''
    instance = None
    def __new__(cls, *args, **kwargs):
        # 判断有没有已经创建好的对象，如果没有，创建一个对象，并且保存
        # 如果有，则将保存的对象返回
        if cls.instance is None:
            obj = super().__new__(cls)
            # 创建客户端链接对象
            # 1、创建一个Fdfs_client对象，创建过程中需要指定一个client的配置文件，django在查找内容的时候，是从根目录开始查找，而不是相对路径，因此如果写相对路径就会报错
            # 由配置文件中的信息 得到 字典trackers
            obj.tracker = get_tracker_conf(FDFS_CLIENT_CONF)
            # tracker = get_tracker_conf('./client.conf')
            obj.client = Fdfs_client(obj.tracker)
            cls.instance = obj
        return cls.instance

    def upload(self, content):
        '''
        fdfs上传文件方法
        :param content: 上传文件对应的二进制格式
        :return: 返回访问文件的url路径
        '''
        # 创建客户端链接对象
        # 1、创建一个Fdfs_client对象，创建过程中需要指定一个client的配置文件，django在查找内容的时候，是从根目录开始查找，而不是相对路径，因此如果写相对路径就会报错
        # 由配置文件中的信息 得到 字典trackers
        # tracker = get_tracker_conf(self.FDFS_CLIENT_CONF)
        # tracker = get_tracker_conf('./client.conf')
        # client = Fdfs_client(tracker)
        # 上传文件到fdfs中，可以根据文件名上传，也可以根据文件内容上传，根据需求进行选择
        res = self.client.upload_by_buffer(content)
        # 以上返回的是一个字典，字典格式如下
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        # 只需要关注Status和Storage IP，Status为上传状态，成功的话返回Upload successed.字符串，Remote file_id为上传后返回的在fdfs中的文件名
        if res.get('Status') != 'Upload successed.':
            # 上传失败，为了代码的通用性，不能直接去捕获异常，可以抛出一个上传文件异常
            raise Exception('上传文件到fdfss失败')
            # return None
        # 获取返回文件ID
        filename = res.get('Remote file_id').decode()
        # 返回访问文件的url路径
        # return self.FDFS_BASE_URL + filename
        # 如果直接拼接好对应的ip地址和端口号，一旦ip地址发生变化，那么数据库中所有的内容都会失效
        return filename

if __name__ == '__main__':
    with open('D:/IT学习/python学习练习/Flask-ihome/ihome/static/images/landlord01.jpg', 'rb') as f:
        file_content = f.read()

    # fdfs_upload = FdfsStorage()
    # ret = fdfs_upload.save(file_content)
    # print(ret)
    f1 = FdfsStorage()
    ret = f1.upload(file_content)
    print(f1)
    print(ret)
    f2 = FdfsStorage()
    ret = f2.upload(file_content)
    print(f2)
    print(ret)







