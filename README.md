cbb_analytics
=============

College Basketball analytics software for analyzing trends in 5 man units and rosters. Originally written to analyze the 2014 - 2015 UCLA basketball season.

* Stage 1: ```LoadAllGames.py```. Load games by webscraping the base url, following the urls for individual game play by play information, then store data frames containing event play by play as an sqlite3 database table, with rosters for both sides for each game. Each raw play by play table and each side's roster gets its own table in the database, tagged with the date in format: yyyy-mm-dd.

* Stage 2: (currently in the notebook ```notebooks/Explore_Play_By_Play_DB.ipynb``` but will be made into its own script when finished). Process each game by loading each game's `play_by_play` and roster table into a `game_table` DataFrame with the time stamps of each player on the court and the running total score for each side. This will be used to compute the strength of each lineup, accounting for factors such as: strength of opponent, leverage of the situation, strength of opponent's lineup, and any other factors deemed important.

### Requirements

Installing this package requires the following 

* [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/)
* [tabulate](https://pypi.python.org/pypi/tabulate)
* [pandas](http://pandas.pydata.org)

