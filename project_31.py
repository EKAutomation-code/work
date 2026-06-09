import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
BASE_URL = "https://scrapeme.live/shop/page/{}/"
headers = {
    "User-Agent": "Mozilla/5.0"
}
data = []
page = 1
while True:
    url = BASE_URL.format(page)
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        break
    soup = BeautifulSoup(res.text, "html.parser")
    products = soup.find_all("li", class_="product")
    if not products:
        break
    for p in products:
        title_tag = p.find("h2", class_="woocommerce-loop-product__title")
        price_tag = p.find("span", class_="woocommerce-Price-amount")
        title = title_tag.text.strip() if title_tag else "N/A"
        price = price_tag.text.strip() if price_tag else "N/A"
        link = p.find("a")["href"]
        data.append({
            "title": title,
            "price": price,
            "link": link
        })
    print(f"Page {page} scraped")
    page += 1
    time.sleep(1)
df = pd.DataFrame(data)
df.to_csv("shop.csv", index=False)
print("DONE: shop.csv")