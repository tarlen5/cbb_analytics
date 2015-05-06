#! /usr/bin/env python
#
# ProcessGames.py
#
# author: Timothy C. Arlen
#         timothyarlen@gmail.com

#
# date:   20 April 2015
#
# Process all games' play by play, loaded from local sqlite database
# files, saved from online play by play. First task will be to get +/-
# for 5 man units!
#

import os
from glob import glob
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import sqlite3
import pandas as pd
from pandas import DataFrame, Series
import pandas.io.sql as sql
from tabulate import tabulate

from LogUtils import logging, set_verbosity, set_frame_display


def processGame(df):

    set_frame_display(len(df),max_rows=50)
    print "\ndf: \n\n",df

    print "columns: ",df.columns
    home_events = df['Home Evt']
    away_events = df['Away Evt']

    # DIAGNOSTICS - This will go in next script to process raw data!
    home_events = set(home_events)
    away_events = set(away_events)
    print "\n\n==>SET OF HOME PLAYS: "
    for event in home_events: print "  ",event
    print "\n\n==>SET OF AWAY PLAYS: "
    for event in away_events: print "  ",event
    print "\nAWAY - HOME: "
    for play in away_events.difference(home_events): print "  ",play
    print "\nHOME - AWAY: "
    for play in home_events.difference(away_events): print "  ",play

    print "\nThen set of real events is: "
    for play in away_events.intersection(home_events): print "  ",play


    raw_input("PAUSED...")

    return

parser = ArgumentParser('Process all game information from database files',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('--db_dir',metavar='DIR',type=str,default='UCLA_2014_2015_db',
                    help='Database directory')
parser.add_argument('-v', '--verbose', action='count', default=None,
                    help='set verbosity level')
args = parser.parse_args()

set_verbosity(args.verbose)

dbfiles = glob(os.path.join(args.db_dir,'*.db'))

for dbfile in dbfiles:
    logging.info("processing file: %s"%dbfile)
    # Open db file, connect to db and print information
    con = sqlite3.connect(dbfile)
    df_PlayByPlay =  sql.read_sql('select * from PlayByPlay',con)
    # Also get home/away roster...SHOW ALL TABLES??

    con.close()
    # Now give raw data frame to function for processing into useful
    # play by play (or possession by possession) information
    processGame(df_PlayByPlay)
