from . import api
from datetime import datetime
from flask import current_app, jsonify, request, g, session
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome.utils.response_code import RET
import json
from ihome.utils.fdfs.storage import FdfsStorage
from ihome.utils.commons import login_required
from ihome import redis_store, constants, db

@api.route('/areas', methods=['GET'])
def get_area_info():
    '''获取城区信息'''
    #尝试从redis中读取数据
    try:
        data_json = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
    else:
        if data_json is not None:
            # redis有缓存数据
            current_app.logger.info('从redis中读取缓存')
            return data_json, 200, {'Content-Type': 'application/json'}

    # 查询数据库，读取城区信息
    try:
        # 返回的是一个area对象的列表
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_li_dict = []
    # 将对象转换为字典
    for area in area_li:
        area_li_dict.append(area.to_dict())

    # 将要返回的值放进字典中，并转换为json字符串
    data_dict = dict(errno=RET.OK, errmsg='OK', data=area_li_dict)
    data_json = json.dumps(data_dict)

    # 将数据保存到redis中
    try:
        redis_store.setex('area_info', constants.AREA_INFO_REDIS_CACHE_EXPIRES, data_json)
    except Exception as e:
        current_app.logger.error(e)

    return data_json, 200, {'Content-Type':'application/json'}

@api.route('/houses/info', methods=['POST'])
@login_required
def save_house_info():
    '''保存房屋的基本信息
    前端发送过来的json数据
    {
        "title": "",
        "price": "",
        "area_id": "1",
        "address": "",
        "room_count": "",
        "acreage": "",
        "unit": "",
        "capacity": "",
        "beds": "",
        "deposit": "",
        "min_days": "",
        "max_days": "",
        "facility": ["7", "8"]
    }
    '''
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验参数
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return  jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 单价和押金校验
    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return  jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg='城区信息有误')

    # 参数校验过多，就不校验那么多了
    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # print('the first time add')
    # db.session.add(house)

    # 处理房屋的设施信息
    facility_ids = house_data.get('facility')
    print(facility_ids)

    # print('-'*50)
    # 如果用户勾选了设施信息，保存信息到数据库
    if facility_ids:
        try:
            print('+'*50)
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            # print('-'*50)
            print(facilities)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='保存数据异常')

        # print('-'*50)
        if facilities:
            # 保存有合法设施的数据
            # 保存设施数据
            print('开始执行house.facilities = facilities')
            house.facilities = facilities
            print('结束执行house.facilities = facilities')
            # db.session.add(house)
            # print('the second time add')

    # print('-'*50)
    try:
        print('start add')
        db.session.add(house)
        print('end add')
        print('start commit')
        db.session.commit()
        print('end commit')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    return jsonify(errno=RET.OK, errmsg='OK', data={'house_id':house.id})


@api.route('/houses/image', methods=['POST'])
@login_required
def save_house_image():
    '''保存房屋图片'''
    user_id = g.user_id

    image_file = request.files.get('house_image')
    # print(image_file)
    house_id = request.form.get('house_id')
    # print(house_id)

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断house_id的正确性
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    image_data = image_file.read()
    # print(image_data)
    # 上传图片
    try:
        fdfs_storage = FdfsStorage()
        file_name = fdfs_storage.upload(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')

    # 保存图片信息到数据库中
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 处理房屋的主页图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片数据异常')

    image_url = constants.FDFS_BASE_URL + file_name
    return jsonify(errno=RET.OK, errmsg='OK', data={'image_url':image_url})

@api.route('/users/houses', methods=['GET'])
@login_required
def get_user_houses():
    '''获取房东发布的房源信息条目'''
    user_id = g.user_id
    # 从数据库中读取出对应房东的所有房源信息
    try:
        # 查询房屋信息方法1
        houses = House.query.filter_by(user_id=user_id).all()
        # 查询方法2
        # user = User.query.get(user_id)
        # houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 将查询到的房屋信息转换为字典存放到字典列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg='OK', data={'houses':houses_list})

@api.route('/houses/index', methods=['GET'])
def get_houses_index():
    '''获取主页幻灯片展示的房屋基本信息'''
    # 从缓存中尝试读取数据
    try:
        ret = redis_store.get('home_page_data')
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        # 因为从redis中读取出来的是json字符串，所以直接进行字符串拼接并返回
        current_app.logger.info('从redis中读取缓存')
        response_json = '{"errno":"0", "errmsg":"OK", "data":%s}' % ret
        return response_json, 200, {'Content-Type': 'application/json'}
    else:
        # 无法从redis中读取数据，从数据库中读取数据
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg='查询无数据')

        houses_list = []
        for house in houses:
            # 如果房屋未设置主页图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json,并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex('house_page_data', constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        response_json = '{"errno":"0", "errmsg":"OK", "data":%s}' % json_houses
        return response_json, 200, {'Content-Type':'application/json'}


