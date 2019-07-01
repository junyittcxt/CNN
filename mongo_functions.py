"""Contains common functions to interface with MongoDB"""

import pymongo

#TODO: move these to a credentials file
username = "cxtanalytics"
password = "3.1415cxt"
mongoport = "192.168.1.110:27017"
portfolio_dbname = "MLProduction"


def get_portfolio_db(portfolio_dbname = "MLProduction", username = "cxtanalytics", password = "3.1415cxt", mongoport = "192.168.1.110:27017"):
    """Returns database storing strategies"""

    client = pymongo.MongoClient('mongodb://%s:%s@%s' % (username, password, mongoport))
    db = client[portfolio_dbname]

    return db
