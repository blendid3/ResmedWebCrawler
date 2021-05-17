import scrapy
from flask import Flask, redirect
from flask_restful import Api, Resource, reqparse
import os
import requests
import json
import time
import random
import logging

app = Flask(__name__)
api = Api(app)

# Get port from environment variable or choose 9000 as local default
port = int(os.getenv("PORT", 9000))

class RTviewHealthCheck(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('format', type=str, help='format of the message to be displayed: text/json')
        args = parser.parse_args()

        pass


api.add_resource(RTviewHealthCheck, "/<string:env>/top/<int:limit>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
