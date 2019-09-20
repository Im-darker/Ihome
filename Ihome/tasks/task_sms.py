from celery import Celery
from Ihome.libs.yuntongxun.sms import CCP

celery_app = Celery("Ihome", broker="redis://127.0.0.1:6379/1")


@celery_app.task
def send_sms(to, datas, temp_id):
    ccp = CCP()
    ccp.send_template_sms(to, datas, temp_id)



