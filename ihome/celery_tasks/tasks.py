from celery import Celery
from ihome.libs.send_sms import CCP

celery_app = Celery('ihome', broker='redis://192.168.0.111:6379/1')

@celery_app.task
def send_sms(tid, mobile, datas):
    ccp = CCP()
    ccp.send_message(tid, mobile, datas)