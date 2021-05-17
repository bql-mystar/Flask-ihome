from ronglian_sms_sdk import SmsSDK
import json

accId = '8a216da874af5fff01751164ae401f50'
accToken = '36cb4e7e6a494d7a83233f38f65315b5'
appId = '8a216da874af5fff01751164af861f57'


class CCP(object):
    '''自己封装的发送短信的辅助类'''
    # 用来保存对象的类属性
    instance = None

    def __new__(cls):
        # 判断CCP有没有已经创建好的对象，如果没有，创建一个对象，并且保存
        # 如果有，则将保存的对象返回
        if cls.instance is None:
            obj = super().__new__(cls)
            obj.sdk = SmsSDK(accId, accToken, appId)
            cls.instance = obj
        return cls.instance

    def send_message(self, tid, mobile, datas):
        """发送短信
                Args:
                    tid: 短信模板ID，容联云通讯网站自行创建
                    mobile: 下发手机号码，多个号码以英文逗号分隔
                    datas: 模板变量
                Returns:
                    返回发送结果和发送成功消息ID
                    发送成功示例:
                    {"statusCode":"000000","templateSMS":{"dateCreated":"20130201155306",
                     "smsMessageSid":"ff8080813c373cab013c94b0f0512345"}}
                    发送失败示例：
                    {"statusCode": "172001", "statusMsg": "网络错误"}
                """
        resp = self.sdk.sendMessage(tid, mobile, datas)
        # print(resp)
        resp = json.loads(resp)
        status_code = resp.get('statusCode')
        if status_code == '000000':
            # 表示发送短信成功
            return 0
        else:
            # 短信发送失败
            return -1


if __name__ == '__main__':
    ccp = CCP()
    # ccp1 = CCP()
    # print(ccp)
    # print(ccp1)
    resp = ccp.send_message(1, '18759875182', ['1478', '1'])
    print(resp)