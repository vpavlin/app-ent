#!/usr/bin/env python

import logging
import utils
import constants
logger = logging.getLogger(__name__)


class Config(object):
    app = ""
    app_id = ""
    statusList = []
    #PENDING,ERROR,COMPLETED,
    status = "PENDING"
    status_id_count = 0
    persist = False
    db_key = "status"

    def setApp(self, app):
        self.app = app

    def setAppId(self, appid):
        self.app_id = appid

    def __init__(self, ppersist):
        self.persist = ppersist
        if self.persist:
            utils.addShelveKV(constants.DEFAULT_DB, self.db_key, [])

    def addStatus(self, message, data="", status_type="PENDING"):
        logger.debug("Ctx status updated :" + message)
        self.status_id_count += 1
        tmp = { "status_id" : self.status_id_count, "app" : self.app, "app_id" : self.app_id, 
            "status_message" : message, "status_data" : data, "status" : status_type}
        if self.persist:
            utils.appendShelveKV(constants.DEFAULT_DB, self.db_key, tmp)
        else:
            self.statusList.append(tmp)

    def getStatus(self):
        if self.persist:
            return utils.getShelveKV(constants.DEFAULT_DB, self.db_key)
        else:
            return self.statusList


globalCtx = None

