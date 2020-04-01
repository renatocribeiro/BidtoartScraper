import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path
from random import randint
import time
import numpy as np

MAX_SAVES = 1500

def wait_a_bit():
    secs = [(1, 5), (5, 10), (10, 30), (30, 60)]
    probs = [0.8, 0.16, 0.02, 0.02]
    rand_ch = np.random.choice(len(secs), 1, p=probs)[0]
    secs = np.random.uniform(*secs[rand_ch])
    print("wait {} secs.".format(secs))
    time.sleep(secs)

def is_login_succ(r):
    soup_login = BeautifulSoup(r.content, 'html.parser')
    div_log = soup_login.find("div", attrs={"class":"not-logged"})
    return not div_log

def retrieve_categories(r):
    par = lambda x:x[:x.rfind('(')].strip()
    soup_cats = BeautifulSoup(r.content, 'html.parser')
    select_cat = soup_cats.find("select", attrs={"data-param":"category"}).find_all("option")
    cats = {int(cat.get('value')):par(cat.get_text()) for cat in select_cat[1:]}
    return cats

def is_next_page_avail(r):
    soup_next = BeautifulSoup(r.content, 'html.parser')
    return bool(soup_next.find("a", attrs={"rel":"next"}))

def has_sub(r):
    soup_item = BeautifulSoup(r.content, 'html.parser')
    return not bool(soup_item.find("a", attrs={"class":"subcriber_only"}))

def gen_path(artist_name, item_name, category_name):
    norm = lambda x:x.replace(' ', '_').lower()
    return Path("./{}/{}/{}.html".format(norm(artist_name), norm(category_name), norm(item_name)))

def save_to_file(r, path):
    soup_item = BeautifulSoup(r.content, 'html.parser')
    lot = soup_item.find("li", attrs={"class":"lot-detail"})

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(lot.decode_contents())
    print("S:{}".format(path))

def retrieve_items(r):
    soup_items = BeautifulSoup(r.content, 'html.parser')
    return [item.get('href') for item in soup_items.find_all("a", attrs={"class":"text-bold underline"})]

def file_exists(path):
    return path.is_file() and path.stat().st_size > 0

def get_req(sess, url):
    for _ in range(3):
        try:
            r = sess.get(url)
        except ConnectionError as e:
            print(e)
        except Exception as e:
            print(e)
        else:
            wait_a_bit()
            return r
        wait_a_bit()
    exit()

def scrape(login, pw, artists):
    login_url = "https://bidtoart.com/en/login"
    nbr_saves = 0
    with requests.Session() as s:

        r_login = s.post(login_url, data = {'member_login_name':login, 'member_password':pw})
        if is_login_succ(r_login):
            print("LOGIN OK")
            wait_a_bit()

            for artist in artists:
                r_artist = get_req(s, artist)
                cats = retrieve_categories(r_artist)
                for cat in cats:
                    curr_page = 1
                    while (curr_page is not None):
                        #load new page
                        cat_url = "{base_url}?page={page_nbr}&limit=100&category={cat_nbr}".format(base_url = artist, page_nbr = curr_page, cat_nbr = cat)                        
                        print(cat_url)
                        r_cat = get_req(s, cat_url)
                        
                        #go through items
                        items = retrieve_items(r_cat)

                        for item in items:
                            artist_name = artist.split('/')[5]
                            item_name = "_".join(item.split('/')[5:])
                            path = gen_path(artist_name, item_name,  cats[cat])
                            
                            if nbr_saves > MAX_SAVES:
                                print("Passed MAX_SAVES")
                                exit()

                            if not file_exists(path):
                                r_item = get_req(s, item)
                                if has_sub(r_item):
                                    save_to_file(r_item, path)
                                    nbr_saves += 1
                                else:
                                    print("Subscription might be over.")
                                    exit()

                        #prepare next page
                        curr_page = curr_page+1 if is_next_page_avail(r_cat) else None
        else:
            print("LOGIN NOK")