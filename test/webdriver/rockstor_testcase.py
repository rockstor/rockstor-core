from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import unittest, time, re
import yaml
import sys, getopt

class RockStorTestCase(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        with open('config.yaml','r') as f:
            conf = yaml.load(f)
        self.base_url = conf['base_url']
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()

