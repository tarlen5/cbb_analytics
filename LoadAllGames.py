#! /usr/bin/env python
#
# LoadAllGames.py
#
# author: Timothy C. Arlen
#         timothyarlen@gmail.com
#
# date:   24 March 2015
#
#
# 16 - April 2015 TO DO:
#   1) Do we want columns for FirstName, LastName? - Not sure
#      because play-by-play always gives full name...
#   2) Put in print tabulate statements for debug mode -- DONE
#   3) Break off ending diagnostics to new file: processGames.py -- DONE
#   4) Consistency for var_names, FunctionNames()!!! -- DONE
#   Naming conventions: ClassName, ModuleName, funcName, var_name, CONSTANT
#   5) Put date in db file, since mutiple gms against same team! -- DONE
#   6) Order date first in name...
#

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import re
import os
import sys

from urllib2 import urlopen
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from pandas import DataFrame, Series
from tabulate import tabulate

from LogUtils import logging, set_verbosity

# Global variables-regex:
clock_expr = re.compile("(20:00|[0-1][0-9]:[0-5][0-9])")
date_expr = re.compile("([0-1][0-9]/[0-3][0-9]/[0-1][0-9])")

def getAllStats(text):
    """Expects 'text' to be a list of lines of html. Searches over each
    line and finds portion of 'text' that contains the information
    needed to process the box score and play-by-play

    If relevant text matches are not found, then throws exception.
    If everthing handled correctly, then returns the string subset
    for all stats, box score and play-by-play

    """

    start_index = None; end_index = None; mid_index = None
    start_text = 'Official Basketball Box Score'
    mid_text = 'Play-by-Play\r'
    end_text = '2nd period-only' # Break on final score instead???
    for i,line in enumerate(text):
        if start_text in line:
            start_index = i
            #print text[i:i+10]

        if mid_text in line: mid_index = i
        if end_text in line: end_index = i

    if (start_index is None):
        msg = "start_index not found, for string of: %s"%start_text
        raise IndexError(msg)
    if (mid_index is None):
        msg = "mid_index not found, for string of: %s"%mid_text
        raise IndexError(msg)
    if (end_index is None):
        msg = "end_index not found, for string of: %s"%end_text
        raise IndexError(msg)

    all_stats = text[start_index:end_index+4]
    box_score = text[start_index:mid_index]
    play_by_play = text[mid_index:end_index+4]

    return all_stats, box_score, play_by_play


def getRosters(box_score):
    """Parses the box_score-a list of strings-for the away team and
    roster, and the home team and roster

    Assumes: first 5 listings for VISITORS and HOME TEAM are the
    starters

    """

    home_team_name = ""
    away_team_name = ""
    home = []; away = []
    is_home = None  #Flag for putting roster slot into Home or Away
    for line in box_score:
        if 'VISITORS:' in line:
            line = line.split(',')[0]
            away_team_name = '_'.join(line.split()[1:-1])
            is_home = False
        if 'HOME TEAM:' in line:
            line = line.split(',')[0]
            home_team_name = '_'.join(line.split()[2:-1])
            #home_team_name = clean_name(home_team_name)
            is_home = True

        line_split = line.split(' ')
        if line_split[0].isdigit():
            # continue because there must have been junk before the
            # 'VISITORS' or 'HOME TEAM' portion of the box score
            if is_home is None: continue

            # else process it as a roster name and jersey number:
            # IMPORTANT: Assumes roster spot is formatted as:
            #  '## Last Name(s), First Name(s)...'
            # where '##' is jersey number and there are as many '.'
            # remaining as to fill up 23 total characters in the line.
            jersey = line[0:2]
            name = line[3:23].split('.')[0]
            # IF we want first, last name, should be pretty easy now.
            if is_home:
                starter = True if len(home) < 5 else False
                home.append({'name':name,'jersey':jersey,'starter':starter})
            else:
                starter = True if len(away) < 5 else False
                away.append({'name':name,'jersey':jersey,'starter':starter})

    logging.debug('Home team name: %s'%home_team_name)
    logging.debug('Away team name: %s'%away_team_name)

    return home, away, home_team_name, away_team_name

def getDate(box_score):
    """From box_score, get date that game was played, in format: MM/DD/YY
    at the beginning of the line.
    """

    for line in box_score:
        if bool(date_expr.match(line)):
            mm,dd,yy = line.split()[0].split('/')
            date_text = '20'+yy+'_'+mm+'_'+dd
            return date_text

    return None

def processPlay(event):
    """A "play" is defined as one single line of the play-by-play
    sheet. An "event" is either a "home play" or "away play", so per
    "play" there are up to two events. A play can also be any event
    that is recorded: "sub in", "sub out", "fg made", "fg attempt",
    "timeout", etc.

    A couple of distinct formatting assumptions are made (and if
    broken-the play will not be processed):
      1) At indices [48:53] of the event a timestamp is recorded
         (from 00:00 to 20:00), to mark at what point in the half
         the event was recorded.
      2) From index [0:47] any number of these string indices may
         be used to record a play for the HOME side.
      3) At index [67:], a play on the visitor's side may be
         recorded.
    """

    clockTime = event[48:53]
    home_event = event[:47]
    away_event = event[67:]
    if not bool(clock_expr.match(clockTime)): return None,None,None

    home_event = parseEvent(home_event)
    away_event = parseEvent(away_event)

    return home_event, away_event, clockTime


def parseEvent(event):
    """Returns the TEAM event stripping away player name info (for now)"""

    split = event.split()
    if len(split) <= 1: return None
    else:
        if 'by' in split:
            index = [i for i,x in enumerate(split) if x == 'by'][0]
            # Throw away "name" i.e. "by whom" is not recorded...
            return (' ').join(split[0:index])

        # Or, b/c it's substitution or timeout or something else...
        else: return (' ').join(split)

    return


