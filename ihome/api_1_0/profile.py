from . import api
from ihome.utils.commons import login_required
from flask import g, jsonify, request, current_app, session
from ihome.utils.response_code import RET
from ihome.utils.fdfs.storage import FdfsStorage
from ihome.models import User
from ihome import db
from ihome import constants

@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    '''
    设置用户头像
    参数： 图片(多媒体表单格式)     用户id
    '''
    # login_required装饰器中已经将user_id保存到g对象中，所以视图函数中可以直接读取
    user_id = g.user_id
    # 获取图片
    avatar = request.files.get('avatar')

    if avatar is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图片')

    avatar_data = avatar.read()
    # 调用fdfs上传图片，返回文件名
    try:
        fdfd_storage = FdfsStorage()
        filename = fdfd_storage.upload(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')

    # 保存文件名到数据库中
    try:
        user = User.query.filter_by(id=user_id).update({'avatar_url':filename})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片信息失败')

    avatar_url = constants.FDFS_BASE_URL + filename

    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg='保存成功', data={'avatar_url':avatar_url})


@api.route('/users/name', methods=['PUT'])
@login_required
def change_user_name():
    '''
        修改用户名
        参数： 修改的用户名    用户id
        '''
    # login_required装饰器中已经将user_id保存到g对象中，所以视图函数中可以直接读取
    user_id = g.user_id
    # 获取修改后用户名
    request_data = request.get_json()

    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    name = request_data.get('name')     # 用户想要设置的名字
    if name is None:
        return jsonify(errno=RET.PARAMERR, errmsg='名字不能为空')

    # 保存用户昵称name，并同时判断name是否重复(利用数据库的唯一索引)
    try:
        user = User.query.filter_by(id=user_id).update({'name': name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='设置用户名错误')

    # 修改session数据中name字段
    session['name'] = name
    # 保存成功返回
    return jsonify(errno=RET.OK, errmsg='保存成功', data={'name': name})


@api.route('/users', methods=['GET'])
@login_required
def get_user_profile():
    '''获取个人信息'''
    # login_required装饰器中已经将user_id保存到g对象中，所以视图函数中可以直接读取
    user_id = g.user_id

    # 查询数据库获取个人信息
    try:
        # user = User.query.filter_by(id=user_id).first()
        user = User.query.get(user_id)
        # print(user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')

    # print(user.to_dict())
    # print(user)
    # 保存成功返回    User类中有自定义一个to_dict方法，这个方法返回一个保存了用户对应信息的字典
    return jsonify(errno=RET.OK, errmsg='保存成功', data=user.to_dict())

@api.route('/users/auth', methods=['GET'])
@login_required
def get_user_auth():
    '''获取用户的实名认证信息'''
    # login_required装饰器中已经将user_id保存到g对象中，所以视图函数中可以直接读取
    user_id = g.user_id

    # 查询数据库获取个人信息
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')

    # 保存成功返回    User类中有自定义一个to_dict方法，这个方法返回一个保存了用户对应信息的字典
    return jsonify(errno=RET.OK, errmsg='保存成功', data=user.auth_to_dict())


@api.route('/users/auth', methods=['POST'])
@login_required
def set_user_auth():
    '''保存实名认证信息'''
    user_id = g.user_id

    # 获取前端传递过来的json数据
    request_json = request.get_json()
    if not request_json:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    real_name = request_json.get('real_name')   # 真实姓名
    id_card = request_json.get('id_card')   # 身份证号

    # 校验参数
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 保存用户的姓名与身份证号
    auth_dict = {
        'real_name': real_name,
        'id_card': id_card
    }
    try:
        # 设置用户只可以认证一次，只有姓名和身份证号为空(也就是第一次未认证的时候)才可以修改
        user = User.query.filter_by(id=user_id, real_name=None, id_card=None).update(auth_dict)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存用户实名信息失败')

    return jsonify(errno=RET.OK, errmsg='OK')














