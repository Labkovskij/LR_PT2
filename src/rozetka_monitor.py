from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time


class RozetkaMonitor:
    def __init__(self, url, data_file='data/products.csv', driver_path='chromedriver'):
        self.url = url
        self.data_file = data_file
        self.driver_path = driver_path

    def fetch_products(self):
        """Отримання даних про товари."""
        options = Options()
        options.add_argument('--headless')  # Запуск без відкриття браузера
        options.add_argument('--disable-gpu')
        service = Service(self.driver_path)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(self.url)
        time.sleep(5)  # Зачекати завантаження сторінки

        products = []
        items = driver.find_elements(By.CLASS_NAME, 'goods-tile')
        for item in items:
            try:
                name = item.find_element(By.CLASS_NAME, 'goods-tile__title').text.strip()
                price = item.find_element(By.CLASS_NAME, 'goods-tile__price-value').text.strip()
                price = float(price.replace(' ', '').replace('₴', ''))  # Видалення пробілів і знаку гривні
                availability = 'In Stock' if item.find_element(By.CLASS_NAME,
                                                               'goods-tile__availability') else 'Out of Stock'
                products.append({'Name': name, 'Price': price, 'Availability': availability})
            except Exception as e:
                print(f"Error parsing item: {e}")
        driver.quit()
        return pd.DataFrame(products)

    def load_previous_data(self):
        """Завантаження попередніх даних."""
        if os.path.exists(self.data_file):
            return pd.read_csv(self.data_file)
        else:
            return pd.DataFrame(columns=['Name', 'Price', 'Availability'])

    def save_data(self, data):
        """Збереження даних."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data.to_csv(self.data_file, index=False)

    def compare_data(self, old_data, new_data):
        """Порівняння даних."""
        changes = {
            'New Products': new_data[~new_data['Name'].isin(old_data['Name'])],
            'Removed Products': old_data[~old_data['Name'].isin(new_data['Name'])],
            'Price Changes': new_data.merge(old_data, on='Name', suffixes=('_new', '_old')).query(
                'Price_new != Price_old')
        }
        return changes

    def monitor(self):
        """Моніторинг змін."""
        new_data = self.fetch_products()
        old_data = self.load_previous_data()
        changes = self.compare_data(old_data, new_data)
        self.save_data(new_data)

        report = []
        if not changes['New Products'].empty:
            report.append("New Products:\n" + changes['New Products'].to_string(index=False))
        if not changes['Removed Products'].empty:
            report.append("\nRemoved Products:\n" + changes['Removed Products'].to_string(index=False))
        if not changes['Price Changes'].empty:
            report.append("\nPrice Changes:\n" + changes['Price Changes'].to_string(index=False))
        return '\n'.join(report)


# Використання
if __name__ == "__main__":
    url = "https://rozetka.com.ua/ua/notebooks/c80004/"  # Категорія ноутбуків
    monitor = RozetkaMonitor(url, driver_path='path/to/chromedriver')  # Вкажіть шлях до chromedriver
    report = monitor.monitor()

    # Збереження звіту
    with open('results/report.txt', 'w') as f:
        f.write(report)

    print(report)