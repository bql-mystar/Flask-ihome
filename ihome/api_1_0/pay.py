from . import api
from ihome import db
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g, current_app, jsonify, request
from ihome.utils.response_code import RET
from alipay import AliPay
import os
from ihome import constants
import json


@api.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
def order_pay(order_id):
    '''发起支付宝支付'''
    user_id = g.user_id
    # 判断订单状态
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == 'WAIT_PAYMENT').first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg='订单数据有误')

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), 'keys/app_private_key.pem')).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), 'keys/alipay_public_key.pem')).read()
    # 创建支付宝的SDK工具对象
    alipay = AliPay(
        appid="2021000118643231",
        app_notify_url=None,  # the default notify path
        app_private_key_string=app_private_key_string,
        # alipay public key, do not use your own public key!
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA or RSA2
        debug=True,  # False by default
        # config=AliPayConfig(timeout=15)  # optional, request timeout
    )

    order_string = alipay.api_alipay_trade_wap_pay(
        out_trade_no=order.id,      # 订单编号
        total_amount=str(order.amount/100.0),       # 总金额
        subject='爱家 %s' % order.id,     # 订单标题
        return_url="http://127.0.0.1:5000/payComplete.html",    # 返回的链接地址
        notify_url=None  # this is optional
    )

    # 构建让用户跳转的支付链接地址
    pay_url = constants.ALIPAY_URL_PREFIX + order_string

    return jsonify(errno=RET.OK, errmsg='OK', data={'pay_url':pay_url})

@api.route('/orders/payment', methods=['PUT'])
def save_order_payment_result():
    '''保存订单支付结果'''
    alipay_data = request.form.to_dict()
    # sign must be poped out
    # 对支付宝的数据进行分离操作     提取出支付宝的签名参数sign值 和 剩下的其他数据
    signature = alipay_data.pop("sign")

    print(json.dumps(alipay_data))
    print(signature)

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), 'keys/app_private_key.pem')).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), 'keys/alipay_public_key.pem')).read()
    # 创建支付宝的SDK工具对象
    alipay = AliPay(
        appid="2021000118643231",
        app_notify_url=None,  # the default notify path
        app_private_key_string=app_private_key_string,
        # alipay public key, do not use your own public key!
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA or RSA2
        debug=True,  # False by default
        # config=AliPayConfig(timeout=15)  # optional, request timeout
    )

    # verify
    # 借助工具验证参数的合法性
    # 如果确定参数是支付宝的，返回True，否则返回False
    result = alipay.verify(alipay_data, signature)
    order_id = alipay_data.get('out_trade_no')
    trade_no = alipay_data.get('trade_no')
    if result:
        try:
            Order.query.filter_by(id=order_id).update({'status':'WAIT_COMMENT', 'trade_no':trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg='OK')