def cleanName(table_name):
    """
    Quick function that drops non-alphanumeric characters, and
    whitespace, keeping only [A-Z], [a-z], [0-9], also '_' and '-'

    IMPORTANT: Run this on db names to prevent SQL injection!
    """
    return ''.join( chr for chr in table_name if (chr.isalnum() or chr == '_'
                                                  or chr == '-') )


def saveRoster(roster, teamname, dbfile, game_date):
    """Saves roster of teamname to sqlite database dbfile"""
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()

    # Create the new SQLite table for roster:
    # REDO THIS USING ''' '''?
    tablename = cleanName(teamname+'_roster_'+game_date)

    try:
        # First, drop table if it exists already
        query = 'DROP TABLE '+tablename
        cur.execute(query)
    except:
        pass

    logging.info("Creating table: %s"%tablename)
    create_table_query = 'CREATE TABLE '+tablename+'(Name TEXT, Jersey INT, Starter INT)'
    cur.execute(create_table_query)

    for player in roster:
        cur.execute('INSERT INTO '+tablename +
                    '''(Name, Jersey, Starter) VALUES(?,?,?)''',
                    (player['name'],player['jersey'],int(player['starter'])))

    # Unless you use 'with', need to commit your changes to db manually.
    conn.commit()

    loglevel = logging.root.getEffectiveLevel()
    if loglevel <= logging.INFO:
        # Display data entered:
        cur.execute('SELECT * from '+tablename+' ORDER BY Starter DESC, Name ASC')
        data = cur.fetchall()
        print tabulate(data,headers=["Name","Jersey","Starter"],tablefmt="grid")

    conn.close()

    return


def savePlayByPlay(frame, dbfile, game_date):
    """Saves DataFrame, frame,  to sqlite database dbfile"""

    conn = sqlite3.connect(dbfile)

    tablename = cleanName('PlayByPlay_'+game_date)
    logging.info('Creating table: %s'%tablename)
    df.to_sql(tablename,conn,flavor='sqlite',if_exists='replace')

    #loglevel = logging.root.getEffectiveLevel()
    #if loglevel <= logging.DEBUG:
    #    cur = conn.cursor()
    #    cur.execute('SELECT * from '+tablename+' limit 50')
    #    data = cur.fetchall()
    #    print tabulate(data,headers=['Clock','Home Evt','Away Evt'],tablefmt="grid")

    conn.close()

    return

parser = ArgumentParser(
    '''Collects Box score and play by play information from a base
    site and puts them into a database.''',
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('filename',metavar='STR',type=str, default='UCLA_2014_2015.db',
                    help='''Output filename for the database.''')
#parser.add_argument('--db_dir',metavar='DIR',type=str,default='UCLA_2014_2015',
#                    help='Database directory')
parser.add_argument('-v', '--verbose', action='count', default=None,
                    help='set verbosity level')
args = parser.parse_args()

set_verbosity(args.verbose)

BASE_URL = "http://www.uclabruins.com/SportSelect.dbml?SPSID=749889&SPID=126928&DB_OEM_ID=30500&Q_SEASON=2014"
logging.warn("Looking up game information from: %s"%BASE_URL)

# This finds the right links to the official box score:
soup_base = BeautifulSoup(urlopen(BASE_URL))
game_links = soup_base.findAll('a',{"target":'_STATS'})
urls = [lnk.get('href') for lnk in game_links]

# Stage 1:
#   For each url (link to box score and play by play):
#     1) Load roster, box_score, and all play-by-play events
#     2) Save each as a table to the season's sqlite3 db file


# Initialize database for saving all info:
dbfile = args.filename

processed = 0
unprocessed = 0
for i,url in enumerate(urls):
    if i == 0: continue  # Skip first exhibition game.

    try:
        logging.info("processing url: %s"%url)
        soup_game = BeautifulSoup(urlopen(url))

        # Now parse the box score text possession by possession
        all_lines = str(soup_game.prettify).split('\n')

        stats_full,box_score,play_by_play = getAllStats(all_lines)

        # 1) Store box score, build rosters
        # 2) Process event by event into a table/dataframe
        home_roster,away_roster,home_team,away_team = getRosters(box_score)
        game_date = getDate(box_score)

        home_events = []; away_events = []; time_stamps = []
        for play in play_by_play:
            hEvent, aEvent, tStamp = processPlay(play)
            if tStamp is None: continue
            home_events.append(hEvent)
            away_events.append(aEvent)
            time_stamps.append(tStamp)

        # Now put the lists of events and clock into data frame:
        df = DataFrame({'Clock': time_stamps,'Home Evt':home_events,
                        'Away Evt':away_events},
                       columns=['Clock','Home Evt','Away Evt'])

        # Saving all info to database
        #dbfile= os.path.join(args.db_dir,game_date+'_'+home_team+'_vs_'+away_team+'.db')
        logging.info('Using database: %s',dbfile)
        saveRoster(home_roster,home_team,dbfile,game_date)
        saveRoster(away_roster,away_team,dbfile,game_date)
        savePlayByPlay(df,dbfile,game_date)
        processed += 1

    except IndexError, e:
        logging.warn(
            "  Exception: %s\n...Skipping processing for this game..."%e)
        unprocessed += 1
    except:
        logging.warn(
            "  Exception Other: %s\n  ...Skipping processing for this game..."
            %sys.exc_info()[0])
        print "Full message: ",sys.exc_info()
        unprocessed += 1

fin_msg = "FINISHED! Processed %d games correnctly and "%processed
fin_msg+="failed to process %d games."%unprocessed
logging.warn(fin_msg)
