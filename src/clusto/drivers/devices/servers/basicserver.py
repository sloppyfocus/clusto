from clusto.drivers.base import Device
from clusto.drivers.devices.common import PortMixin, IPMixin

class BasicServer(IPMixin, PortMixin, Device):
    """
    server
    """

    _clusto_type = 'server'
    _driver_name = 'basicserver'

    _properties = {'model':None,
                   'manufacturer':None}

    _portmeta = {'pwr-nema-5': {'numports':1},
                 'nic-eth': {'numports':2},
                 'console-serial' : { 'numports':1, }
                 }



class BasicVirtualServer(BasicServer, IPMixin):

    _clusto_type = 'server'
    _driver_name = 'basicvirtualserver'

    def power_on(self, *args, **kwargs):
        raise NotImplementedError()

    def power_off(self, *args, **kwargs):
        raise NotImplementedError()

    def power_reboot(self, *args, **kwargs):
        raise NotImplementedError()

    def create(self, pool, **kwargs):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()
