#time to try nr2003 parsing
from bs4 import BeautifulSoup as soup
import re


def listmaker(table):
    td = table.findAll("td")
    if "TIME" in td[3].text or "LAP" in td[0].text: # for practice, qualifying, happy hour, and penalties
        return [[purify_text(td[y].text) for y in range(x, x+4)] for x in range(0, len(td)-4, 4)]      
    else: # for race
        return [[purify_text(td[y].text) for y in range(x, x+9)] for x in range(0, len(td), 9)]

def purify_text(text):
    return text.replace('\r','').replace('\n','').replace('\t','').replace('*','')
    
def scrape_results(html: str):
    html_soup = soup(html,features="html.parser")
    tables = html_soup.findAll("table")

    # substring to find session headers
    h3_pattern = re.compile("Session:\s([A-Z][a-z]*)")
    titles = [purify_text(title.text).replace("Session: ", "") for title in html_soup.findAll("h3", string=h3_pattern)] + ['Penalties']

    # create dictionary {key=session, value=2d array of table}
    race_dict = {}
    for i, title in enumerate(titles):
        race_dict.update({title: listmaker(tables[i])})
    return race_dict