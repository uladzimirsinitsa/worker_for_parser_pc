
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from flask import Flask, jsonify
from flask import request

from bs4 import BeautifulSoup

app = Flask(__name__)


def check_url(url):
    return 'pulscen.ru' in url


# index 1, 2, 3, 4
def get_price_and_availability(soup: BeautifulSoup) -> tuple:
    product_name = soup.find('h1').get_text(strip=True) or ''
    try:
        price = soup.find(class_='bp-price').get_text()
        if '&nbsp' in price:
            price = price.replace('&nbsp', '')
        if ' ' in price:
            price = price.replace(' ', '')
    except AttributeError:
        price = 'NA'
    try:
        currency = soup.find(class_='price-currency').get_text(strip=True)
    except AttributeError:
        currency = 'NA'
    try:
        availability = soup.find(class_='aui-text-label').get_text(strip=True)
    except AttributeError:
        availability = 'NA'
    if availability == 'Опт / Розница':
        availability = "NA"
    return product_name, price, currency, availability


# infex 5, 6
def get_sales_type(soup: BeautifulSoup):
    wholesale, retail = ['NA', 'NA']
    try:
        for i in soup.find_all(class_='aui-text-label'):
            if i.text.strip() == 'Опт / Розница':
                wholesale = 1
                retail = 1
            elif i.get_text(strip=True) == 'Опт':
                wholesale = 1
                retail = 0
            elif i.get_text(strip=True) == 'Розница':
                wholesale = 0
                retail = 1
    except IndexError:
        wholesale = 'NA'
        retail = 'NA'
    return wholesale, retail


# index 7, 8, 9
def get_item_data(soup: BeautifulSoup) -> tuple:
    vendor_code = 'NA'
    try:
        temp = soup.find(class_='product-info__left-cols').find_all(class_="product-description-list")
        for i in temp:
            if 'Артикул:' in i.find(class_='product-description-list__label').get_text(strip=True):
                vendor_code = i.find(class_='product-description-list__value').get_text(strip=True)
           
    except AttributeError:
        vendor_code = 'NA'
    try:
        img_url = soup.find(class_='product-images-main__img').get('src')
    except AttributeError:
        img_url = 'NA'
    try:
        category = soup.find_all(class_='aui-breadcrumbs__item-link')[-1].get_text(strip=True)
    except AttributeError:
        category = "NA"

    return vendor_code, img_url, category


# index 10, 11
def get_breadcrumbs_and_description(soup: BeautifulSoup) -> tuple:
    breadcrumbs = ''
    try:
        for breadcrumb in soup.find_all(class_='aui-breadcrumbs__item-link'):
            temp = breadcrumb.get_text(strip=True)
            breadcrumbs += f'{temp}* '
    except AttributeError:
        breadcrumbs = 'NA'
    try:
        description = soup.find(class_='product-tabber__body').text
        description = description.replace('ВКонтактеTwitter', '')
    except AttributeError:
        description = 'NA'
    return breadcrumbs, description
            

# index 12, 13, 14
def get_сontact_details(soup: BeautifulSoup) -> tuple:
    try:
        temp = soup.find(class_='phone-popup__contacts').find_all('a')
        phone = []
        phone_1, phone_2, mail = ['NA', 'NA', 'NA']
        for i in temp:
            if '@' in i.get_text(strip=True):
                mail = i.get_text(strip=True)
                break
        for i in temp:
            if '@' not in i.get_text(strip=True):
                phone.append(i.get_text(strip=True))
                if len(phone) == 2:
                    phone_1 = phone[0]
                    phone_2 = phone[1]
                    break
        if len(phone) == 1:
            phone_1 = phone[0]
    except AttributeError:
        phone_1, phone_2, mail = ['NA', 'NA', 'NA']

    return phone_1, phone_2, mail


# index 15, 16, 17, 18, 19
def get_seller_details(soup: BeautifulSoup) -> tuple:
    try:
        city = soup.find(class_='phone-popup__title').get_text(strip=True)
        if city == 'Отдел продаж':
            city = "NA"
    except AttributeError:
        city = 'NA'
    try:
        temp_string = soup.find(class_='yandex-map-static__map js-yandex-map-static-image').get('src')
        new_temp_string = temp_string.replace('https://static-maps.yandex.ru/1.x/?ll=', '')
        coordinates = new_temp_string[:new_temp_string.index('&')]
        if coordinates == '0,0':
            coordinates = 'NA'
    except AttributeError:
        coordinates = 'NA'
    try:
        sellers_name = soup.find(class_='product-company-info__name').find('a').get_text(strip=True)
    except AttributeError:
        sellers_name = 'NA'
    try:
        sellers_url = soup.find(class_='product-company-info__name').find('a').get('href')
    except AttributeError:
        sellers_url = 'NA'
    try:
        sellers_address = soup.find(class_='product-company-info__address').get_text(strip=True)
    except AttributeError:
        sellers_address = 'NA'
    return city, coordinates, sellers_name, sellers_url, sellers_address


