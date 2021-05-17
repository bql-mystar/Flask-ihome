from . import api
from ihome import redis_store, constants
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
import re
from ihome.models import User, db
from sqlalchemy.exc import IntegrityError

@api.route('/users', methods=['POST'])
def register():
    '''
    注册
    请求的参数： 手机号、短信验证码、密码、确认密码
    参数格式： json
    '''
    # 获取请求的json数据，返回字典
    request_json = request.get_json()
    mobile = request_json.get('mobile')
    sms_code = request_json.get('sms_code')
    print(sms_code)
    password = request_json.get('password')
    password_submit = request_json.get('password_submit')
    # 校验参数
    if not all([mobile, sms_code, password, password_submit]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 判断手机号格式
    if not re.match(r'1[34578]\d{9}', mobile):
        # 表示手机号格式不多
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')

    if password_submit != password:
        return jsonify(errno=RET.PARAMERR, errmsg='两次密码不一致')

    sms_code_mobile = 'sms_code_%s' % mobile
    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get(sms_code_mobile)
        print(real_sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='读取真实短信验证码异常')

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码失效')

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        redis_store.delete(sms_code_mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='')

    # 判断用户填写短信验证码的正确性
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')

    # 判断用户的手机号是否注册过
    # 保存用户的注册数据到数据库中
    user = User(name=mobile, mobile=mobile)
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        # 表示手机号出现了重复值，即手机号已经注册过
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库异常')

    # 保存登录状态到session中
    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='注册成功')



@api.route('/sessions', methods=['POST'])
def login():
    '''
    用户登录
    参数： 手机号， 密码
    '''
    # 获取参数
    request_json = request.get_json()
    mobile = request_json.get('mobile')
    password = request_json.get('password')
    # 校验参数
    # 参数完整的校验
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 手机号的格式
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 判断错误次数是否超过限制，如果超过限制，则返回
    # 通过request中的remote_addr方法，可以获取访问的ip
    user_ip = request.remote_addr
    print(user_ip)
    # 通过redis来记录：   'access_nums_用户ip' : 次数
    access_nums_ip = 'access_nums_%s' % user_ip
    try:
        access_nums = redis_store.get(access_nums_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg='错误次数过多，请稍后重试')
    # 从数据库中根据手机号查询用户的数据对象
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')

    # 用数据库的密码与用户填写的密码进行对比验证
    if user is None or user.check_password(password) is False:
        # 如果验证失败，记录错误信息，返回信息
        try:
            redis_store.incr(access_nums_ip)
            redis_store.expire(access_nums_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg='用户名或密码错误')

    # 验证相同相同成功，保存登录状态在session中
    session['name'] = user.name
    session['mobile'] = mobile
    session['user_id'] = user.id

    return jsonify(errno=RET.OK, errmsg='登录成功')

@api.route('/sessions', methods=['GET'])
def check_login():
    '''检查登录状态'''
    # 尝试从session中获取用户的名字
    name = session.get('name')
    # print(name)
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={"name":name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')

@api.route('/sessions', methods=['DELETE'])
def logout():
    '''登出(退出)'''
    # 清除session数据
    csrf_token = session.get('csrf_token')
    session.clear()
    session['csrf_token'] = csrf_token
    return jsonify(errno=RET.OK, errmsg='OK')















