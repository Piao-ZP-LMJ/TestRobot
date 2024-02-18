import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By

from phone import APIClient
from yeZiPhone import YeZiPhoneClient


class AndroidRobot:

    def test_driver(self):
        capabilities = {
            'platformName': 'Android',
            'platformVersion': '14',
            'deviceName': '127.0.0.1:5554',
            'appPackage': 'com.eg.android.AlipayGphone',
            'appActivity': 'com.eg.android.AlipayGphone.AlipayLogin'
        }
        # 'appActivity': 'com.eg.android.AlipayGphone.AlipayLogin.chimera.PersistentIntentOperationService',
        # 'automationName': 'uiautomator2',
        options = UiAutomator2Options().load_capabilities(capabilities)

        # driver = webdriver.Remote(command_executor=appium_server_url, options=options)
        driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', capabilities, options=options)
        # driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub',capabilities)

        # 同意按钮
        agg = driver.find_element(By.XPATH, '//*[@resource-id="android:id/button2"]')
        agg.click()

        time.sleep(5)

        # 注册按钮
        agg1 = driver.find_element(By.XPATH, '//*[@text="Sign up"]')
        agg1.click()

        code = self.getMessage(driver)
        isTrue = self.codeIfNull(code)
        if isTrue == True:
            code = self.getMessage(driver)
            if code is None:
                print("结束程序,验证码多次未收到,手动排查问题.")

        time.sleep(2)
        #输入验证码
        agg8 = driver.find_element(By.XPATH, '//*[@resource-id="com.ali.user.mobile.security.ui:id/box_input_wrapper"]/android.widget.TextView[1]')
        agg8.send_keys(code)


    def getMessage(self, driver):
        aPIClient = YeZiPhoneClient()

        # 获取Alipay手机号
        phone = aPIClient.get_phone()

        time.sleep(2)

        # 手机号输入框
        agg2 = driver.find_element(By.XPATH, '//*[@text="Enter phone number"]')
        # 输入手机号
        agg2.send_keys(phone)

        time.sleep(2)

        # 下一步按钮
        agg3 = driver.find_element(By.XPATH, '//*[@text="Next"]')
        agg3.click()

        code = aPIClient.get_message(phone)
        return code


    def codeIfNull(self, code, driver):
        if code is None:
            time.sleep(2)

            #回退
            agg4 = driver.find_element(By.XPATH, '//*[@resource-id="com.alipay.mobile.antui:id/back_button"]')
            agg4.click()
            time.sleep(2)

            # 回退
            agg5 = driver.find_element(By.XPATH, '//*[@resource-id="com.alipay.mobile.antui:id/back_button"]')
            agg5.click()
            time.sleep(2)

            #点击输入框
            agg6 = driver.find_element(By.XPATH,'//*[@resource-id="com.eg.android.AlipayGphone:id/login_guide_page_container"]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]')
            agg6.click()
            time.sleep(2)

            #删除输入框内容
            agg7 = driver.find_element(By.XPATH,'//*[@resource-id="com.eg.android.AlipayGphone:id/login_guide_page_container"]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.Button[1]')
            agg7.click()
            return True
        else:
            return False
a =AndroidRobot()
a.test_driver()

