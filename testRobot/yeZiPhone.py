import time
import requests

from myRedis import RedisClient
from sqlalchemy import create_engine, Column, String, Integer, BigInteger, DateTime, DECIMAL, SmallInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from sql import Phone

class YeZiPhoneClient:

    def __init__(self):
        self.base_url = "http://api.sqhyw.net:90/api"
        self.token = None

    def login(self, username, password):
        url = f"{self.base_url}/logins"
        params = {
            "username": username,
            "password": password
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                print("登录成功")
                self.token = data['token']
                return self.token
            else:
                print(f"登录失败: {data['msg']}")
        else:
            print(f"请求失败，HTTP 状态码: {response.status_code}")
            #http: // api.sqhyw.net: 90 / api / get_mobile?token = 你的token & project_id = 专属项目对接码

    def get_phone(self, author=None):
        url = f"{self.base_url}/get_mobile"
        token = self.utf8_to_gb2312(self.get_redis_token())
        project_id = self.utf8_to_gb2312('744909')
        special = self.utf8_to_gb2312('1')
        params = {
            "token": token,
            "project_id": project_id,
            "special": special
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['message'] == "ok":
                print("请求成功")
                return data['mobile']
            else:
                print(f"请求失败: {data['msg']}")
        else:
            print(f"请求失败，HTTP 状态码: {response.status_code}")
        return None

    def get_message(self,phone, author=None):
        url = f"{self.base_url}/get_message"
        token = self.get_redis_token()
        params = {
            "token": token,
            "project_id": "764482",
            "special": '1',
            "phone_num": phone,
        }
        time.sleep(5)  # 5秒后执行第一次获取

        start_time = time.time()  # 获取开始时间的时间戳
        timeout = 60  # 设定超时时间，比如60秒

        while time.time() - start_time < timeout:

            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['message'] == "ok":
                    print("请求成功")
                    self.add_blacklist(phone)
                    return data['code']
                else:
                    print(f"请求失败: {data['msg']}")
            else:
                print(f"请求失败，HTTP 状态码: {response.status_code}")
            time.sleep(5)  # 每隔5秒重新尝试
        # todo 这里后面给用户一个提示,超时未获取
        self.add_blacklist(phone)
        print("超时未能获取验证码")
        return None

    #拉黑
    def add_blacklist(self,phone, author=None):
        url = f"{self.base_url}/get_message"
        token = self.get_redis_token()
        params = {
            "token": token,
            "project_id": "764482",
            "special": '1',
            "phone_num": phone,
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['message'] == "ok":
                print("拉黑成功")
            else:
                print(f"拉黑失败: {data['message']}")
        else:
            print(f"拉黑失败，HTTP 状态码: {response.status_code}")



    def get_redis_token(self):
        redis = RedisClient()
        token = redis.get_value_by_key('wxid_3eb3mapikc8i12')
        if token == None:
            token = self.login()
        if self.token is not None:
            redis = RedisClient()
            redis.set_key_value_with_expiry('wxid_3eb3mapikc8i12',self.token,86400)
        return token

    def utf8_to_gb2312(self, utf8_str):
        try:
            gb2312_str = utf8_str.encode('utf-8').decode('latin1').encode('gb2312')
            return gb2312_str
        except UnicodeEncodeError:
            print("Encoding conversion error")
            return None





