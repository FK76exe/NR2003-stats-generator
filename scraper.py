from bs4 import BeautifulSoup as soup
import re


def clean_record(record: str):
    """Cleans up record string to be readable"""
    pattern = re.compile(r'[^\n\t]+')
    matches = pattern.findall(record)
    return matches

def convert_html_to_table(filepath: str):
    """Reads an HTML file and generates a dictionary of information"""
    data = {}

    file = open(filepath, "r")
    content = file.read()
    
    # convert to bs4
    html_soup = soup(content, features="html.parser")

    # find track name
    data['track'] = html_soup.find("h3").text

    # get race results
    race_table = html_soup.find_all("table")[-2].find_all("tr")

    # turn race results into 2D array
    data["results"] = [clean_record(record.text) for record in race_table[1:]]

    return data