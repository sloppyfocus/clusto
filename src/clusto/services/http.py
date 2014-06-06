#!/usr/bin/env python
try:
    import simplejson as json
except ImportError:
    import json

from webob import Request, Response
from traceback import format_exc
from urllib import unquote_plus
import re
import os

from clusto.drivers import Driver, IPManager
import clusto.script_helper
import clusto

from clusto.services.config import conf, get_logger
log = get_logger('clusto.http', 'INFO')

conf = clusto.script_helper.load_config(os.environ.get('CLUSTOCONFIG', '/etc/clusto/clusto.conf'))
clusto.connect(conf)


def unclusto(obj):
    '''
    Convert an object to a representation that can be safely serialized into
    JSON.
    '''
    if type(obj) in (str, unicode, int) or obj is None:
        return obj
    if isinstance(obj, clusto.Attribute):
        return {
            'key': obj.key,
            'value': unclusto(obj.value),
            'subkey': obj.subkey,
            'number': obj.number,
            'datatype': obj.datatype
        }
    if issubclass(obj.__class__, Driver):
        return '/%s/%s' % (obj.type, obj.name)
    return str(obj)


def dumps(request, obj, **kwargs):
    result = json.dumps(obj, indent=2, sort_keys=True, **kwargs)
    if 'callback' in request.params:
        callback = request.params['callback']
        result = '%s(%s)' % (callback, result)
        content_type = 'text/javascript'
    else:
        content_type = 'application/json'
    return Response(result, content_type=content_type, **kwargs)


def loads(request, obj):
    return json.loads(obj)


class EntityAPI(object):
    def __init__(self, obj):
        self.obj = obj
        self.url = '/%s/%s' % (self.obj.type, self.obj.name)

    def _dict(self):
        result = {
            'object': self.url,
            'driver': self.obj.driver,
        }

        attrs = []
        for x in self.obj.attrs():
            attrs.append(unclusto(x))
        result['attrs'] = attrs
        result['contents'] = [unclusto(x) for x in self.obj.contents()]
        result['parents'] = [unclusto(x) for x in self.obj.parents()]
        result['actions'] = [x for x in dir(self) if not x.startswith('_') and callable(getattr(self, x))]
        return result

    def addattr(self, request):
        '''
        Add an attribute to this object.

        Requires HTTP parameters "key" and "value"
        Optional parameters are "subkey" and "number"
        '''
        kwargs = dict(request.params.items())
        self.obj.add_attr(**kwargs)
        return self.show(request)

    def setattr(self, request):
        '''
        Set an attribute on this object.

        Requires HTTP parameters "key" and "value"
        Optional parameters are "subkey" and "number"
        '''
        kwargs = dict(request.params.items())
        if 'number' in kwargs:
            kwargs['number'] = int(kwargs['number'])
        self.obj.set_attr(**kwargs)
        return self.show(request)

    def delattr(self, request):
        '''
        Delete an attribute from this object.

        Requires HTTP parameter "key"
        '''
        self.obj.del_attrs(request.params['key'])
        return self.show(request)

    def attrs(self, request):
        '''
        Query attributes from this object.
        '''
        result = {
            'attrs': []
        }
        kwargs = dict(request.params.items())
        for attr in self.obj.attrs(**kwargs):
            result['attrs'].append(unclusto(attr))
        return dumps(request, result)

    def insert(self, request):
        '''
        Insert an object into this object

        Requires a "device" attribute, which is the absolute URL path to the
        object to be inserted.

        For example: /pool/examplepool/insert?object=/server/exampleserver
        '''
        device = request.params['object'].strip('/').split('/')[1]
        device = clusto.get_by_name(device)
        self.obj.insert(device)
        return self.show(request)

    def remove(self, request):
        '''
        Remove a device from this object.

        Requires a "device" attribute, which is the absolute URL path to the
        object to be removed.

        For example: /pool/examplepool/remove?object=/server/exampleserver
        '''
        device = request.params['object'].strip('/').split('/')[1]
        device = clusto.get_by_name(device)
        self.obj.remove(device)
        return self.show(request)

    def show(self, request):
        '''
        Returns attributes and actions available for this object.
        '''
        search_parents = bool(request.params.get('search_parents', False))
        result = {}
        result['object'] = self.url
        result['driver'] = self.obj.driver

        attrs = []
        for x in self.obj.attrs():
            attrs.append(unclusto(x))
        result['attrs'] = attrs
        result['contents'] = [unclusto(x) for x in self.obj.contents()]
        result['parents'] = [unclusto(x) for x in
                             self.obj.parents(search_parents=search_parents)]
        result['actions'] = [x for x in dir(self) if not x.startswith('_') and callable(getattr(self, x))]

        return dumps(request, result)


