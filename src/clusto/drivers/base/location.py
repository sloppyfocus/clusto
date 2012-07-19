
from clusto.drivers.base import Driver

class Location(Driver):

    _clusto_type = "location"
    _driver_name = "location"

    def insert(self, thing):
        """Insert the given Enity or Driver into this Entity.

        Such that:

        >>> A.insert(B)
        >>> (B in A)
        True

        A given entity can only be in one Location one time.
        """

        d = self.ensure_driver(thing,
                               "Can only insert an Entity or a Driver. "
                               "Tried to insert %s." % str(type(thing)))

        locations = thing.parents(clusto_drivers=[self._driver_name])
        if locations:
            raise TypeError("%s is already in location(s) %s." %
                                (thing, locations))

        self.add_attr("_contains", d, number=True)
