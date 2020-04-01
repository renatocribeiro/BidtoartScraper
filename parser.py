import glob
import re
import pandas as pd
from bs4 import BeautifulSoup

def pos_num(s):
    return re.findall(r"\d{4}", s)

def get_li_pos(s, *args):
    for i, elem in enumerate(s):
        if any([arg in elem.get_text() for arg in args]):
            return i
    return None

def parse():
    l = []
    for f_path in glob.glob('./**/*.html', recursive = True):
        with open(f_path, 'r') as f:
            content = f.read().replace('\n', '')
            soup = BeautifulSoup(content, 'html.parser')
            li = soup.find_all("li")
            comps = f_path.split('/')[1:]
            artist_name = comps[0]
            category = comps[1]
            item_id = comps[2][comps[2].rfind('_')+1:comps[2].rfind('.')]
            lot_number = li[0].get_text()[li[0].get_text().find("Lot")+3:].strip()
            item_name_ = soup.find("li", attrs = {"class":"art_item_name"}).get_text().strip()
            match_year = pos_num(item_name_)
            if len(match_year) == 0:
                item_name = item_name_
                item_year = (None, None)
            elif len(match_year) == 1:
                pos_year = item_name_.rfind(match_year[0])
                item_name = item_name_[:pos_year].strip(' (,.-')
                item_year = (int(match_year[0]), int(match_year[0]))
            elif len(match_year) == 2:
                if match_year[0] == match_year[1]:
                    pos_year = item_name_.find(match_year[0])
                    item_name = item_name_[:pos_year].strip(' (,.-')
                    item_year = (int(match_year[0]), int(match_year[0]))
                else:
                    pos_year0 = item_name_.find(match_year[0])
                    pos_year1 = item_name_.find(match_year[1])
                    if ('-' in item_name_[pos_year0:pos_year1] or
                        '/' in item_name_[pos_year0:pos_year1]):
                        item_name = item_name_[:pos_year0]
                        item_year = (int(match_year[0]), int(match_year[1]))
                    elif int(1900 <= int(match_year[1]) <= 2000):
                        item_name = item_name_[:pos_year1].strip(' (,.-')
                        item_year = (int(match_year[1]), int(match_year[1]))
            else:
                item_name = item_name_[:item_name_.find(match_year[-1])]
                item_year = (int(match_year[-1]), int(match_year[-1]))
            item_support = li[2].get_text().replace('\n', '').replace('\t', '').strip()
            item_signed = "inch" not in li[3].get_text()
            dims_li_pos = get_li_pos(li, " inch ")
            dims = (None, None, None)
            if dims_li_pos is not None:
                dim_raw = li[dims_li_pos].get_text()
                ppos_1 = dim_raw.find('(')
                ppos_2 = dim_raw.rfind(')')
                dim_raw = dim_raw[ppos_1+1:ppos_2].replace(' ', '').replace('\t', '').replace('-', '').strip()
                dims_ = dim_raw.split('inch')[:-1]
                dims = (float(dims_[0]), float(dims_[1]) if len(dims_) >= 2 else None , float(dims_[2]) if len(dims_) == 3 else None)
            estim_li_pos = get_li_pos(li, " Estimate ")
            estim_from = li[estim_li_pos].find("input", attrs={"id":"estimated_price_from"}).get("value")
            estim_to = li[estim_li_pos].find("input", attrs={"id":"estimated_price_to"}).get("value")
            if estim_from == '0' or estim_from == '':
                estim_from = None
                estim_to = None
                estim_curr = None
                estim_rate = None
            else:
                select = li[estim_li_pos].find("option", attrs={"selected":"selected"})
                if select:
                    estim_curr = select.get_text()
                    estim_rate = select.get("value")
                else:
                    estim_curr = li[estim_li_pos].find("option").get_text()
                    estim_rate = li[estim_li_pos].find("option").get("value")
                
            sold_li_pos = get_li_pos(li, "Sold:", "Unsold")
            price_sold_ = li[sold_li_pos].find("input", attrs={"class":"price_sold"})
            price_sold, curr_sold, rate_sold = None, None, None
            if price_sold_:
                price_sold = price_sold_.get("value")
                pos_select = li[sold_li_pos].find("option", attrs={"selected":"selected"})
                curr_sold = pos_select.get_text()
                rate_sold = pos_select.get("value")
            house_name = None
            house_name_pos = soup.find("li" ,attrs={"class":"house_name"})
            if house_name_pos:
                house_name = house_name_pos.get_text().strip()
            house_auction_name = None
            house_auction_name_pos = soup.find("li" ,attrs={"class":"house_auction_name"})
            if house_auction_name_pos:
                house_auction_name = house_auction_name_pos.get_text().strip()
            pos_sale_nbr = get_li_pos(li, "Sale no")
            sale_nbr_ = li[pos_sale_nbr].get_text().replace('Sale no', '').strip()
            sale_nbr = None if sale_nbr_ == "N/A" or sale_nbr_ == "" else sale_nbr_
            
            sale_date_pos = pos_sale_nbr - 1
            pos_arrow = li[sale_date_pos].get_text().find("->")
            sale_date = li[sale_date_pos].get_text()[:pos_arrow] if pos_arrow != -1 else li[sale_date_pos].get_text()
            sale_date = sale_date.strip().replace('\t', '').replace(', ', ',').replace(' ', ',')
            sale_date_comps = sale_date.split(',')
            month, day, year = None, None, None
            month, day, year = sale_date_comps[0], int(sale_date_comps[1]), int(sale_date_comps[2])
            
            city, region, country = None, None, None
            if len(li)-1 != pos_sale_nbr:
                locs_comps = li[-1].get_text().strip().split(',')
                locs_comps = list(map(str.strip, locs_comps))
                if len(locs_comps) == 2:
                    city, country = locs_comps[0], locs_comps[1]
                else:
                    city, region, country = locs_comps[0], locs_comps[1], locs_comps[2]
            tmp_d = {"artist":artist_name, "category":category, "site_id":item_id, 
                    "lot_number":lot_number, "item_name":item_name, 
                    "item_year_from":item_year[0],"item_year_to":item_year[1], "item_support":item_support,
                    "item_signed":item_signed, "dim1":dims[0], 
                    "dim2":dims[1], "dim3":dims[2], "estim_from":estim_from,
                    "estim_to":estim_to, "estim_curr":estim_curr,
                    "estim_rate":estim_rate, "sold_price":price_sold,
                    "sold_curr":curr_sold, "sold_rate":rate_sold,
                    "house_name":house_name, "house_auction_name":house_auction_name,
                    "sale_number":sale_nbr, "sale_day":day, "sale_month":month,
                    "sale_year":year, "city":city, "region":region, "country":country}
            l.append(tmp_d)
    pd.DataFrame(l).to_csv("all.csv")