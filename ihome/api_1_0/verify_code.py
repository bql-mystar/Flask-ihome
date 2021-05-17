from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, db
from ihome import constants
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
import random
from ihome.libs.send_sms import CCP
from ihome.celery_tasks.tasks import send_sms

@api.route('/image_codes/<image_code_id>', methods=['GET'])
def get_image_code(image_code_id):
    '''
    获取图片验证码
    :param image_code_id: 图片验证码编号
    :return: 正常：验证图片    异常：返回json
    '''
    # 业务逻辑处理
    # 生成验证码图片
    # 名字  真实文本  图片数据
    name, text, image_data = captcha.generate_captcha()
    # 将验证码真实值与编号保存到redis中，使用set集合
    image_code_id_number = 'image_code_%s' % image_code_id
    # redis_store.set(image_code_id_number, text)
    # redis_store.expire(image_code_id_number, constants.IMAGE_CODE_REDIS_EXPIRE)
    # 以上两行代码可以整合成以下一行，setex方法中既可以设置对应的键值对，还可以设置有效期
    try:
        #                       记录名字                有效期                         记录值
        redis_store.setex(image_code_id_number, constants.IMAGE_CODE_REDIS_EXPIRE, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        # return jsonify(errorno=RET.DBERR, errmsg='save image code id failed')
        return jsonify(errorno=RET.DBERR, errmsg='保存图片验证码失败')
    # 返回图片
    resp = make_response(image_data)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp

# 未使用异步celery
# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>', methods=['GET'])
# def get_sms_code(mobile):
#     # 获取参数
#     image_code = request.args.get('image_code')
#     image_code_id = request.args.get('image_code_id')
#     print(image_code)
#     print(image_code_id)
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         # 表示参数不完整
#         return jsonify(errorno=RET.PARAMERR, errmsg='参数不完整')
#     # 业务逻辑处理
#     # 从reids中取出真实的图片验证码
#     image_code_id_number = 'image_code_%s' % image_code_id
#     try:
#         real_image_code = redis_store.get(image_code_id_number)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')
#     # 在redis中，如果设置的值过期了，那么不会以异常的形式来体现出来，而是通过返回值为None来体现
#     # 判断图片验证码是否过期
#
#     if real_image_code is None:
#         # 表示图片验证码过期
#         return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')
#     # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
#     try:
#         redis_store.delete(image_code_id_number)
#     except Exception as e:
#         current_app.logger.error(e)
#     # 与用户填写的值进行对比
#     # real_image_code = real_image_code.decode('utf-8')
#     print(real_image_code)
#     if real_image_code.lower() != image_code.lower():
#         # 用户填写错误
#         return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
#     send_sms_code_id = 'send_sms_code_%s' % mobile
#     # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
#     try:
#         send_flag = redis_store.get(send_sms_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示在60秒内有过发送记录
#             return jsonify(errno=RET.REQERR, errmsg='请求过于频繁，请60秒后重试')
#     # 判断手机号是否存在
#     # 在sqlalchemy中如果查询不出东西来，不会抛出一个异常，而是返回一个None
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 表示号码已存在
#             return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')
#
#     # 如果手机号不存在，则生成短信验证码
#     sms_code = '%06d' % random.randint(0, 999999)
#     sms_code_mobile = 'sms_code_%s' % mobile
#     # 保存真实的短信验证码
#     try:
#         redis_store.setex(sms_code_mobile, constants.SMS_CODE_REDIS_EXPIRE, sms_code)
#         # 保存发送给这个手机号的记录，防止用户在60秒内再次发出发送短信的操作
#         redis_store.setex(send_sms_code_id, constants.SEND_SMS_CODE_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')
#
#     # 发送短信
#     try:
#         ccp = CCP()
#         result = ccp.send_message(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRE/60)])
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR, errmsg='发送异常')
#
#     # 返回值
#     if result == 0:
#         # 发送成功
#         return jsonify(errno=RET.OK, errmsg='发送成功')
#     else:
#         return jsonify(errno=RET.THIRDERR, errmsg='发送失败')

# 使用异步celery
@api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>', methods=['GET'])
def get_sms_code(mobile):
    # 获取参数
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')
    print(image_code)
    print(image_code_id)
    # 校验参数
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(errorno=RET.PARAMERR, errmsg='参数不完整')
    # 业务逻辑处理
    # 从reids中取出真实的图片验证码
    image_code_id_number = 'image_code_%s' % image_code_id
    try:
        real_image_code = redis_store.get(image_code_id_number)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')
    # 在redis中，如果设置的值过期了，那么不会以异常的形式来体现出来，而是通过返回值为None来体现
    # 判断图片验证码是否过期

    if real_image_code is None:
        # 表示图片验证码过期
        return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')
    # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
    try:
        redis_store.delete(image_code_id_number)
    except Exception as e:
        current_app.logger.error(e)
    # 与用户填写的值进行对比
    # real_image_code = real_image_code.decode('utf-8')
    print(real_image_code)
    if real_image_code.lower() != image_code.lower():
        # 用户填写错误
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
    send_sms_code_id = 'send_sms_code_%s' % mobile
    # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
    try:
        send_flag = redis_store.get(send_sms_code_id)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒内有过发送记录
            return jsonify(errno=RET.REQERR, errmsg='请求过于频繁，请60秒后重试')
    # 判断手机号是否存在
    # 在sqlalchemy中如果查询不出东西来，不会抛出一个异常，而是返回一个None
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示号码已存在
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')

    # 如果手机号不存在，则生成短信验证码
    sms_code = '%06d' % random.randint(0, 999999)
    sms_code_mobile = 'sms_code_%s' % mobile
    # 保存真实的短信验证码
    try:
        redis_store.setex(sms_code_mobile, constants.SMS_CODE_REDIS_EXPIRE, sms_code)
        # 保存发送给这个手机号的记录，防止用户在60秒内再次发出发送短信的操作
        redis_store.setex(send_sms_code_id, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')

    # 使用异步celery发送短信
    send_sms.delay(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRE/60)])

    return jsonify(errno=RET.OK, errmsg='发送成功')










