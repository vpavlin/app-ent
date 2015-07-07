#!/usr/bin/env python

import logging
import context
from constants import __ATOMICAPPVERSION__
from flask import Flask, jsonify, request
from flask.ext.restful import Api, Resource

logger = logging.getLogger(__name__)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    logger.info("shutting down rest app server")
    func()

class StatusList(Resource):

    def get(self):
        return jsonify(items=context.globalCtx.getStatus())


class ExitServer(Resource):

    def post(self):
        shutdown_server()
        return 'Server shutting down...'

class Endpoints(Resource):

    def get(self):
        epl = []
        epl.append("/")
        epl.append("/atomicapp-run/version")
        epl.append("/atomicapp-run/api/v"+__ATOMICAPPVERSION__+"/quit")
        epl.append("/atomicapp-run/api/v"+__ATOMICAPPVERSION__+"/status")
        return jsonify(items=epl)

class Version(Resource):

    def get(self):
        return __ATOMICAPPVERSION__

class Rest(object):

    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.app.ep = []
        self.url = "/atomicapp-run/api/v"+__ATOMICAPPVERSION__;
        self.api.add_resource(Endpoints, "/")
        self.api.add_resource(Version, "/atomicapp-run/version")
        self.api.add_resource(ExitServer, self.url + "/quit")
        self.api.add_resource(StatusList, self.url + "/status")


    def addResource(self, cls, routeStr):
        self.api.add_resource(cls, routeStr)

    def run(self, pdebug, pport):
        logger.info("rest endpoint is http://localhost:"+str(pport)+""+self.url);
        self.app.run(debug=pdebug, port=pport, host='0.0.0.0')

