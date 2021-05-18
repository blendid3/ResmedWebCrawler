# what's reqparse
import flask
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask import Flask, redirect
from flask_restful import Api, Resource, reqparse
import os
import requests
app = Flask(__name__)
api = Api(app)



videos = {}
class myFirstWebsite(Resource):
    def get(self, video_id):
        return videos[video_id]

    # def put(self, video_id):
    #     return
    # pass

api.add_resource(myFirstWebsite, "/<int:id>")
if __name__ == '__main__':
    app.run(host='0.0.0.0')