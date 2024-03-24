from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import time
import random
import json

category_links = []

def save_cookies(context, path='cookies.json'):
    cookies = context.cookies()
    with open(path, 'w') as f:
        json.dump(cookies, f)

def load_cookies(file_path):
    with open(file_path, 'r') as f:
        cookies = json.load(f)
    return cookies

def simulate_human_behavior(page):
    page.mouse.move(random.randint(100, 500), random.randint(100, 500), steps=random.randint(7, 20))
    page.mouse.click(random.randint(100, 500), random.randint(100, 500), delay=random.uniform(0.1, 0.3))
    page.evaluate("window.scrollBy(0, window.innerHeight)")
    page.evaluate("""
        document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'ArrowDown'}));
        document.dispatchEvent(new MouseEvent('mousemove', {clientX: 100, clientY: 200}));
    """)

def extract_links(html_content):
 soup = BeautifulSoup(html_content, 'html.parser')
 base_url = 'https://www.leroymerlin.fr/produits'
 return [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith(base_url)]


def scrape_category(page, link):
    try:
        page.goto(link)
        page.wait_for_selector("#component-WebsiteHeaderComponent", state="attached", timeout=40000)
        html_content = page.content()
        simulate_human_behavior(page)

        soup = BeautifulSoup(html_content, 'html.parser')
        category_div = soup.find('div', id='component-productfamilypage')
        category_id = category_div.get('data-category') if category_div else None
        print(f"Category ID : {category_id}")
        with open("category_ids.txt", 'a') as file:
         if category_id is not None:
           file.write(category_id.strip()+"\n")
        
    except Exception as e:
               print(f"stopped on {link}")
               print(e)

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)

    context = browser.new_context()
    try:
        cookies = load_cookies("cookies.json")
        context.add_cookies(cookies)
    except Exception as e:
        print(f"Could not load cookies: {e}")
    
    page = context.new_page()

    for i in range (1,3): 
     page.goto(f"https://www.leroymerlin.fr/plan-de-site-categories.html?p={i}")
     page.wait_for_selector("#component-WebsiteHeaderComponent", state="attached", timeout=40000)
     category_links.extend(extract_links(page.content()))

    page = context.new_page()
    for link in category_links[2230:] : 
        scrape_category(page, link)

    save_cookies(context, "cookies.json")
    browser.close()