class PortInfoAPI(EntityAPI):
    def ports(self, request):
        '''
        Returns a list of ports within this object and any information about
        connections between those ports and other devices.
        '''
        result = {}
        result['object'] = self.url
        result['ports'] = []
        for port in self.obj.port_info_tuples:
            porttype, portnum, otherobj, othernum = [unclusto(x) for x in port]
            result['ports'].append({
                'type': porttype,
                'num': portnum,
                'other': otherobj,
                'othernum': othernum,
            })

        return dumps(request, result)

    def set_port_attr(self, request):
        kwargs = {}
        params = request.params
        for arg in ('porttype', 'portnum', 'key', 'value'):
            if not arg in params:
                return Response(status=400, body='Required argument "%s" is missing\n' % arg)
            kwargs[arg] = params[arg]

        try:
            kwargs['portnum'] = int(kwargs['portnum'])
        except ValueError:
            return Response(status=400, body='portnum must be an integer\n')

        self.obj.set_port_attr(**kwargs)
        return Response(status=200)

    def get_port_attr(self, request):
        kwargs = {}
        params = request.params
        for arg in ('porttype', 'portnum', 'key'):
            if not arg in params:
                return Response(status=400, body='Required argument "%s" is missing\n' % arg)
            kwargs[str(arg)] = params[arg]

        try:
            kwargs['portnum'] = int(kwargs['portnum'])
        except ValueError:
            return Response(status=400, body='portnum must be an integer\n')

        return dumps(request, self.obj.get_port_attr(**kwargs))


class RackAPI(EntityAPI):
    def insert(self, request):
        '''
        Insert a device into a rack.

        This method is overridden to require a "ru" parameter in addition to
        "device"

        Example: /rack/examplerack/insert?object=/server/exampleserver&ru=6
        '''
        device = request.params['object'].strip('/').split('/')[1]
        device = clusto.get_by_name(device)
        self.obj.insert(device, int(request.params['ru']))
        return self.contents(request)


class ResourceAPI(EntityAPI):
    def allocate(self, request):
        '''
        Allocate a new object of the given type
        '''
        driver = clusto.DRIVERLIST[request.params['driver']]
        device = self.obj.allocate(driver)
        return dumps(request, unclusto(device), status=201)


class QueryAPI(object):
    @classmethod
    def get_entities(self, request):
        kwargs = {'attrs': []}
        for k, v in request.params.items():
            if k in ('format', 'callback'):
                continue
            v = loads(request, unquote_plus(v))
            kwargs[str(k)] = v

        attrs = []
        for attr in kwargs['attrs']:
            attrs.append(dict([(str(k), v) for k, v in attr.items()]))
        kwargs['attrs'] = attrs

        result = [unclusto(x) for x in clusto.get_entities(**kwargs)]
        return dumps(request, result)

    @classmethod
    def get_by_name(self, request):
        if not 'name' in request.params:
            return Response(status=400, body='400 Bad Request\nYou must specify a "name" parameter\n')
        name = request.params['name']
        obj = clusto.get_by_name(name)
        api = EntityAPI(obj)
        return api.show(request)

    @classmethod
    def get(self, request):
        if not 'name' in request.params:
            return Response(status=400, body='400 Bad Request\nYou must specifiy a "name" parameter\n')
        name = request.params['name']

        result = clusto.get(name)
        if result is None:
            return Response(status=404, body='404 Not Found\n')

        result = [EntityAPI(x)._dict() for x in result]
        return dumps(request, result)

    @classmethod
    def get_from_pools(self, request):
        if not 'pools' in request.params:
            return Response(status=400, body='400 Bad Request\nYou must specify at least one pool\n')
        pools = request.params['pools'].split(',')

        if 'types' in request.params:
            clusto_types = request.params['types'].split(',')
        else:
            clusto_types = None

        result = [unclusto(x) for x in clusto.get_from_pools(pools, clusto_types)]
        return dumps(request, result)

    @classmethod
    def get_ip_manager(self, request):
        if not 'ip' in request.params:
            return Response(status=400, body='400 Bad Request\nYou must specify an IP\n')

        try:
            ipman = IPManager.get_ip_manager(request.params['ip'])
        except:
            return Response(status=404, body='404 Not Found\n')
        return dumps(request, unclusto(ipman))


