import time
import requests

from myRedis import RedisClient
from sqlalchemy import create_engine, Column, String, Integer, BigInteger, DateTime, DECIMAL, SmallInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from sql import Phone

# 定义映射类的基类
Base = declarative_base()

class APIClient:
    # 创建数据库连接
    engine = create_engine('mysql://root:root@124.70.70.96:3306/keaimao')
    Base.metadata.create_all(engine)  # 创建表
    # 创建Session类实例
    Session = sessionmaker(bind=engine)  # 注意这里的改动
    def __init__(self):
        self.base_url = "http://api.haozhuma.com"
        self.token = None

    def login(self, username, password):
        url = f"{self.base_url}/sms/"
        params = {
            "api": "login",
            "user": username,
            "pass": password
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                print("登录成功")
                self.token = data['token']
            else:
                print(f"登录失败: {data['msg']}")
        else:
            print(f"请求失败，HTTP 状态码: {response.status_code}")

    def get_token(self,my_wxid):
        session = self.Session()
        try:
            phone = session.query(Phone).filter_by(my_wxid=my_wxid).one_or_none()
            # 检查 user 是否为 None，如果是，则将 credits 设置为 0
            if phone is not None:
                self.login(phone.user,phone.password)
        finally:
            session.close()
        if self.token is not None:
            redis = RedisClient()
            redis.set_key_value_with_expiry(my_wxid,self.token,86400)
        return self.token
    def get_robot_token(self):
        session = self.Session()
        try:
            phone = session.query(Phone).filter_by(my_wxid='wxid_3eb3mapikc8i12').one_or_none()
            # 检查 user 是否为 None，如果是，则将 credits 设置为 0
            if phone is not None:
                self.login(phone.user,phone.password)
        finally:
            session.close()
        if self.token is not None:
            redis = RedisClient()
            redis.set_key_value_with_expiry('wxid_3eb3mapikc8i12',self.token,86400)
        return self.token

    import requests
    def get_redis_token(self,my_wxid):
        redis = RedisClient()
        token = redis.get_value_by_key(my_wxid)
        if token == None:
            token = self.get_token(my_wxid);
        return token
    def get_redis_robot_token(self):
        redis = RedisClient()
        token = redis.get_value_by_key('wxid_3eb3mapikc8i12')
        if token == None:
            token = self.get_robot_token();
        return token

    def get_phone(self, my_wxid,phone, author=None):
        url = "http://api.haozhuma.com/sms/"
        token = self.get_redis_token(my_wxid)
        params = {
            "api": "getPhone",
            "token": token,
            "sid": 57118,
            "phone": phone
        }
        if author:
            params["author"] = author

        response = requests.get(url, params=params)  # 或者使用 POST 方法
        if response.status_code == 200:
            data = response.json()
            if data['code'] == "0":
                print("请求成功")
                verification =  self.get_verification_code(my_wxid,phone)
                return verification
            else:
                print(f"请求失败: {data['msg']}")
        else:
            print(f"请求失败，HTTP 状态码: {response.status_code}")
        return None

    def get_verification_code(self,my_wxid, phone):
        url = "http://api.haozhuma.com/sms/"
        token = self.get_redis_token(my_wxid)
        params = {
            "api": "getMessage",
            "token": token,
            "sid": 57118,
            "phone": phone
        }

        start_time = time.time()  # 获取开始时间的时间戳
        timeout = 120  # 设定超时时间，比如60秒

        while time.time() - start_time < timeout:
            response = requests.get(url, params=params)  # 或 POST
            if response.status_code == 200:
                data = response.json()
                if data['code'] == "0":
                    print("验证码 : "+str(data['yzm']))
                    return data['yzm']
                else:
                    print(f"尝试获取验证码失败: {data['msg']}")
            else:
                print(f"请求失败，HTTP 状态码: {response.status_code}")

            time.sleep(5)  # 每隔5秒重新尝试

        #todo 这里后面给用户一个提示,超时未获取
        print("超时未能获取验证码")
        return None

    def get_phones(self):
        url = "http://api.haozhuma.com/sms/"
        token = self.get_redis_robot_token()
        params = {
            "api": "getPhone",
            "token": token,
            "sid": 73685
        }

        response = requests.get(url, params=params)  # 或 POST
        if response.status_code == 200:
            data = response.json()
            if data['code'] == "0":
                print("手机号 : "+str(data['phone']))
                return data['phone']
            else:
                print(f"尝试获取验证码失败: {data['msg']}")
        else:
            print(f"请求失败，HTTP 状态码: {response.status_code}")
