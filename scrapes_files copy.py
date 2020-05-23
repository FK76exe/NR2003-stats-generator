#time to try nr2003 parsing
from bs4 import BeautifulSoup as soup


def listmaker(table):
    td = table.findAll("td")
    result_list = []
    #seperate if qual or race:
    if "TIME" in td[3].text:#for qual
        for x in range(0,len(td)-4,4):
            result_list.append([
                text_purifier(td[x].text),
                text_purifier(td[x+1].text),
                text_purifier(td[x+2].text),
                text_purifier(td[x+3].text)])
    elif "LAP" in td[0].text: #for penalty
        for x in range(0,len(td)-4,4):
            result_list.append([
                text_purifier(td[x].text),
                text_purifier(td[x+1].text),
                text_purifier(td[x+2].text),
                text_purifier(td[x+3].text)])        
    else:
        for x in range(0,len(td),9): #for race
            result_list.append([
                text_purifier(td[x].text),
                text_purifier(td[x+1].text),
                text_purifier(td[x+2].text),
                text_purifier(td[x+3].text),
                text_purifier(td[x+4].text),
                text_purifier(td[x+5].text),
                text_purifier(td[x+6].text),
                text_purifier(td[x+7].text),
                text_purifier(td[x+8].text)])
    return result_list
            
def get_track(html):
    f = open(html,"rb")
    contents = f.read()
    html_soup = soup(contents,features="html.parser")
    total_session = html_soup.findAll("h3")
    return text_purifier(total_session[0].text)

def text_purifier(text):
    text = text.replace('\r','')
    text = text.replace('\n','')
    text = text.replace('\t','')
    return text
    
def race_gen(html):
    #print("new")
    f = open(html,"rb")
    contents = f.read()
    html_soup = soup(contents,features="html.parser")
    total_session = html_soup.findAll("table")
    
    #sort into tables
    #print(listmaker(total_session[-2]))
    #print(len(listmaker(total_session[-2])))
##    if listmaker(total_session[-2])[0] == "F":
##        race = total_session[-2]  #if penalty table exists
##    else:
##        race = total_session[-1]  #if penalty table does not exist
    race = total_session[-2]
##    for x in total_session:
##        print(html)
##        if len(listmaker(x)) > 10:
##            print(listmaker(x)[:10])
##            print('next')
##        else:
##            print(listmaker(x))

    #purify them (make them a list)
    race = listmaker(race)

    return race

#have no table
#print(race_gen('race_folder/1997 R15.html'))
#print(race_gen('race_folder/1997 R20.html'))

#print(race_gen('race_folder/1997 R22.html'))
#print(race_gen('race_folder/1997 R2.html'))
