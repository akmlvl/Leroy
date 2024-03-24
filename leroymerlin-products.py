from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import csv
import json
import os
def save_cookies(context, path='cookies.json'):
    cookies = context.cookies()
    with open(path, 'w') as f:
        json.dump(cookies, f)

def load_cookies(file_path):
    with open(file_path, 'r') as f:
        cookies = json.load(f)
    return cookies

def bot_captcha(p) :
      browser = p.firefox.launch(headless=False)
      context = browser.new_context()
      cookies = load_cookies("cookies.json")
      context.add_cookies(cookies)
      page = context.new_page()
      page.goto('https://leroymerlin.fr') 
      aa = input("continue : ??")
      save_cookies(context)
      page.close()

def simulate_human_behavior(page):
    page.mouse.move(random.randint(100, 500), random.randint(100, 500), steps=random.randint(7, 15))
    page.mouse.click(random.randint(100, 500), random.randint(100, 500), delay=random.uniform(0.1, 0.3))
    page.evaluate("window.scrollBy(0, window.innerHeight)")
    page.evaluate("""
        document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'ArrowDown'}));
        document.dispatchEvent(new MouseEvent('mousemove', {clientX: 100, clientY: 200}));
    """)

def extract_product_info(html_content,current_page_number,category_id):


    soup = BeautifulSoup(html_content, 'html.parser')

    info_tag = soup.find('script', {'class': 'dataJsonLd'})

    json_data = json.loads(info_tag.string) if info_tag else None

    products_number = json_data["offers"]["offerCount"] if json_data and "offers" in json_data else None
    price_currency = json_data["offers"]["priceCurrency"] if json_data and "offers" in json_data else None

    #pages number
    nav_tag = soup.find('nav', {'class': 'mc-pagination'})
    pages_number = nav_tag.get('data-max-page') if nav_tag else None


    div_element = soup.find('div', {'class': 'col-xl-9 col-xxl-9 col-s-12 col-m-12 col-l-12 col-line-end js-list-content'})
    products_script_tag = div_element.find('script', {'class': 'dataTms'})

    products_data = json.loads(products_script_tag.string) if products_script_tag else None

    
    list_products_entry = next((item for item in products_data if item["name"] == "list_products"), None)
    
    products_list = list_products_entry["value"] if list_products_entry else None
    
    products = []
    
    for product in products_list:
        product_id = product.get("list_product_id", "")
        product_name = product.get("list_product_name", "")
        product_price = product.get("product_unitprice_ati", "")
        product_url = "https://www.leroymerlin.fr" + product.get("list_product_url_page", "")
        product_seller_id = product.get("seller_id", "")
        product_seller_name = product.get("seller", "")
        product_position = f'category {category_id} page :{current_page_number} Pos:{product.get("list_product_position", "")}'
        
        products.append({
            "Product ID": product_id,
            "Product Name": product_name,
            "Prix Produit": product_price,
            "Product URL": product_url,
            "ID vendeur": product_seller_id,
            "Nom vendeur": product_seller_name,
            "Product Position": product_position
        })

    # Create a dictionary with the extracted information
    info = { 'category_id' :  category_id, 'page' : current_page_number,
   'Nomber de pages' : pages_number, 'Nombre de produits': products_number, 'price currency' : price_currency
}
    print(info)
    return products, int(pages_number)

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    context = browser.new_context()

    try:
        cookies = load_cookies("cookies.json")
        context.add_cookies(cookies)
    except:
        context = browser.new_context()
        
    page = context.new_page()
    def handle_route(route, request):
          if request.resource_type == 'image':
              route.abort()
          else:
              route.continue_()
      
    page.route('**/*', handle_route)
    
    with open("category_ids.txt", "r") as file:
        categories = file.read().splitlines()
    
    for category_id in categories:
      category_products = []
      save_cookies(context)
      current_page = 1
      pages_number = None
      failed = False

      while not failed and (pages_number is None or (current_page <= pages_number and current_page <=3)) :
              try:
                page.goto(f'https://www.leroymerlin.fr/product-family-v2/services/productfamilypage?category={category_id}&version=standard&locale=fr_FR&p={current_page}')
                page.wait_for_selector("#sorting-select", state="attached", timeout=30000)
                
                page_products = []
                
                page_products, pages_number = extract_product_info(page.content(),current_page , category_id)
                current_page += 1
              except Exception as e:
                  print("failed on " + category_id + str(e))
                  failed = True
                  with open("failed.txt", "a") as file:
                   file.write(category_id+"\n")
                  page.close()
                  print(page.url)
                  bot_captcha(p)
                  cookies = load_cookies("cookies.json")
                  context.add_cookies(cookies)
                  page = context.new_page()
                  page.route('**/*', handle_route)
              category_products.extend(page_products)
      products_df = pd.DataFrame(category_products)
      products_df.to_csv("products_info.csv", mode='a', index=False, header=not os.path.isfile("products_info.csv"), encoding='utf-8-sig')

    products_df['Prix Produit'] = pd.to_numeric(products_df['Prix Produit'], errors='coerce')
    
    grouped = products_df.groupby(['ID vendeur' , 'Nom vendeur'])
    
    products_per_seller = grouped.size().reset_index(name='Nombre de produits')
    
    median_price_per_seller = grouped['Prix Produit'].median().reset_index(name='Prix Moyen')
    
  
    summary_df = pd.merge(products_per_seller, median_price_per_seller, on=['ID vendeur' , 'Nom vendeur'])
    
    summary_df.to_excel('seller_summary.xlsx', index=False)