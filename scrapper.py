import re, os, sys, urllib2
from urllib import quote

import readline, rlcompleter; readline.parse_and_bind("tab: complete")

def get_input():
    pass

"""
only several key POST parameters are needed.
2012-02-03 done fuzzing via Fiddler 2

__VIEWSTATE=cluster_fuck_of_b64_stream&
ddlsegment=18237141& //actual internal bus ID
rpt%24ctl27%24imgBtn.x=6&
rpt%24ctl27%24imgBtn.y=6&
rpt%24ctl27%24hidSngserialID=28&
rpt%24ctl27%24hidDualserialID=28&



__VIEWSTATE=cluster_fuck_of_b64_stream&
ddlRoute=53& //this one used to switch Bus No.
ddlSegment=17082410& //this one used to switch forward/backword routes.
"""

URL_ENTRY = 'http://www.cdgjbus.com:8802/BusTravelGuide/Default.aspx'
from conf import DEFAULT_VIEWSTATE

dbg = None

class Transit(object):
    # this class is a state machine that handles transit data.
    # one instance per ViewState
    def proc_viewstate(self, html):
        self.viewstate = re.search(r' name="__VIEWSTATE" id="__VIEWSTATE" value="([^"]+)"', html)
        self.viewstate = self.viewstate.group(1) if self.viewstate else ''
        self.viewstate = '__VIEWSTATE=' + quote(self.viewstate)
        return self.viewstate
    def req(self, url, content=None, headers={}):
        headers.setdefault('User-agent', '')
        if content:
            params = content.split('&')
            sig = '__VIEWSTATE='
            for i, p in enumerate(params):
                if p[:len(sig)] == sig:
                    del params[i]
                if not p:
                    del params[i]
            params.append(self.viewstate)
            content = '&'.join(params)
        html = urllib2.urlopen(urllib2.Request(url, content, headers)).read().replace('\r', '').replace('\n', '')
        self.proc_viewstate(html)
        return html
    def get_stops(self, route_id, html=''):
        # get a list of station names by ddlSegment

            # only HTTP when necessary
        if route_id not in self._route_stops.keys():
            html = html or self.req(URL_ENTRY, '%s&ddlSegment=%s' % (self.viewstate, route_id))
            s = re.findall(r'_lblStation">([^<]+)</span>', html)
            # offset is the .NET control ID offset on the page.
            offset = re.search(r'rpt\$ctl\d+\$hidSngserialID"[^>]+value="(\d+)".*?'
                'rpt\$ctl\d+\$hidDualserialID"[^>]+value="(\d+)', html)
            # substract
            offset = int.__sub__(*map(int, offset.groups()[::-1]))
            self._route_stops[route_id] = s
            self.route_offset[route_id] = offset
        return self._route_stops[route_id]
    def get_routes(self, html):
        # Get both route names of ShangXing & XiaXing
        r = re.search(r' name="ddlSegment" (.*)</select>', html, re.M)
        r = re.findall(r'(selected="selected")? value="([^"]+)">([^"]+)</', r.group(1))
        print r
        # routes = {'route_id': (offset, [stations]) }
        self._route_stops = {}
        self.route_names = {}
        self.route_offset = {}
        for x in r:
            # x = ('selected', route_id, route_names)
            self.route_names[x[1]] = x[2]
            if x[0]:
                self._route_stops[x[1]] = self.get_stops(x[1], html)
                self.last_route_id = x[1]
        return self.route_names.keys()
    def __init__(self, bus_no):
        # this function changes a lot.

        self.bus_no = bus_no

        # initial page request
        html = self.req(URL_ENTRY)
        # get ddlSegment as the next req parameter
        self.get_routes(html)

        # second page req
        # be sure to provide a random but exist ddlSegment, or you can not get ddlSegment offsets
        params = 'ddlRoute=%s&ddlSegment=%s&__EVENTTARGET=ddlRoute' % (
            bus_no,
            self.last_route_id
        )
        html = self.req(URL_ENTRY, params)
        self.get_routes(html)
    @property
    def route_stops(self):
        return self._route_stops
    @route_stops.setter
    def route_stops(self, value):
        self._route_stops = value
    def last_stop(self, route_id, station_index):
        # get nearest bus info by station_index.
        # station_index start with 0
        station_index = int(station_index)
        route = self.get_stops(route_id)
        # self.route.setdefault(route_id, self.get_route(route_id))
        if 0 <= station_index < len(route):
            # construct HTTP POST data
            data = '%s&ddlRoute=%s&ddlsegment=%s&'\
                'rpt%%24ctl%02d%%24imgBtn.x=1&'\
                'rpt%%24ctl%02d%%24imgBtn.y=1&'\
                'rpt%%24ctl%02d%%24hidSngserialID=%s&'\
                'rpt%%24ctl%02d%%24hidDualserialID=%s&' % (
                    self.viewstate, self.bus_no, route_id,
                    station_index,
                    station_index,
                    station_index, station_index+1,
                    station_index, station_index+1+self.route_offset[route_id]
                )
            html =  self.req(URL_ENTRY, data)
            print 'recv data', len(html), route_id, route[station_index]
            return re.findall(r'\/td><td>([^<]+)<\/td><td> ([\d:]+)<\/td><td>(\d+)<\/td>', html)
            # test: $ python -i -c "from scrapper import *;a=Transit(56)"
            # test: >>> a.last_stop('17082410', 4)
        else:
            # wrong call
            print 'wrong?', station_indexa
            return []

# a.last_stop('17082410', 6)
# a.last_stop('17082411', 14)

if '__main__' == __name__:
    bus = Transit(56)
    seg1, seg2 = bus.route_names.keys()