import time

import requests
from bs4 import BeautifulSoup


url = 'https://quotes.toscrape.com/'
response = requests.get(url)
# print(f"Response: {response}")
# start_time = time.time()
soup = BeautifulSoup(response.text, 'lxml')
# delta_time = time.time() - start_time
# print(soup)
quotes = soup.find_all('span', class_='text')

for quote in quotes:
    print(quotes)
# print(delta_time)

# if __name__ == '__main__':
#     pass