"""
IPMixin is a basic mixin to be used by devices that can be assigned IPs
"""

import re

import clusto

from clusto.drivers.resourcemanagers import IPManager

from clusto.exceptions import ConnectionException,  ResourceException


class IPMixin:

    def addIP(self, ip=None, ipman=None):

        if not ip and not ipman:
            raise ResourceException('If no ip is specified then an ipmanager must be specified')

        elif ip:
            
            if not ipman:
                ipman = IPManager.getIPManager(ip)

            return ipman.allocate(self, ip)
        else:
            return ipman.allocate(self)
            
            
        
    def hasIP(self, ip):

        ipman = IPManager.getIPManager(ip)

        return self in ipman.owners(ip)
    
    def bindIPtoOSPort(self, ip, osportname, ipman=None, porttype=None, portnum=None):
        """bind an IP to an os port and optionally also asign the os port name
        to a physical port

        If the given ip is already allocated to this device then use it.  If
        it isn't, try to allocate it from a matching IPManager.

        
        """

        if (porttype != None) ^ (portnum != None):
                raise Exception("both portype and portnum need to be specified or set to None")
            
        try:
            clusto.beginTransaction()

            if not self.hasIP(ip):
                if not ipman:
                    ipman = IPManager.getIPManager(ip)

                ipman.allocate(self, ip)

                clusto.flush()


            ipattrs = ipman.getResourceAttrs(self, ip)

            if porttype is not None and portnum is not None:
                self.setPortAttr(porttype, portnum, 'osportname', osportname)

            self.setAttr(ipattrs[0].key,
                         number=ipattrs[0].number,
                         subkey='osportname',
                         value=osportname)

            clusto.commit()
        except Exception, x:
            clusto.rollbackTransaction()
            raise x
        


        



            
        