import json
import os
import time
from decimal import Decimal, ROUND_HALF_UP
import sql
from flask import Flask, request, send_file
import requests
from sqlalchemy import create_engine, Column, String, Integer, BigInteger, DateTime, DECIMAL, SmallInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

import pymysql

from myRedis import RedisClient
from phone import APIClient
from sql import UsePhone,User

app = Flask(__name__)

# 定义映射类的基类
Base = declarative_base()

class Robot:
    # 创建数据库连接
    engine = create_engine('mysql://root:root@124.70.70.96:3306/keaimao')
    Base.metadata.create_all(engine)  # 创建表
    # 创建Session类实例
    Session = sessionmaker(bind=engine)  # 注意这里的改动
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Robot, cls).__new__(cls)
        return cls._instance

    def __init__(self, host='192.168.31.45', port=8090):
    #def __init__(self, host='47.106.211.207', port= 1010):
        self.host = host
        self.port = port
        self.authorization_file = './authorization.txt'
        self.authorization = self.get_authorization()
        self.robot_master = ['sundreamer']
        self.events = {
            "EventFriendMsg": lambda msg: self.handle_private_message(msg),  # 朋友发消息事件
            "EventReceivedTransfer": lambda transfer: self.handle_received_transfer(transfer),  # 收到转账事件
            "EventSendOutMsg": lambda msg: self.myself(msg),  # 自己发给别人的事件
        }




        self.push_events = {
            "SendTextMsg": lambda params: self.send_text_message(params),  # 发送文本消息
            "AcceptTransfer": lambda params: self.accept_transfer(params),  # 接收好友转账
        }
        self.menu = {
            # "查询余额,查询库存,新电途,二次取码:xxxx(xxxx是具体的电话号码)"
            "菜单": lambda request: self.menus(request),
            "新电途": lambda request: self.xdt(request),
            "查询余额": lambda request: self.remaining(request),
            "查询库存": lambda request: self.repertory(request),
            "充值:": lambda request: self.save(request)
        }
        self.msg = {
           "A": "查询余额\r\n 查询库存\r\n 新电途",
           "B": "积分增加成功 \r\n 当前可用积分：",
           "C": "\r\n 开始获取验证码... \r\n 请在两分钟内打开小程序输入手机号获取验证码",
           "D": "验证码已到达,账号售后时间1小时 \r\n 当前可用积分：",
           "E": "积分增加成功 \r\n 当前可用积分：",
           "F":  "取号积分为4.5 \r\n 1元=1积分 \r\n 直接转账即可预存积分",
           "G": "积分余额:",
           "H": "库存余量:",
           "I": "库存暂时不足,正在以最快速度补上库存,请客官稍等~",
           "J": "获取验证码超时,积分已退回.",
           "K": "余额不足以获取号码\r\n当前剩余积分: ",
           "L": "您的充值金额大于50,已自动为您增加20%当前所充值的金额\r\n当前剩余积分: ",
           "M": "您的充值金额大于20,已自动为您增加10%当前所充值的金额\r\n当前剩余积分: ",
           "N": "充值成功\r\n当前剩余积分: ",
           "O": "教程: \r\n 给我发送 菜单  我会给您提供目前的功能列表 \r\n 直接给我转账,1元=1积分 \r\n 想要获取优惠券账号时,请给我发送 新电途 \r\n  在 微信/支付宝中搜索 新电途 \r\n 如果当前有登录账号,请把当前登录的账号退掉,重新点击登录,会出现2个选项,选择下面灰色的按钮 使用其他手机号码登录 \r\n 把我提供给你的手机号码输入到小程序里, 点击获取验证码. 等待10~20秒我会给你验证码. 登录进去就可以使用啦.\r\n 当前活动: 单5号 新用户第一单1.4积分 后续2积分",
           "P": "此功能维护中",
           "Q": "加号成功\r\n号码 : "
        }

    def get_authorization(self):
            if os.path.isfile(self.authorization_file):
                with open(self.authorization_file, 'r') as file:
                    return file.read().strip()
            else:
                return ''

    def set_authorization(self, authorization):
            with open(self.authorization_file, 'w') as file:
                file.write(authorization)
            self.authorization = authorization

    def send_http(self, params, url=None, headers=None, method='post', timeout=3, no=1):
        url = url or f'http://{self.host}:{self.port}'
        try:
            response = requests.post(url, json=params, headers=headers, timeout=timeout)
            response_data = response.json()  # 正确调用json()方法
            print(response_data)
            # 检查response_data是否有错误消息
            if response_data.get('code') == -1 and response_data.get('msg') == '数据格式化错误':
                raise ValueError('数据格式化错误')  # 抛出自定义异常
            response.raise_for_status()  # 检查其他HTTP错误
            return response_data
        except ValueError as e:
            # 捕获数据格式化错误
            print(f"Custom error caught: {e}")
            if no <= 5:
                no += 1
                # 传递正确的参数
                return self.send_http(params, url, headers, method, timeout, no)
            # 可以在这里添加额外的错误处理逻辑
            return str(e)
        except Exception as e:
            # 捕获其他所有异常
            print(f"An error occurred: {e}")
            return str(e)


    def response(self, request):

            redis = RedisClient()
            redis_value = redis.get_value_by_key('MSG_'+request.get('from_wxid'))
            if redis_value is None:
                self.pushMsg(request, self.msg.get("O"))
                redis.set_key_value_with_expiry('MSG_'+request.get('from_wxid'),1,86400)

            # 获取请求中的事件类型
            event_type = request.get('event')

            # 检查事件类型是否在 slf.events 字典中
            if event_type in self.events:
                # 调用相应的事件处理函数
                return self.events[event_type](request)
            else:
                # 处理未知事件类型的情况
                print(f"Unknown event type: {event_type}")
                # 可以返回一个错误信息或者进行其他的错误处理

    def pushMsg(self,json,msg):
        response_data = {
            "success": True,
            "event": "SendTextMsg",
            "type": 1,
            "to_wxid": json.get('from_wxid', ''),
            "msg": msg,
            "robot_wxid": json.get('robot_wxid', '')
        }
        self.send_http(response_data, None, None)

    #自我触发事件 发送给对方
    def myPushMsg(self,json,msg):
        response_data = {
            "success": True,
            "event": "SendTextMsg",
            "type": 1,
            "to_wxid": json.get('to_wxid', ''),
            "msg": msg,
            "robot_wxid": json.get('robot_wxid', '')
        }
        self.send_http(response_data, None, None)

    def pushMoneyMsg(self,json):
        response_data = {
            "success": True,
            "event": "AcceptTransfer",
            "type": 2000,
            "to_wxid": json.get('from_wxid', ''),
            "msg": json.get('msg', ''),
            "robot_wxid": json.get('robot_wxid', '')
        }
        self.send_http(response_data, None, None)


    def handle_private_message(self, msg):
        # 检查请求是否以 "二次取码:" 开头

        if 1 == 2:
            phone_number = msg.get('msg').split("充值:")[1]
            return self.verification(msg, phone_number)
        # 对于其他类型的请求
        elif msg.get('msg') in self.menu:
            return self.menu[msg.get('msg')](msg)
        else:
            print("未知命令，请重新输入。")

            return self.menu[msg.get('msg')](msg)

    def verification(self, request, phone_number):
        #二次取码,根据 用户微信id,与发送来的手机号,并且收码次数为1的, 提供第二次验证码发送服务,否则不做任何处理.
        self.pushMsg(request, self.msg.get("G"))
        pass

    def menus(self, request):
        #菜单栏, 直接返回当前菜单信息即可
        self.pushMsg(request,self.msg.get("A"))
        pass

    def remaining(self, request):
        # 使用

        self.remainings(request)


    def remainings(self, request):
        user_id = request.get('from_wxid')
        session = self.Session()
        try:
            user = session.query(User).filter_by(to_wxid=user_id).one_or_none()
            # 检查 user 是否为 None，如果是，则将 credits 设置为 0
            if user is None or user.credits is None:
                user_credits = 0
            else:
                user_credits = user.credits
            self.pushMsg(request, self.msg.get("G")+str(user_credits))
        finally:
            session.close()

    def repertory(self, request):
        robot_wxid = request.get('robot_wxid')
        session = self.Session()
        try:
            user = session.query(UsePhone).filter_by(my_wxid=robot_wxid).filter_by(type=0).count()
            # 检查 user 是否为 None，如果是，则将 credits 设置为 0
            if user is None:
                user_credits = 0
            else:
                user_credits = user
            self.pushMsg(request, self.msg.get("H") + str(user_credits))
        finally:
            session.close()

    def xdt(self, request):
        robot_wxid = request.get('robot_wxid')
        session = self.Session()
        try:
            user = session.query(UsePhone).filter_by(my_wxid=robot_wxid).filter_by(type=0).first()
            # 检查 user 是否为 None，如果是，则将 credits 设置为 0
            if user is None:
                # 库存不足,请等待补库存.
                self.pushMsg(request, self.msg.get("I"))
                return
            user.type = 1
            user.num = 1
            session.commit()
            #用户积分
            users = session.query(User).filter_by(to_wxid=request.get('from_wxid')).one_or_none()
            if users is None:
                user_credits = 0
                user.type = 0
                user.num = 0
                session.commit()
                self.pushMsg(request, self.msg.get("K")+str(user_credits))
                return
            else:
                 if users.is_first == 0:
                     money = users.credits - Decimal(1.4)
                     # 四舍五入到两位小数
                     rounded_money = money.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                     if rounded_money < 0:
                         user.type = 0
                         user.num = 0
                         session.commit()
                         self.pushMsg(request, self.msg.get("K") + users.credits)
                         return
                     else:
                         user.money = Decimal(1.4)
                 else:
                     money = users.credits - Decimal(2.0)
                     rounded_money = money.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                     if rounded_money < 0:
                        user.type = 0
                        user.num = 0
                        session.commit()
                        self.pushMsg(request, self.msg.get("K") + users.credits)
                        return


            self.pushMsg(request, str(user.phone) + self.msg.get("C"))
            self.pushMsg(request, self.msg.get("G") + str(rounded_money))
            phone=user.phone
            # 获取验证码.
            apiClient=APIClient()
            verification_code = apiClient.get_phone(robot_wxid,phone,author=None)
            if verification_code is None:
                user.type = 1
                session.commit()
                self.pushMsg(request, str(user.phone) + self.msg.get("J"))
                self.pushMsg(request, self.msg.get("G") + str(users.credits))
            else:
                user.my_wxid = robot_wxid
                user.use_vx_user_id = request.get('from_wxid')
                user.money = Decimal(2.0)
                users.is_first = 1
                users.credits = rounded_money
                session.commit()
                self.pushMsg(request,str(verification_code))
                self.pushMsg(request, self.msg.get("D")+str(users.credits))
        except Exception as e:
            user.type = 0
            user.num = 0
            session.commit()
            print(e)
        finally:
            session.close()

    def handle_received_transfer(self, transfer):
        #收到转账后,收款,并且给当前用户加对应积分,并且返回一些提示语.
        robot_wxid = transfer.get('robot_wxid')
        user_id = transfer.get('from_wxid')
        money = transfer.get('money')
        session = self.Session()
        self.pushMoneyMsg(transfer)

        money = Decimal(money)
        try:
            user = session.query(User).filter_by(to_wxid=user_id).filter_by(my_wxid=robot_wxid).one_or_none()
            # # 如果金额大于特定值，则增加对应的百分比
            # if money >= Decimal('50'):
            #     money += money * Decimal('0.20')  # 增加20%
            # elif money >= Decimal('20'):
            #     money += money * Decimal('0.10')  # 增加10%

            if user is None:
                user = User()
                user.to_wxid = user_id
                user.my_wxid = robot_wxid
                user.credits = money
                user.is_first = 0
                session.add(user)
            else:
                user.credits = user.credits+money
            # if money >= Decimal('50'):
            #     self.pushMsg(transfer, self.msg.get("L")+str(money))
            # elif money >= Decimal('20'):
            #     self.pushMsg(transfer, self.msg.get("M") + str(money))
            # elif money < Decimal('20'):
                self.pushMsg(transfer, self.msg.get("N") + str(user.credits))
            session.commit()
        except Exception as e:
            print(e)
        finally:
            session.close()
        pass

    #给用户手动充值
    def save(self, request,number):
        robot_wxid = request.get('robot_wxid')
        user_id = request.get('to_wxid')
        session = self.Session()
        try:
            user = session.query(User).filter_by(to_wxid=user_id).filter_by(my_wxid=robot_wxid).one_or_none()

            if user is None:
                user = User()
                user.to_wxid = user_id
                user.my_wxid = robot_wxid
                user.credits = Decimal(number)
                user.is_first = 0
                session.add(user)
                self.myPushMsg(request, self.msg.get("B") + number)
            else:
                user.credits = user.credits + Decimal(number)
                self.myPushMsg(request, self.msg.get("B") + str(user.credits))
            session.commit()
        finally:
            session.close()

    def savePhone(self, msg, number):
        robot_wxid = msg.get('robot_wxid')
        session = self.Session()
        try:
            usePhone = UsePhone()
            usePhone.phone = number
            usePhone.my_wxid = robot_wxid
            usePhone.type = 0
            usePhone.num = 0
            session.add(usePhone)
            self.myPushMsg(msg, self.msg.get("Q") + number)
            session.commit()
        finally:
            session.close()


    def myself(self, msg):
        if msg.get('msg', '').startswith("充值:"):
            number = msg.get('msg').split("充值:")[1]
            return self.save(msg, number)
        elif msg.get('msg', '').startswith("加号:"):
            number = msg.get('msg').split("加号:")[1]
            return self.savePhone(msg, number)
        pass
        pass




@app.route('/', methods=['POST'])
def index():
    data = request.get_json()
    print("Received request parameters:", data)
    robot = Robot()
    return json.dumps(robot.response(data))


@app.route('/remote', methods=['GET', 'POST'])
def remote():
    # 实现 remote 功能
    pass


@app.route('/down', methods=['GET'])
def down():
    # 实现文件下载功能
    filepath = request.args.get('filepath', './favicon.ico')
    if not os.path.exists(filepath):
        return json.dumps({'success': False, 'message': 'file not found!'}), 404
    return send_file(filepath, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)
