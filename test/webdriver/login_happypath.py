from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import unittest, time, re
import yaml
import sys, getopt
from rockstor_testcase import RockStorTestCase

class LoginHappypath(RockStorTestCase):
    def test_login_happypath(self):
        driver = self.driver
        driver.get(self.base_url + "/login_page?next=/")
        driver.find_element_by_id("inputUsername").clear()
        driver.find_element_by_id("inputUsername").send_keys("admin")
        driver.find_element_by_id("inputPassword").clear()
        driver.find_element_by_id("inputPassword").send_keys("admin")
        driver.find_element_by_id("sign_in").click()
        # wait till current step element is rendered
        current_step = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "current-step")))
        driver.find_element_by_id("logout_user").click()

