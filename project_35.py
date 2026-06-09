from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
url = "https://scrapeme.live/shop/"
driver.get(url)
data = []
while True:
    time.sleep(2)
    products = driver.find_elements(By.CLASS_NAME, "product")
    for p in products:
        try:
            title = p.find_element(By.TAG_NAME, "h2").text
            price = p.find_element(By.CLASS_NAME, "price").text
            link = p.find_element(By.TAG_NAME, "a").get_attribute("href")

            data.append({
                "title": title,
                "price": price,
                "link": link
            })
        except:
            continue
    try:
        next_btn = driver.find_element(By.CLASS_NAME, "next")
        next_btn.click()
    except:
        break
driver.quit()
df = pd.DataFrame(data)
df.to_csv("selenium_shop.csv", index=False)
print("DONE: selenium_shop.csv")