# index 20, 21, 22, 23, 24, 25
def get_delivery_methods(soup: BeautifulSoup) -> tuple:
    temp = []

    pickup, delivery_by_transport_company, delivery_by_the_companys_fleet, courier_delivery, mail_delivery, other_delivery_methods = ['NA', 'NA', 'NA', 'NA', 'NA', 'NA']
    try:
        soup.find(id="tab-delivery").find(class_='product-deliveries__type').find_all(class_='product-deliveries__item')
    except AttributeError:
        return pickup, delivery_by_transport_company, delivery_by_the_companys_fleet, courier_delivery, mail_delivery, other_delivery_methods


    for i in soup.find(id="tab-delivery").find(class_='product-deliveries__type').find_all(class_='product-deliveries__item'):
        if i.find(class_='product-deliveries__name').get_text(strip=True) == 'Самовывоз':
            try:
                pickup = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                pickup = 1
            
        elif i.find(class_='product-deliveries__name').get_text(strip=True) == 'Доставка автопарком компании':
            try:
                delivery_by_the_companys_fleet = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                delivery_by_the_companys_fleet = 1
        elif i.find(class_='product-deliveries__name').get_text(strip=True) == 'Доставка транспортной компанией':
            try:
                delivery_by_transport_company = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                delivery_by_transport_company = 1
        elif i.find(class_='product-deliveries__name').get_text(strip=True) == 'Доставка курьером':
            try:
                courier_delivery = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                courier_delivery = 1
        elif i.find(class_='product-deliveries__name').get_text(strip=True) == 'Доставка почтой':
            try:
                mail_delivery = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                mail_delivery = 1
        else:
            key = i.find(class_='product-deliveries__name').get_text(strip=True)
            try:
                value = i.find(class_='product-deliveries__description').get_text(strip=True)
                if value == '':
                    value = 1
            except AttributeError:
                value = 1
            temp.append([key, value])
        other_delivery_methods = str(dict(temp))
        if other_delivery_methods == '{}':
            other_delivery_methods = 'NA'
    return pickup, delivery_by_the_companys_fleet, delivery_by_transport_company, courier_delivery, mail_delivery, other_delivery_methods


# index 27
def get_product_characteristics(soup: BeautifulSoup):
    temp = []
    try:
        for i in soup.find(id='tab-facets').find_all(class_='product-description-list__item'):
            key = i.find(class_='product-description-list__label').get_text(strip=True)
            value = i.find(class_='product-description-list__value').get_text(strip=True)
            temp.append([key, value])
        product_characteristics = str(dict(temp))
    except AttributeError:
        product_characteristics = 'NA'
    return product_characteristics 


# index 28 
def get_terms_of_payment(soup: BeautifulSoup):
    payment = []
    try:
        for i in soup.find(class_='product-deliveries__type_payment').find_all(class_='product-deliveries__item'):
            key = i.find(class_='product-deliveries__name').get_text(strip=True)
            value = 1
            try:
                if i.find(class_='product-deliveries__description-text').get_text(strip=True):
                    value = i.find(class_='product-deliveries__description-text').get_text(strip=True)
            except AttributeError:
                pass
            payment.append([key, value])
        terms = str(dict(payment))
    except AttributeError:
        terms = 'NA'
    return terms


@app.route('/', methods=['GET'])
def parser():
    if request.args['url']:
        url = request.args['url']
        for url in [url]:
            service = Service(executable_path=r'/usr/src/app/chromedriver')
            options = ChromeOptions()
            options.headless = True
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(url)

            if not check_url(driver.current_url):
                driver.quit()
                return jsonify({'response': 'code not pulse.ru'})
            try:
                element = driver.find_element(By.CLASS_NAME, 'js-show-phone-number')
                element.click()
                time.sleep(1)
                WebDriverWait(driver, timeout=25).until(
                    lambda d: d.find_element(By.CLASS_NAME, 'phone-popup__contacts')
                    )
            except TimeoutException:
                driver.quit()
                return jsonify({'except': 'TimeoutException'})
        
            except NoSuchElementException:
                driver.quit()
                return jsonify({'except': 'NoSuchElementException'})

            soup = BeautifulSoup(driver.page_source, 'lxml')
            driver.quit()

            product_name, price, currency, availability = get_price_and_availability(soup)
            wholesale, retail = get_sales_type(soup)
            vendor_code, img_url, category = get_item_data(soup)
            breadcrumbs, description = get_breadcrumbs_and_description(soup)
            phone_1, phone_2, mail = get_сontact_details(soup)
            city, coordinates, sellers_name, sellers_url, sellers_address = get_seller_details(soup)

            pickup, delivery_by_the_companys_fleet,\
                delivery_by_transport_company,\
                courier_delivery, mail_delivery,\
                other_delivery_methods = get_delivery_methods(soup)

            product_characteristics = get_product_characteristics(soup)
            terms_of_payment = get_terms_of_payment(soup)
            return {
                    'url_product': url,  # index 0
                    'title_product': product_name,  # index 1
                    'price': price,  # index 2
                    'currency': currency,  # index 3
                    'availability': availability,  # index 4
                    'bulk': wholesale,  # index 5
                    'retail': retail,  # index 6
                    'article': vendor_code,  # index 7
                    'url_photo': img_url,  # index 8
                    'category': category,  # index 9
                    'full_category_raw': breadcrumbs,  # index 10
                    'description_product': description,  # index 11
                    'tel_1': phone_1,  # index 12
                    'tel_2': phone_2,  # index 13
                    'email': mail,  # index 14
                    'city': city,  # index 15
                    'geo': coordinates,  # index 16
                    'title_seller': sellers_name,  # index 17
                    'url_seller': sellers_url,  # index 18
                    'address': sellers_address,  # index 19
                    'pickup': pickup,  # index 20
                    'delivery': delivery_by_transport_company,  # index 21
                    'self_delivery': delivery_by_the_companys_fleet,  # index 22
                    'courier': courier_delivery,  # index 23
                    'post': mail_delivery,  # index 24
                    'other_delivery': other_delivery_methods, # index 25
                    'characteristics': product_characteristics,  # index 26
                    'payments': terms_of_payment  # index 27      
                }


if __name__ == "__main__":
    app.run(debug=False)