class ClustoApp(object):
    def __init__(self):
        self.urls = [
            ('^/favicon.ico$',
                self.notfound),
            ('^/search$',
                self.search),
            ('^/query/(?P<querytype>[a-z_]+)',
                self.query_delegate),
            ('^/(?P<objtype>\w+)/(?P<name>[-\w0-9]+)/(?P<action>\w+)',
                self.action_delegate),
            ('^/(?P<objtype>\w+)/(?P<name>[-\w0-9]+)',
                self.action_delegate),
            ('^/(?P<objtype>\w+)',
                self.types_delegate),
            ('^/',
                self.default_delegate),
        ]
        self.urls = [(re.compile(pattern), obj) for pattern, obj in self.urls]

        self.types = {
            'server': PortInfoAPI,
            'consoleserver': PortInfoAPI,
            'networkswitch': PortInfoAPI,
            'powerstrip': PortInfoAPI,
            'rack': RackAPI,
            'resource': ResourceAPI,
        }

    def default_delegate(self, request, match):
        types = ['/' + x for x in clusto.typelist.keys()]
        types.sort()
        return dumps(request, types)

    def types_delegate(self, request, match):
        objtype = match.groupdict()['objtype']
        result = []
        for obj in clusto.get_entities(clusto_types=(objtype,)):
            result.append(unclusto(obj))
        return dumps(request, result)

    def action_delegate(self, request, match):
        if request.method == 'GET':
            return self.get_action(request, match)

        if request.method == 'POST':
            return self.post_action(request, match)

        if request.method == 'DELETE':
            return self.delete_action(request, match)

        return Response(status=501, body='501 Not Implemented\n')

    def query_delegate(self, request, match):
        querytype = match.groupdict()['querytype']

        if hasattr(QueryAPI, querytype):
            method = getattr(QueryAPI, querytype)
            return method(request)
        else:
            return Response(status=400, body='400 Bad Request\nThere is no such query\n')

    def post_action(self, request, match):
        name = request.path_info.strip('/')
        if name.count('/') != 1:
            return Response(status=400, body='400 Bad Request\nYou may only create objects, not types or actions\n')
        objtype, objname = name.split('/', 1)

        try:
            obj = clusto.get_by_name(objname)
            if obj:
                return Response(status=409, body='409 Conflict\nObject already exists\n')
        except LookupError:
            pass

        obj = clusto.driverlist[objtype](objname)

        obj = EntityAPI(obj)
        response = obj.show(request)
        response.status = 201
        return response

    def delete_action(self, request, match):
        name = request.path_info.strip('/')
        if name.count('/') != 1:
            return Response(status=400, body='400 Bad Request\nYou may only delete objects, not types or actions\n')
        objtype, objname = name.split('/', 1)

        try:
            obj = clusto.get_by_name(objname)
        except LookupError:
            return Response(status=404, body='404 Not Found\n')

        clusto.delete_entity(obj.entity)
        return Response(status=200, body='200 OK\nObject deleted\n')

    def get_action(self, request, match):
        group = match.groupdict()
        try:
            obj = clusto.get_by_name(group['name'])
        except LookupError:
            return Response(status=404, body='404 Not Found\n')

        if obj.type != group['objtype']:
            response = Response(status=302)
            response.headers.add('Location', str('/%s/%s/%s' % (obj.type, obj.name, group.get('action', ''))))
            return response

        action = group.get('action', 'show')
        handler = self.types.get(group['objtype'], EntityAPI)
        if not obj:
            obj = clusto.get_by_name(group['name'])
        h = handler(obj)
        if hasattr(h, action):
            f = getattr(h, action)
            response = f(request)
        else:
            response = Response(status=404, body='404 Not Found\nInvalid action\n')
        return response

    def search(self, request, match):
        query = request.params.get('q', None)
        if not query:
            return Response(status=400, body='400 Bad Request\nNo query specified\n')

        result = []
        for obj in clusto.get_entities():
            if obj.name.find(query) != -1:
                result.append(unclusto(obj))
        return dumps(request, result)

    def notfound(self, request, match):
        return Response(status=404)

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = Response(status=404, body='404 Not Found\nUnmatched URL\n')

        for pattern, handler in self.urls:
            match = pattern.match(request.path_info)
            if match:
                try:
                    response = handler(request, match)
                except:
                    response = Response(status=500, body=format_exc(),
                                        content_type='text/plain')
                break
        return response(environ, start_response)


application = ClustoApp()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('0.0.0.0', 9996, application)
    log.info('clusto httpd loaded using wsgiref (debug mode)')
    server.serve_forever()
