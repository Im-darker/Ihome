from datetime import datetime

from flask import request, g
from flask import session

from Ihome.models import Area, House, Facility, HouseImage, User, Order
from Ihome.utils import constants
from Ihome.utils.commons import login_required
from Ihome.utils.image_storage import storage
from Ihome.utils.response_code import RET
from . import api
from flask import jsonify, current_app, json
from Ihome import redis_store, db


@api.route("/areas")
def get_area_info():
    """获取城区信息"""
    try:
        # 先查询redis缓存,如果没有再从数据库查询
        area_li = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询出错")

    if area_li:
        # 用日志记录一下命中redis缓存
        current_app.logger.error("成功击中redis缓存")
        return area_li, 200, {"Content-Type": "application/json"}

    # 查询数据
    try:
        area_list = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 把数据集对象转化为单个的字典对象
    area_dict_list = []
    for area in area_list:
        area_dict_list.append(area.to_dict())

    response_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_list)
    response_json = json.dumps(response_dict)
    # 把数据保存到redis缓存中
    try:
        redis_store.setex("area_info", constants.AREA_INFO_TIME, response_json)
    except Exception as e:
        current_app.logger.error(e)

    return response_json, 200, {"Content-Type": "application/json"}


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房源基本信息"""
    # 获取数据

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

    # 检验参数
    if not all([title,price,area_id,address,room_count,acreage,unit,
                             capacity,beds,deposit,min_days,max_days]):

        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="数据不存在")

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
    # try:
    #     db.session.add(house)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据保存错误")
    #
    # 处理房屋设施
    facility_ids = house_data.get("facilities")

    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

        # 表示填写的设施是正确的存在的并保存数据！
        if facilities:
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        # 事务回滚
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存错误")

    # 保存数据成功
    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片
    参数 图片 房屋的id
    """
    image_file = request.files.get("house_image")
    # 多媒体表单传参
    house_id = request.form.get("house_id")

    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断house_id正确性
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:  # if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    image_data = image_file.read()
    # 保存图片到七牛中
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    # 保存图片信息到数据库中
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    # 处理房屋的主图片
    if not house.index_image_url:


        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    image_url = constants.QI_NIU_URL + file_name

    return jsonify(errno=RET.OK, errmsg="OK", data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_home():
    """获取房东的房屋列表"""
    user_id = g.user_id

    # 从数据库中获取用户的房屋列表数据
    try:
        # user = User.query.filter_by(id=user_id).first()
        user = User.query.get(user_id)
        print(user)
        houses = user.houses
        print(houses)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    # 把数据对象转换成字典格式的列表数据
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_dict())

    # 转成json格式　如：　"data":[{},{},{}]
    print(houses_list)
    house_data = json.dumps(houses_list)
    print(house_data)

    # return '{"errno": "0", "errmsg": "OK", "data": "%s"}' % house_data, 200, {"Content-Type": "application/json"}
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": house_data})


@api.route("/houses/index", methods=["GET"])
def get_home_index():
    """
    获取首页图片展示
    参数：index_image_url,　　　
    """
    # 从缓存中获取数据
    try:
        image_list = redis_store.get("home_page_image")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据获取错误")

    if image_list:
        return '{"errno": 0, "errmsg": "OK", "data": %s}' % image_list, 200, {"Content-Type": "application/json"}

    # 缓存理没有数据,从数据库里获取
    try:
        # 以订单量最多房屋图片来作为首页图片推荐
        home_list = House.query.order_by(House.order_count.desc()).limit(constants.home_page_max)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if home_list is None:
        return jsonify(errno=RET.NODATA, errmsg="无数据")

    # 把图片对象转换成一个个字典数据
    home_json_list = []
    for home in home_list:
        # 如果该房子没有设置过主页图片则跳过
        if home.index_image_url is None:
            continue
        home_json_list.append(home.to_dict())

    # 把字典数据转换成json格式
    home_json_data = json.dumps(home_json_list)

    # 把数据保存到redis缓存中
    try:
        redis_store.setex("home_page_image", constants.HOME_PAGE_CACHE_TIME, home_json_data)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno:"0", "errmsg":"ok", "data": %s}' % home_json_data, 200, \
           {"Content-Type": "application/json"}


# --------------------------------------------------------------------------------------------------------------------
@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("击中缓存")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), \
               200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_LIST_CACHE_DATA_TIME, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), \
           200, {"Content-Type": "application/json"}
    return resp


# GET /api/v1.0/houses/houses?sd=xxxx&ed=xxxxx&aid=xxxx&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """获取搜索的房屋列表数据"""
    # 获取参数
    start_date = request.args.get("sd")
    end_date = request.args.get("ed")
    area_id = request.args.get("aid")
    sort_key = request.args.get("sk", "new")
    page = request.args.get("p", "1")

    # 校验参数
    try:

        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数错误")

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 尝试从缓存中获取数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)

    try:
        response_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)

    else:
        if response_json:
            return response_json, 200, {"Content-Type": "application"}


    # 过滤时间条件
    # 设置过滤条件的容器
    filter_params_list = []
    # 设置冲突的订单为None
    conflict_order = None

    try:
        if start_date and end_date:
            conflict_order = Order.query.filter(end_date >= Order.begin_date, start_date <= Order.end_date).all()

        elif start_date:
            conflict_order = Order.query.filter(start_date <= Order.end_date).all()

        elif end_date:
            conflict_order = Order.query.filter(end_date >= Order.begin_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if conflict_order:
        # 获取冲突的房屋id
        conflict_houseids = [order.house_id for order in conflict_order]

        if conflict_houseids:
            # 获取可预定的房屋id
            houseids = House.query.filter(House.id.notin_(conflict_houseids))
            filter_params_list.append(houseids)

    # 地区条件   过滤不正确的地区
    if area_id:
        filter_params_list.append(House.area_id == area_id)

    # 先通过过滤条件得到想要的数据再进行各种方式排序
    # 各种条件进行排序
    if sort_key == "booking":
        houseids = House.query.filter(*filter_params_list).order_by(House.order_count.desc())

    elif sort_key == "price-inc":
        houseids = House.query.filter(*filter_params_list).order_by(House.price.asc())

    elif sort_key == "price-des":
        houseids = House.query.filter(*filter_params_list).order_by(House.price.desc())

    else:
        houseids = House.query.filter(*filter_params_list).order_by(House.create_time.desc())

    # 进行分页处理
    # paginate(page=想要返回第几页 默认第一页, per_page=按多少数据进行分页，默认20条,  error_out=查询的页面超出总页数是否要抛出异常, 默认True )
    try:
        # 得到一个分页后的数据对象
        page_object = houseids.paginate(page=page, per_page=constants.HOUSE_PAGE_MAX_NUMBER, error_out=False)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.UNKOWNERR, errmsg="分页出现异常")

    # 获取每一页的数据
    house_list = page_object.items
    houses = []

    for house in house_list:
        houses.append(house.to_det_dict())

    # 获取总页数
    total_pages = page_object.pages

    response_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_pages,
                              "houses": houses, "current_page": page})

    response_json = json.dumps(response_dict)

    # 设置redis缓存数据,以查询日期+地区id+排序作为key
    if page <= total_pages:
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)

        try:
            # 获取管道对象, 可以存储多个执行命令
            pipeline = redis_store.pipeline()
            # 开启事务
            pipeline.multi()
            # 加入缓存
            pipeline.hset(redis_key, page, response_json)
            # 设置有效期
            pipeline.expire(redis_key, constants.HOUSE_LIST_CACHE_DATA_TIME)

            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return response_json, 200, {"Content-Type": "application/json"}











































