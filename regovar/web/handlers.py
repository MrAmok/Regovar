#!env/python3
# coding: utf-8
import ipdb; 


import os
import json
import aiohttp
import aiohttp_jinja2
import datetime
import time


from aiohttp import web, MultiDict
from urllib.parse import parse_qsl

from config import *
from core import *
# from web.tus import *








# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# COMMON TOOLS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def rest_success(response_data=None, pagination_data=None):
    """ 
        Build the REST success response that will encapsulate the given data (in python dictionary format)
        :param response_data:   The data to wrap in the JSON success response
        :param pagination_data: The data regarding the pagination
    """
    if response_data is None:
        results = {"success":True}
    else:
        results = {"success":True, "data":response_data}
    if pagination_data is not None:
        results.update(pagination_data)
    return web.json_response(results)



def rest_error(message:str="Unknow", code:str="0", error_id:str=""):
    """ 
        Build the REST error response
        :param message:         The short "friendly user" error message
        :param code:            The code of the error type
        :param error_id:        The id of the error, to return to the end-user. 
                                This code will allow admins to find in logs where exactly this error occure
    """
    results = {
        "success":      False, 
        "msg":          message, 
        "error_code":   code, 
        "error_url":    ERROR_ROOT_URL + code,
        "error_id":     error_id
    }
    return web.json_response(results)







def notify_all(data):
    msg = json.dumps(data)
    if 'msg' not in data.keys() or data['msg'] != 'hello':
        log ("API_rest Notify All: {0}".format(msg))
    for ws in WebsocketHandler.socket_list:
        ws[0].send_str(msg)

# Give to the core the delegate to call to notify all users via websockets
regovar.notify_all = notify_all






# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# MISC HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class ApiHandler:
    def __init__(self):
        pass

    def welcom(self, request):
        return rest_success({
            "api_url": HOST_P,
            "title": "Regovar Service API",
            "version": "alpha",
            "format_supported": ["json"],
            "website" : "regovar.org"
        })



    def config(self, request):
        return rest_success({
            "host": HOST_P,
            "pagination_default_range": RANGE_DEFAULT,
            "pagination_max_range": RANGE_MAX,
            "export_modules": annso.export_modules, 
            "import_modules": annso.import_modules,
            "report_modules": annso.report_modules
            })



class WebsocketHandler:
    socket_list = []
    async def get(self, request):
        peername = request.transport.get_extra_info('peername')
        if peername is not None:
            host, port = peername

        ws_id = "{}:{}".format(host, port)
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        WebsocketHandler.socket_list.append((ws, ws_id))
        msg = {'msg':'hello', 'data': [[str(_ws[1]) for _ws in WebsocketHandler.socket_list]]}
        notify_all(msg)

        try:
            async for msg in ws:
                if msg.tp == aiohttp.MsgType.text:
                    if msg.data == 'close':
                        log ('CLOSE MESSAGE RECEIVED')
                        await ws.close()
                    else:
                        # Analyse message sent by client and send response if needed
                        data = msg.json()
                        if data['msg'] == 'user_info':
                            log('WebsocketHandler {0} '.format(data['msg']))
                            pass
                        elif msg.tp == aiohttp.MsgType.error:
                            log('ws connection closed with exception {0}'.format(ws.exception()))
        finally:
            WebsocketHandler.socket_list.remove((ws, ws_id))

        return ws



async def on_shutdown(app):
    log("SHUTDOWN SERVER... CLOSE ALL")
    for ws in WebsocketHandler.socket_list:
        await ws[0].close(code=999, message='Server shutdown')



 



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# USER HANDLER
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
class UserHandler:
    def __init__(self):
        pass


    def all(self, request):
        return rest_success("all")

    def add(self, request):
        return rest_success("add")

    def get(self, request):
        return rest_success("get")

    def edit(self, request):
        return rest_success("edit")

    def login(self, request):
        return rest_success("login")

    def logout(self, request):
        return rest_success("logout")