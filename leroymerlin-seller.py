from playwright.sync_api import sync_playwright
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import json
import csv

def save_cookies(context, path='cookies.json'):
    cookies = context.cookies()
    with open(path, 'w') as f:
        json.dump(cookies, f)

def load_cookies(file_path):
    with open(file_path, 'r') as f:
        cookies = json.load(f)
    return cookies

def simulate_human_behavior(page):
    page.mouse.move(random.randint(100, 500), random.randint(100, 500), steps=random.randint(20, 50))
    page.mouse.click(random.randint(100, 500), random.randint(100, 500), delay=random.uniform(0.1, 0.5))
    page.evaluate("window.scrollBy(0, window.innerHeight)")
    page.evaluate("""
        document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'ArrowDown'}));
        document.dispatchEvent(new MouseEvent('mousemove', {clientX: 100, clientY: 200}));
    """)

def extract_seller_info(page):

    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')

    seller_id_input = soup.find('input', {'id': 'seller-id'})
    seller_id = seller_id_input['value'] if seller_id_input else None


    seller_name_element = soup.find('div', class_='m-seller-info__name')
    seller_name = seller_name_element.text.strip() if seller_name_element else 'N/A'

    global_score_element = soup.find('span', class_='mc-stars-result__text')
    global_score = global_score_element.text.strip().replace("Global score: " , "") if global_score_element else 'N/A'

    location_element = soup.find('p', class_='m-seller-info__city')
    location = location_element.text.strip().split(':')[1].strip() if location_element else ''

    shipping_country_element = soup.find('p', class_='m-seller-info__country')
    shipping_country = shipping_country_element.text.strip().split(':')[1].strip() if shipping_country_element else ''

    member_since_element = soup.find('span', class_='m-seller-info__sub-text')
    member_since = member_since_element.text.strip() if member_since_element else ''

    about_element = soup.find('div', class_='m-seller-pres')
    about = about_element.text.strip() if about_element else ''

    shipping_terms_element = soup.find('div', id='ELEM_shippingTerms_content')
    shipping_terms = shipping_terms_element.text.strip() if shipping_terms_element else ''

    returns_refund_element = soup.find('div', id='ELEM_returnsAndRefund_content')
    returns_refund = returns_refund_element.text.strip() if returns_refund_element else ''

    eco_participation_element = soup.find('div', id='ELEM_ecoParticipation_content')
    eco_participation = eco_participation_element.text.strip() if eco_participation_element else ''

    take_back_policy_element = soup.find('div', id='ELEM_takeBackPolicy_content')
    take_back_policy = take_back_policy_element.text.strip() if take_back_policy_element else ''

    response = page.request.post("https://www.leroymerlin.fr/bomp-seller/reviews", data=json.dumps({"id": seller_id}),headers={'Content-Type': 'application/json'})
    response_json = response.json()

    total_review_count = ((response_json or {}).get('statistics') or {}).get('totalRatingStatistics', {}).get('totalReviewCount', '') if response_json else 'N/A'
    seller_info = {
    'id' : seller_id,
    'Nom du vendeur': seller_name,
    'Score global': global_score,
    'Nombre des avis': total_review_count,
    'Siège': location,
    'Pays d\'expédition': shipping_country,
    'Membre depuis': member_since,
    'À propos': about,
    'Modalités d\'expédition': shipping_terms,
    'Retour et remboursement': returns_refund,
    'Éco-participation': eco_participation,
    'Modalités de reprise': take_back_policy,
    'Lien vendeur': page.url
}
    return seller_info

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    context = browser.new_context()

    try:
        cookies = load_cookies("cookies.json")
        context.add_cookies(cookies)
    except:
        context = browser.new_context()
    
    # context.clear_cookies()
    
    page = context.new_page()
    seller_data = []
    
    with open("sellers.txt", "r") as file:
        seller_links = file.read().splitlines()
    
    for link in seller_links:
      try :
        page.goto(link)
        page.wait_for_selector("#component-sellercomponent", state="attached", timeout=40000)  
        seller_info = extract_seller_info(page)
        simulate_human_behavior(page)
        print(seller_info)
        seller_data.append(seller_info)
        df = pd.DataFrame(seller_data)
        df.to_excel("seller_info.xlsx", index=False)
        print()
      except Exception as e:
          print(e)
    
    save_cookies(context)
    browser.close()