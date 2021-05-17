from . import api
from ihome.models import House, Order
from ihome.utils.commons import login_required
from flask import g, request, jsonify, current_app
from ihome.utils.response_code import RET
import datetime
from ihome import db, redis_store
import json

@api.route('/orders', methods=['POST'])
@login_required
def save_order():
    '''保存订单'''
    user_id = g.user_id
    # 获取参数
    request_json = request.get_json()
    print('获取request_json')
    if not request_json:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    house_id = request_json.get('house_id')
    start_date = request_json.get('start_date')
    end_date = request_json.get('end_date')
    if not all([house_id, start_date, end_date]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 日期格式检查
    try:
        # 将请求的时间参数字符串转换为datetime类型
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        assert start_date <= end_date
        # 机算预定天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期格式错误')

    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房屋信息失败')

    if not house:
        return jsonify(errno=RET.DBERR, errmsg='房屋不存在')

    # 预定的房屋是否是房东自己的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='不能预定自己的房屋')

    # 确保用户预定的时间内，房屋没有被别人下单
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='检查出错,请稍后重试')

    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg='房屋已经被预定了')

    # 订单金额
    amount = days * house.price
    # 保存订单数据
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存订单失败')

    return jsonify(errno=RET.OK, errmsg='OK', data={'order_id':order.id})

@api.route('/users/orders', methods=['GET'])
@login_required
def get_user_orders():
    '''查询用户的订单信息'''
    user_id = g.user_id
    # 用户的身份，用户想要查询作为房客预定别人房子的订单，还是想要作为房东查询别人预定自己房子的订单
    role = request.args.get('role', '')

    # 查询订单数据
    try:
        if role == 'landlord':
            # 以房东的身份查询订单
            # 先查询属于自己的房子有哪些
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            # 在查询预定了自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc())
        else:
            # 以房客的身份查询订单，查询自己预定的订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询订单失败')

    # 将订单对象转换为字典数据
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg='OK', data={'orders':orders_dict_list})

@api.route('/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    '''接单、拒单'''
    user_id = g.user_id
    request_json = request.get_json()
    if not request_json:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # action参数表明用户端请求的是接单还是拒单的行为
    action = request_json.get('action')
    if action not in ('accept', 'reject'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')

    if action == 'accept':
        # 接单，将订单的状态设置为等待评论
        order.status = 'WAIT_PAYMENT'

    if action == 'reject':
        # 拒单，要求用户传递拒单原因
        reason = request_json.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        order.status = 'REJECTED'
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    return jsonify(errno=RET.OK, errmsg='OK')

@api.route('/orders/<int:order_id>/comment', methods=['PUT'])
@login_required
def save_order_comment(order_id):
    '''保存订单评论信息'''
    user_id = g.user_id
    request_json = request.get_json()
    comment = request_json.get('comment')
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        # 需要确保只能评论自己下的订单，而且订单处于待评价状态才可以
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == 'WAIT_COMMENT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')

    try:
        # 将订单状态设置为已完成
        order.status = 'COMPLETE'
        # 保存订单的评论信息
        order.comment = comment
        # 将房屋的完成订单数加一
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    house_info_id = 'house_info_%s' % house.id
    # 因房屋详情中有订单的评论信息，为了让最新的评论信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
    try:
        redis_store.delete(house_info_id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')



















