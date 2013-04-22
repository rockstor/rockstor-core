from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re
from rockstor_testcase import RockStorTestCase

class LoginInvalidUsername(RockStorTestCase):
    
    def test_login_invalid_username(self):
        driver = self.driver
        driver.get(self.base_url + "/login_page?next=/")
        driver.find_element_by_id("inputUsername").clear()
        driver.find_element_by_id("inputUsername").send_keys("admin1")
        driver.find_element_by_id("inputPassword").clear()
        driver.find_element_by_id("inputPassword").send_keys("admin")
        driver.find_element_by_css_selector("button.btn.btn-primary").click()
        # Warning: verifyTextPresent may require manual changes
        self.assertRegexpMatches(driver.find_element(by=By.TAG_NAME, value="body").text, r"^[\s\S]*Login incorrect![\s\S]*$")
    
