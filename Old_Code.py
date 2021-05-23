import flask
import scrapy
from flask import Flask, redirect
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
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

TIBCO_HOSTNAME = {
    "PT": ["US1-AIREMS-T01.ec2.local"],
    "PT1": ["US1-AIREMS-T11.ec2.local"],
    "PT2": ["10.130.69.25", "10.130.69.40"],
    "PROD": ["10.130.65.51", "10.130.65.52"]
}

SERVER_URL = {
    "PT": "http://us1-airtmc-m01.ec2.local:8080",
    "PT1": "http://us1-airtmc-m01.ec2.local:8080",
    "PT2": "http://us1-airtmc-m01.ec2.local:8080",
    "PROD": "http://us1-airtmc-m03.ec2.local:8080"
}

# proxies = {
#     'http': 'http://proxy.ec2.local:32611',
#     'https': 'http://proxy.ec2.local:32611',
# }
proxies = []

def formatMsg(queue_list, context_type):
    for q in queue_list:
        q['pend_size'] = '{}MB'.format(q['pend_size'])

    if context_type == 'json':
        return queue_list
    else:
        concat = ','.join(
            ['{}: {}({})'.format(entry['queue_name'], int(entry['pend_msgs']), entry['pend_size']) for entry in
             queue_list])
        return concat


def sendSlackNotification(channelName, msg):
    postData = {}
    postData['message'] = msg
    postData['color'] = 'red'
    url = 'http://us1-airmgo-t01.ec2.local/notificationToHipchat?room=' + channelName
    requests.post(url, data=postData)


def sendAlert(env, queue_list):
    if env == 'PROD':
        for q in queue_list:
            if q['pend_size'] > 2048 or q['pend_msgs'] > 80000:
                sendSlackNotification('nightly_automation', formatMsg(queue_list, 'text'))
                return

    if env == 'PT2':
        for q in queue_list:
            if q['pend_size'] > 2048 or q['pend_msgs'] > 80000:
                sendSlackNotification('pt2_notifications', formatMsg(queue_list, 'text'))
                return
    return


def getDisplay(env):
    path = '/emsmon/getdisplay.jsp?display=ems_title_panel&nl=1&lpnm=north'
    url = SERVER_URL[env] + path

    resp = requests.get(url, proxies=proxies)

    rtvRefrDisplayURL = ''
    dmod = ''
    pnl = ''
    resizeMode = ''

    for line in resp.text.splitlines():
        line = line.strip(';')

        if line.startswith('rtdisp.dataModTime'):
            val = line.split('=')[1]
            dmod = val.strip()

        if line.startswith('rtdisp.serverPanelID'):
            val = line.split('=')[1]
            pnl = val.strip("'")

        if line.startswith('rtdisp.setResizeMode'):
            value = line.split('(')[1]
            resizeMode = value.split(',')[0]

    return 'dmod={}&um={}&pnl={}'.format(dmod, resizeMode, pnl)


class RTviewHealthCheck(Resource):
    def get(self, env, limit):
        parser = reqparse.RequestParser()
        parser.add_argument('format', type=str, help='format of the message to be displayed: text/json')
        args = parser.parse_args()

        contentType = 'json'
        if args['format'] != None and args['format'].lower() == 'text':
            contentType = 'text'

        env = env.upper()
        params = getDisplay(env)

        path = '/emsmon/xmlreq.jsp?op=refresh&rand=86546'
        url = SERVER_URL[env] + path

        for tibco_url in TIBCO_HOSTNAME[env]:
            bodydata = 'display=ems_allqueues_forserver_table&div=rtv&nl=1&ddobj=N672&setmapvar=%24emsServer&ddval=tcp%3A%2F%2F' + tibco_url + '%3A7222&' + params

            resp = requests.post(url, data=bodydata, proxies=proxies)

            pattern = 'rtvtbl.rtv_rowdata'
            exitLoop = 'rtvtbl.rtv_coldata_formatted'
            patternFound = False
            queuelist = []

            for line in resp.text.splitlines():
                logging.info(line)

                if exitLoop in line:
                    break

                if patternFound:
                    trimmed = line.strip().strip(',[]')
                    cols = trimmed.split(',')

                    if len(cols) == 39:
                        hostname = cols[1].strip('"')
                        if hostname == 'tcp://' + tibco_url + ':7222':
                            nm = cols[0].strip('"')
                            pend_msgs = float(cols[6])
                            pend_size = round(float(cols[7]) / 1000000, 1)
                            entry = {'queue_name': nm, 'pend_msgs': pend_msgs, 'pend_size': pend_size}
                            queuelist.append(entry)

                if pattern in line:
                    patternFound = True

            if len(queuelist) != 0:
                break

        queuelist.sort(key=lambda x: x['pend_msgs'], reverse=True)
        limit = int(limit)

        queuelist = queuelist[:limit]
        queuelist = [q for q in queuelist if q['pend_msgs'] > 0]

        sendAlert(env, queuelist)

        return formatMsg(queuelist, contentType), 200


api.add_resource(RTviewHealthCheck, "/<string:env>/top/<int:limit>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)