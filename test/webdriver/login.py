from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#driver = webdriver.Firefox()
#driver = webdriver.Firefox()

# read configuration
import yaml
f = open('config.yaml')
# use safe_load instead load
config = yaml.safe_load(f)
login_url = config['login_url']

f.close()

# Go to the Login page
driver.get(login_url)

# Fill in username / password
loginField = driver.find_element_by_name("login")
loginField.send_keys("admin")

passwordField = driver.find_element_by_name("password")
passwordField.send_keys("admin")

# submit the form
driver.find_element_by_id("sign_in").click()

disks_nav = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "disks_nav")))
disks_nav.click()

disks_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "disks-table"))) 
disk_rows = driver.find_elements_by_class_name("disk_row")
for d in disk_rows:
    print d.get_attribute('href')

driver.quit()

