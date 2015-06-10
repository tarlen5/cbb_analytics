cbb_analytics
=============

College Basketball analytics software for analyzing trends in 5 man units and rosters. Originally written to analyze the 2014 - 2015 UCLA basketball season.

* Stage 1: Load games by webscraping the base url, then store data frames containing event play by play as sqlite3 database tables, with rosters for both sides for each game. Each season gets its own database file.

* Stage 2: Process games by loading into a DataFrame and using machine learning algorithms to search for trends in 5 man units and other roster moves.

### Requirements

Installing this package requires the following 

* [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/)
* [tabulate](https://pypi.python.org/pypi/tabulate)
* [pandas](http://pandas.pydata.org)

