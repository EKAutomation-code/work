import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
data = []
for page in range(1, 6):
    url = BASE_URL.format(page)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")
    for book in books:
        title = book.h3.a["title"]
        price = book.find("p", class_="price_color").text
        rating = book.p["class"][1]
        data.append({
            "title": title,
            "price": price,
            "rating": rating
        })
    print(f"Scraped page {page}")
    time.sleep(1)
df = pd.DataFrame(data)
df.to_csv("books.csv", index=False)
print("DONE: books.csv")