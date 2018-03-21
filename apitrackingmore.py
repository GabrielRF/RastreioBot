import sys
import json
import urllib.request
import urllib.parse
import http.client
# arquivo original em
# https://www.trackingmore.com/api-class_python.html
headers={"Content-Type":"application/json",
        "Trackingmore-Api-Key":"YOUR API KEY",
        'X-Requested-With':'XMLHttpRequest'
        }
class track:

    def trackingmore(requestData, urlStr, method):
        if method == "get":
            url = 'http://api.trackingmore.com/v2/trackings/get'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl, headers=headers)
            result = urllib.request.urlopen(req).read()
        elif method == "post":
            url = 'http://api.trackingmore.com/v2/trackings/post'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="POST")
            result = urllib.request.urlopen(req).read()
        elif method == "batch":
            url = 'http://api.trackingmore.com/v2/trackings/batch'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="POST")
            result = urllib.request.urlopen(req).read()
        elif method == "codeNumberGet":
            url = 'http://api.trackingmore.com/v2/trackings'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="GET")
            result = urllib.request.urlopen(req).read()
        elif method == "codeNumberPut":
            url = 'http://api.trackingmore.com/v2/trackings'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="PUT")
            result = urllib.request.urlopen(req).read()
        elif method == "codeNumberDel":
            url = 'http://api.trackingmore.com/v2/trackings'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="DELETE")
            result = urllib.request.urlopen(req).read()
        elif method == "realtime":
            url = 'http://api.trackingmore.com/v2/trackings/realtime'
            RelUrl = url + urlStr
            req = urllib.request.Request(RelUrl,requestData.encode('utf-8'), headers=headers,method="POST")
            result = urllib.request.urlopen(req).read()
        return result




