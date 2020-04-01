from scraper import *
from parser import *

#next level secure login
LOGIN = ""
PASS = ""

ARTISTS = [
    "https://bidtoart.com/en/find-artist/vhils-alexandre-farto/472263",
]

def main():
    scrape(LOGIN, PASS, ARTISTS)
    parse()


if __name__ == '__main__':
    main()