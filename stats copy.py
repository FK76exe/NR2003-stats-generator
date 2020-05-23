import pandas as pd
from os import listdir
from os.path import isfile,join
import scrapes_files as scrape
from bs4 import BeautifulSoup as soup

all_races = [f for f in listdir('race_folder') if isfile(join('race_folder', f))][1:]
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('expand_frame_repr', False)

###accumulate all results in one dataframe
##accumulator = [['F', 'S', '#', 'DRIVER', 'INTERVAL', 'LAPS', 'LED', 'POINTS', 'STATUS','Race Index']]
##for x in all_races:
##    y = scrape.race_gen('race_folder/' + x)[1:]
##    #print(y)
##    i = (x.split('.html'))[0]
##    for z in y:
##        z.append(i)
##        accumulator.append(z)
##
##
###create accumulator table
##racedata = pd.DataFrame(accumulator[1:],columns = accumulator[0])
##total_stats = pd.DataFrame(columns=['Driver','Starts','Wins','Top 5s','Top 10s','Poles','Av Start','Av Finish','Laps Run','Laps Led','Points','DNF'])

def gen_stats(race_list):
        #accumulate all results in one dataframe
    accumulator = [['F', 'S', '#', 'DRIVER', 'INTERVAL', 'LAPS', 'LED', 'POINTS', 'STATUS','Race Index']]
    for x in race_list:
        y = scrape.race_gen('race_folder/' + x)[1:]
        #print(y)
        i = (x.split('.html'))[0]
        for z in y:
            z.append(i)
            accumulator.append(z)


    #create accumulator table
    racedata = pd.DataFrame(accumulator[1:],columns = accumulator[0])
    total_stats = pd.DataFrame(columns=['Driver','Starts','Wins','Top 5s','Top 10s','Poles','Av Start','Av Finish','Laps Run','Laps Led','Points','DNF'])

    drivers = racedata.DRIVER.unique()
    i = 0
    for driver in drivers:
        win = 0
        starts = 0
        pole = 0
        top5 = 0
        top10 = 0
        av_s = 0
        av_f = 0
        laps_led = 0
        points = 0
        laps_run = 0
        dnf = 0
        for x in racedata[racedata['DRIVER']==driver]['F']:
            if int(x) == 1:
                win += 1
            if int(x) < 6:
                top5 += 1
            if int(x) < 11:
                top10 += 1
            starts += 1
            av_f += int(x)
        for y in racedata[racedata['DRIVER']==driver]['S']:
            if int(y) == 1:
                pole += 1
            av_s += int(y)
        for j in racedata[racedata['DRIVER']==driver]['LAPS']:
            try:laps_run += int(j)
            except TypeError:
                print("bad",racedata[racedata['DRIVER']==driver]['Race Index'])
        for z in racedata[racedata['DRIVER']==driver]['LED']:
            if "*" in z:
                laps_led += int(z.replace("*",""))
            else:
                laps_led += int(z)
        for z in racedata[racedata['DRIVER']==driver]['POINTS']:
            points += int(z)
        for m in racedata[racedata['DRIVER']==driver]['STATUS']:
            if m != 'Running':
                dnf += 1
        av_s = round(av_s/starts,2)
        av_f = round(av_f/starts,2)
        total_stats.loc[i] = [driver,starts,win,top5,top10,pole,av_s,av_f,laps_run,laps_led,points,dnf]
        i += 1
    return total_stats

total_stats = gen_stats(all_races)
total_stats = total_stats.sort_values(['Wins'],ascending=False)
print(total_stats)
