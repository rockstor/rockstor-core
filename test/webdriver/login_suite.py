from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import unittest, time, re
import yaml
import sys, getopt
from login_happypath import LoginHappypath
from login_invalid_username import LoginInvalidUsername
from rockstor_testcase import RockStorTestCase
from  util import read_conf

if __name__ == "__main__":
    conf = read_conf('development')
    suite = unittest.TestSuite([\
            unittest.TestLoader().loadTestsFromTestCase(LoginHappypath),\
            unittest.TestLoader().loadTestsFromTestCase(LoginInvalidUsername)])

    unittest.TextTestRunner(verbosity=2).run(suite)