@api.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    '''获取房屋详情'''
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示
    # 所以需要后端向前端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id,否则返回user_id为-1
    print('接收到请求')
    user_id = session.get('user_id', '-1')

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    # 先从redis缓存中读取信息
    house_info_id = 'house_info_%s' % house_id
    try:
        ret = redis_store.get(house_info_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        current_app.logger.info('从redis中读取缓存信息')
        response_json = '{"errno":"0", "errmsg":"OK", "data":{"house":%s, "user_id":%s}}' % (ret, user_id)
        return response_json, 200, {'Content-Type':'application/json'}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据出错')

    # 存入redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex(house_info_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)


    response_json = '{"errno":"0", "errmsg":"OK", "data":{"house":%s, "user_id":%s}}' % (json_house, user_id)

    return  response_json, 200, {'Content-Type':'application/json'}

@api.route('/houses', methods=['GET'])
def get_house_list():
    '''获取房屋的列表信息(搜索页面)'''
    start_date = request.args.get('sd', '')     # 用户想要的起始时间
    end_date = request.args.get('ed', '')       # 用户想要的结束时间
    area_id = request.args.get('aid', '')       # 区域编号
    sort_key = request.args.get('sk', 'new')    # 排序关键字
    page = request.args.get('p')        # 页数

    # 处理时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')

    # 区域编号处理
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='区域参数有误')

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 从缓存中读取信息
    houses_search_coache = 'house_%s_%s_%s_%s' % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(houses_search_coache, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json, 200, {'Content-Type': 'application/json'}

    # 过滤条件的参数列表容器
    filter_params = []

    # 时间条件
    conflict_orders = None
    try:
        if start_date and end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if conflict_orders:
        # 从订单获取房屋id
        conflict_house_list = [order.house_id for order in conflict_orders]
        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_list:
            filter_params.append(House.id.notin_(conflict_house_list))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 补充排序条件
    if sort_key == 'booking':   # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == 'price-des':
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    try:
    #                               当前页数        每页数据量                                   自动输出错误
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    # 获取页面数据
    house_list = page_obj.items
    houses = []
    for house in house_list:
        houses.append(house.to_basic_dict())

    # 获取页面数据
    total_page = page_obj.pages

    resp_data = dict(errno=RET.OK, errmsg='OK', data={'total_page':total_page, 'houses':houses, 'current_page':page})
    resp_json = json.dumps(resp_data)

    if page <= total_page:
        # 设置缓存数据
        try:
            # 使用哈希类型
            # redis_store.hset(houses_search_coache, page, resp_json)
            # redis_store.expire(houses_search_coache, constants.HOME_PAGE_DATA_REDIS_EXPIRES)
            # 使用redis的pipeline可以同时执行多个redis语句，同时成功，同时失败，相当于mysql中的事务
            # 创建管道对象，可以一次执行多个语句
            pipeline = redis_store.pipeline()
            # 开启多个语句的记录
            pipeline.multi()

            pipeline.hset(houses_search_coache, page, resp_json)
            pipeline.expire(houses_search_coache, constants.HOME_PAGE_DATA_REDIS_EXPIRES)

            # 执行语句
            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {'Content-Type':'application/json'}

































