# -*- coding: utf-8 -*-
import logging
from freemqtt.db.sqlite import getDatabaseInstance

if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, 
                         format='[%(asctime)s %(filename)s:%(lineno)d] %(levelname)s: %(message)s',
                         datefmt  = '%Y%m%d %H:%M:%S'
                       )
    logging.info("Initialize Feemqtt Database now, please wait...")
    db = getDatabaseInstance()
    db.dropTables()
    db.createTables()
    dbsession = db.getSessionClass()()
    dbsession.close()
    logging.info("Initialize SQLite database done!")
