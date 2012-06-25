
from clusto.drivers.base import Device
from clusto.drivers.devices.common import PortMixin, IPMixin

class BasicLoadBalancer(IPMixin, PortMixin, Device):
    """
    Basic load balancer driver
    """

    _clusto_type = 'loadbalancer'
    _driver_name = 'basicloadbalancer'


    _portmeta = {'pwr-nema-5' : {'numports':1},
                 'nic-eth' : {'numports':2}}


