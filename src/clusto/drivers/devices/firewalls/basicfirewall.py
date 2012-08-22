
from clusto.drivers.base import Device
from clusto.drivers.devices.common import PortMixin, IPMixin

class BasicFirewall(IPMixin, PortMixin, Device):
    """
    Basic load firewall driver
    """

    _clusto_type = 'firewall'
    _driver_name = 'basicfirewall'


    _portmeta = {'pwr-nema-5' : {'numports':1},
                 'nic-eth' : {'numports':2}}


