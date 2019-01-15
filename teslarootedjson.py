""" Simple Python class to access the Tesla JSON API
https://github.com/gglockner/teslajson
Reworked to talk directly to in-car RemoteAPI by verygreen

The Tesla JSON API is described at:
http://docs.timdorr.apiary.io/

Example:

import teslarootedjson
c = teslarootedjson.Connection('remoteapi_url', 'debugsvc_url', 'VIN')
v = c.vehicles[0]
v.wake_up()
v.data_request('charge_state')
v.command('charge_start')


Modified by mephisto to get rid of access to a thirdparty

"""

try: # Python 3
    from urllib.parse import urlencode
    from urllib.request import Request, build_opener
    from urllib.request import ProxyHandler, HTTPBasicAuthHandler, HTTPHandler
except: # Python 2
    from urllib import urlencode
    from urllib2 import Request, build_opener
    from urllib2 import ProxyHandler, HTTPBasicAuthHandler, HTTPHandler
import json
import datetime
import calendar

from apiconfig import *

class Connection(object):
    """Connection to Tesla Motors API"""
    def __init__(self,
            RemoteAPIURL='',
            DebugServiceURL='',
            VIN=''):

        """Initialize connection object

        Required parameters:
        RemoteAPIURL: Exposed in-car remote api URL
        DebugServiceURL: Exposed in-car debugservice url
        VIN: Car VIN (possible to get by without, but produces warnings in logs)

        """
        self.baseurl = RemoteAPIURL
        self.debugurl = DebugServiceURL

        if VIN:
            self.VIN = VIN;
        else:
            # get the vin somehow - TBD
            self.VIN = 'blah'

        self.head = {"X-SSL-Client-S-CN": self.VIN}
        self.vehicles = [Vehicle(self)]
        self.vehicles[0]['vin'] = self.VIN

        self.vehicles[0]['display_name'] = self.debug_get_var("GUI_vehicleName")
        result = self.debug_get_var("VAPI_isLocked")
#        if result == "true":
#            self.vehicles[0]['state'] = "asleep"
#        else:
        self.vehicles[0]['state'] = "online"

    def get(self, command):
        """Utility command to get data from API"""
        return self.post(command, None)

    def debug_get_var(self, varname):
        """Utility command to get data from API"""
        result = self.__open("/get_data_value?valueName=%s" % (varname), baseurl=self.debugurl)
        return result['value']

    def post(self, command, data={}):
        """Utility command to post data to API"""
        # XXX
        return self.__open("/%s" % (command), headers=self.head, data=data)

    def __open(self, url, headers={}, data=None, baseurl=""):
        """Raw urlopen command"""
        if not baseurl:
            baseurl = self.baseurl
        req = Request("%s%s" % (baseurl, url), headers=headers)
        try:
            req.data = urlencode(data).encode('utf-8') # Python 3
        except:
            try:
                req.add_data(urlencode(data)) # Python 2
            except:
                pass

        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))


class Vehicle(dict):
    """Vehicle class, subclassed from dictionary.

    There are 3 primary methods: wake_up, data_request and command.
    data_request and command both require a name to specify the data
    or command, respectively. These names can be found in the
    Tesla JSON API."""
    def __init__(self, connection):
        """Initialize vehicle class

        Called automatically by the Connection class
        """
        super(Vehicle, self).__init__()
        self.connection = connection

    def data_request(self, name):
        """Get vehicle data"""
        result = self.connection.get('vehicle_data?endpoints=%s' % name)
        return result[name]

    def wake_up(self):
        """Wake the vehicle"""
        return self.post('wake_up')

    def command(self, name, data={}):
        """Run the command for the vehicle"""
        return self.post('command/%s' % name, data)

    def get(self, command):
        """Utility command to get data from API"""
        return self.connection.get('vehicles/%i/%s' % (self['id'], command))

    def post(self, command, data={}):
        """Utility command to post data to API"""
        return self.connection.post('vehicles/%i/%s' % (self['id'], command), data)
