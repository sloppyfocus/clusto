"""
Clusto schema

"""

VERSION = 3
from sqlalchemy import MetaData, Table, Column, DDL, TIMESTAMP, func
from sqlalchemy import ForeignKey, String, Integer, Text, Index, DateTime
from sqlalchemy import and_, or_, not_, select, event
from sqlalchemy.exc import OperationalError

from sqlalchemy.orm import scoped_session, sessionmaker, mapper, relation

import sqlalchemy.sql

import logging
import sys
import datetime
import clusto
from functools import wraps

try:
    import simplejson as json
except:
    import json


__all__ = ['ATTR_TABLE', 'Attribute', 'and_', 'ENTITY_TABLE', 'Entity', 'func',
           'METADATA', 'not_', 'or_', 'SESSION', 'select', 'VERSION',
           'latest_version', 'CLUSTO_VERSIONING', 'Counter', 'ClustoVersioning',
           'working_version', 'OperationalError', 'ClustoEmptyCommit']


METADATA = MetaData()


CLUSTO_VERSIONING = Table('clustoversioning', METADATA,
                          Column('version', Integer, primary_key=True),
                          Column('timestamp', TIMESTAMP, default=func.current_timestamp(), index=True),
                          Column('user', String(64), default=None),
                          Column('description', Text, default=None),
                          mysql_engine='InnoDB'

                          )

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s')
audit_log = logging.getLogger('clusto.audit')

class ClustoEmptyCommit(Exception):
    pass

class ClustoSession(sqlalchemy.orm.interfaces.SessionExtension):

    def after_begin(self, session, transaction, connection):
        if SESSION.clusto_versioning_enabled:
            sql = CLUSTO_VERSIONING.insert().values(user=SESSION.clusto_user,
                                                    description=SESSION.clusto_description)
            session.execute(sql)

        SESSION.clusto_description = None
        SESSION.flushed = set()

    def before_commit(self, session):

        if not any([session.is_modified(x) for x in session]) \
               and hasattr(SESSION, 'flushed') \
               and not SESSION.flushed:
            raise ClustoEmptyCommit()

    def after_commit(self, session):
        SESSION.flushed = set()

    def after_flush(self, session, flush_context):
        SESSION.flushed.update(x for x in session)


SESSION = scoped_session(sessionmaker(autoflush=True, autocommit=True,
                                      extension=ClustoSession()))


def latest_version():
    return select([func.coalesce(func.max(CLUSTO_VERSIONING.c.version), 0)])

def working_version():
    return select([func.coalesce(func.max(CLUSTO_VERSIONING.c.version),1)])

SESSION.clusto_versioning_enabled = True
SESSION.clusto_version = None
SESSION.clusto_user = None
SESSION.clusto_description = None

ENTITY_TABLE = Table('entities', METADATA,
                     Column('entity_id', Integer, primary_key=True),
                     Column('name', String(128, convert_unicode=True),
                            nullable=False, ),
                     Column('type', String(32), nullable=False),
                     Column('driver', String(32), nullable=False),
                     Column('version', Integer, nullable=False),
                     Column('deleted_at_version', Integer, default=None),
                     mysql_engine='InnoDB'
                     )

Index('idx_entity_name_version',
      ENTITY_TABLE.c.name,
      ENTITY_TABLE.c.version,
      ENTITY_TABLE.c.deleted_at_version)

ATTR_TABLE = Table('entity_attrs', METADATA,
                   Column('attr_id', Integer, primary_key=True),
                   Column('entity_id', Integer,
                          ForeignKey('entities.entity_id'), nullable=False),
                   Column('key', String(256, convert_unicode=True),),
                   Column('subkey', String(256, convert_unicode=True),
                          nullable=True,
                          default=None, ),
                   Column('number', Integer, nullable=True, default=None),
                   Column('datatype', String(32), default='string', nullable=False),

                   Column('int_value', Integer, default=None),
                   Column('string_value', Text(convert_unicode=True),
                           default=None,),
                   Column('datetime_value', DateTime, default=None),
                   Column('relation_id', Integer,
                          ForeignKey('entities.entity_id'), default=None),

                   Column('version', Integer, nullable=False),
                   Column('deleted_at_version', Integer, default=None),
                   mysql_engine='InnoDB'

                   )
Index('idx_attrs_entity_version',
      ATTR_TABLE.c.entity_id,
      ATTR_TABLE.c.version,
      ATTR_TABLE.c.deleted_at_version)

Index('idx_attrs_key', ATTR_TABLE.c.key)
Index('idx_attrs_subkey', ATTR_TABLE.c.subkey)

create_index = DDL('CREATE INDEX idx_attrs_str_value on %(table)s (string_value(20))')
event.listen(ATTR_TABLE, 'after_create', create_index.execute_if(dialect='mysql'))

create_index = DDL('CREATE INDEX idx_attrs_str_value on %(table)s ((substring(string_value,0,20)))')
event.listen(ATTR_TABLE, 'after_create', create_index.execute_if(dialect='postgresql'))

create_index = DDL('CREATE INDEX idx_attrs_str_value on %(table)s (string_value)')
event.listen(ATTR_TABLE, 'after_create', create_index.execute_if(dialect='sqlite'))

COUNTER_TABLE = Table('counters', METADATA,
                      Column('counter_id', Integer, primary_key=True),
                      Column('entity_id', Integer, ForeignKey('entities.entity_id'), nullable=False),
                      Column('attr_key', String(256, convert_unicode=True)),
                      Column('value', Integer, default=0),
                      mysql_engine='InnoDB'
                      )

Index('idx_counter_entity_attr',
      COUNTER_TABLE.c.entity_id,
      COUNTER_TABLE.c.attr_key)

class ClustoVersioning(object):
    pass

class Counter(object):

    def __init__(self, entity, keyname, start=0):
        self.entity = entity
        self.attr_key = unicode(keyname)

        self.value = start

        audit_log.info('create counter entity=%s attr_key=%s value=%s', self.entity.name, self.attr_key, self.value)

        SESSION.add(self)
        SESSION.flush()

    def next(self):

        self.value = Counter.value + 1
        SESSION.flush()
        audit_log.info('increment counter entity=%s attr_key=%s value=%s', self.entity.name, self.attr_key, self.value)
        return self.value

    def delete(self):
        audit_log.info('delete counter entity=%s attr_key=%s value=%s', self.entity.name, self.attr_key, self.value)
        SESSION.delete(self)
        SESSION.flush()

    @classmethod
    def get(cls, entity, keyname, default=0):

        try:
            ctr = SESSION.query(cls).filter(and_(cls.entity==entity,
                                                 cls.attr_key==unicode(keyname))).one()

        except sqlalchemy.orm.exc.NoResultFound:
            ctr = cls(entity, keyname, default)

        return ctr

    @classmethod
    def query(cls):
        return SESSION.query(cls)

class ProtectedObj(object):

    ## this is a hack to make these objects immutable-ish
    writable = False

    @staticmethod
    def writer(func):
        @wraps(func)
        def newfunc(self, *args, **kwargs):
            self.writable = True
            res = func(self, *args, **kwargs)
            self.writable = False
            return res
        return newfunc

    def __setattr__(self, name, val):
        if (name.startswith('_sa_')
            or self.writable
            or name == 'writable'
            or name.startswith('_clusto_writable_')):
            super(ProtectedObj, self).__setattr__(name, val)
        else:
            raise Exception("Not Writable")




class Attribute(ProtectedObj):
    """Attribute class holds key/value pair

    An Attribute is a DB backed object that holds a key, number, subkey,
    and a value.

    Each Attribute is associated with an Entity.

    There can be multiple attributes with the same key, number, subkey, and/or
    value.

    Optionally you can explicitely set int_value, string_value,
    datetime_value, relation_id, and datatype.  These settings would override
    the values set by passing in 'value'.
    """

    @ProtectedObj.writer
    def __init__(self, entity, key, value=None,
                 subkey=None, number=None):

        self.entity = entity
        self.key = unicode(key)

        self.value = value

        if subkey is not None:
            subkey = unicode(subkey)
            
        self.subkey = subkey
        self.version = working_version()
        if isinstance(number, bool) and number == True:
            counter = Counter.get(entity, key, default=-1)
            self.number = counter.next()
        elif isinstance(number, Counter):
            self.number = number.next()
        else:
            self.number = number


        audit_log.info('create attribute entity=%s key=%s subkey=%s value=%s number=%s datatype=%s',
                self.entity.name, self.key, self.subkey, self.value, self.number, self.datatype)
        SESSION.add(self)
        SESSION.flush()



    def __cmp__(self, other):

        if not isinstance(other, Attribute):
            raise TypeError("Can only compare equality with an Attribute. "
                            "Got a %s instead." % (type(other).__name__))

        return cmp(self.key, other.key)

    def __eq__(self, other):

        if not isinstance(other, Attribute):
            return False

        return ((self.key == other.key) and (self.subkey == other.subkey) and
                (self.value == other.value))

    def __repr__(self):

        params = ('key','value','subkey','number','datatype','version', 'deleted_at_version')
                  #'int_value','string_value','datetime_value','relation_id')


        vals = ((x,getattr(self,x)) for x in params)
        strs = ("%s=%s" % (key, ("'%s'" % val if isinstance(val,basestring) else '%s'%str(val))) for key, val in vals)

        s = "%s(%s)" % (self.__class__.__name__, ','.join(strs))

        return s

    def __str__(self):

        params = ('key','number','subkey','datatype',)

        val = "%s.%s %s" % (self.entity.name, '|'.join([str(getattr(self, param)) for param in params]), str(self.value))
        return val

    @property
    def is_relation(self):
        return self.datatype == 'relation'

    def get_value_type(self, value=None):
        if value == None:
            if self.datatype == None:
                valtype = "string"
            else:
                valtype = self.datatype
        else:
            valtype = self.get_type(value)

        if valtype == 'json':
            valtype = "string"
        return valtype + "_value"

    @property
    def keytuple(self):
        return (self.key, self.number, self.subkey)

    @property
    def to_tuple(self):
        return (self.key, self.number, self.subkey, self.value)

    @classmethod
    def get_type(self, value):

        if isinstance(value, (int,long)):
            if value > sys.maxint:
                raise ValueError("Can only store number between %s and %s"
                                 % (-sys.maxint-1, sys.maxint))
            datatype = 'int'
        elif isinstance(value, basestring):
            datatype = 'string'
        elif isinstance(value, datetime.datetime):
            datatype = 'datetime'
        elif isinstance(value, Entity):
            datatype = 'relation'
        elif hasattr(value, 'entity') and isinstance(value.entity, Entity):
            datatype = 'relation'
        elif isinstance(value, (list, dict)):
            datatype = 'json'
        else:
            datatype = 'string'

        return datatype


    def _get_value(self):
        if self.get_value_type() == 'relation_value':
            if hasattr(self, '_clusto_writable_preloaded_relation_value'):
                return getattr(self, '_clusto_writable_preloaded_relation_value')
            else:
                return clusto.drivers.base.Driver(getattr(self, self.get_value_type()))
        else:
            val = getattr(self, self.get_value_type())
            if self.datatype == 'int':
                return int(val)
            elif self.datatype == 'json':
                return json.loads(val)
            else:
                return val

    def _set_value(self, value):

        if not isinstance(value, sqlalchemy.sql.ColumnElement):
            self.datatype = self.get_type(value)
            if self.datatype == 'int':
                value = int(value)
            elif self.datatype == 'json':
                value = json.dumps(value)
        
        value_type = self.get_value_type(value)
        
        if value_type == 'string_value' and value is not None:
            value = unicode(value)
        
        setattr(self, value_type, value)

        audit_log.info('set attribute entity=%s key=%s subkey=%s value=%s number=%s datatype=%s',
                self.entity.name, self.key, self.subkey, self.value, self.number, self.datatype)

    value = property(_get_value, _set_value)

    @ProtectedObj.writer
    def delete(self):
        ### TODO this seems like a hack
        audit_log.info('delete attribute entity=%s key=%s subkey=%s value=%s number=%s datatype=%s',
                self.entity.name, self.key, self.subkey, self.value, self.number, self.datatype)
        if SESSION.clusto_versioning_enabled:
            self.deleted_at_version = working_version()
        else:
            SESSION.delete(self)
            SESSION.flush()

    @classmethod
    def _version_args(cls):
        args = []
        del_version_args = [cls.deleted_at_version==None]
        if SESSION.clusto_version != None:
          del_version_args.append(cls.deleted_at_version>SESSION.clusto_version)
          args.append(cls.version<=SESSION.clusto_version)


        if len(del_version_args) > 1:
          args.append(or_(*del_version_args))
        else:
          args.append(*del_version_args)

        return args

    @classmethod
    def queryarg(cls, key=None, value=(), subkey=(), number=()):
        args = cls._version_args()

        if key:
            args.append(Attribute.key==unicode(key))

        if number is not ():
            args.append(Attribute.number==number)

        if subkey is not ():
            if subkey is not None:
                subkey = unicode(subkey)
        
            args.append(Attribute.subkey==subkey)

        if value is not ():
            valtype = Attribute.get_type(value) + '_value'
            if valtype == 'relation_value':

                # get entity_id from Drivers too
                if hasattr(value, 'entity'):
                    e = value.entity
                else:
                    e = value

                args.append(getattr(Attribute, 'relation_id') == e.entity_id)
            elif valtype == 'string_value':
                if value is not None:
                    value = unicode(value)
                    
                args.append(getattr(Attribute, 'string_value') == value)
            else:
                args.append(getattr(Attribute, valtype) == value)

        return and_(*args)

    @classmethod
    def query(cls):
        args = cls._version_args()

        return SESSION.query(cls).filter(and_(*args))

class Entity(ProtectedObj):
    """
    The base object that can be stored and managed in clusto.

    An entity can have a name, type, and attributes.

    An Entity's functionality is augmented by Drivers which act as proxies for
    interacting with an Entity and its Attributes.
    """

    @ProtectedObj.writer
    def __init__(self, name, driver='entity', clustotype='entity'):
        """Initialize an Entity.

        @param name: the name of the new Entity
        @type name: C{str}
        @param attrslist: the list of key/value pairs to be set as attributes
        @type attrslist: C{list} of C{tuple}s of length 2
        """

        self.name = unicode(name)

        self.driver = driver
        self.type = clustotype

        self.version = working_version()

        audit_log.info('create entity %s driver=%s type=%s', self.name, self.driver, self.type)

        SESSION.add(self)
        SESSION.flush()

    def __eq__(self, otherentity):
        """Am I the same as the Other Entity.

        @param otherentity: the entity you're comparing with
        @type otherentity: L{Entity}
        """

        ## each Thing must have a unique name so I'll just compare those
        if not isinstance(otherentity, Entity):
            retval = False
        else:
            retval = self.name == otherentity.name

        return retval

    def __cmp__(self, other):

        if not hasattr(other, 'name'):
            raise TypeError("Can only compare equality with an Entity-like "
                            "object.  Got a %s instead."
                            % (type(other).__name__))

        return cmp(self.name, other.name)


    def __repr__(self):
        s = "%s(name=%s, driver=%s, clustotype=%s, version=%s, deleted_at_version=%s)"

        return s % (self.__class__.__name__,
                    self.name, self.driver, self.type, str(self.version), str(self.deleted_at_version))

    def __str__(self):
        "Return string representing this entity"

        return str(self.name)

    @property
    def counters(self):
        return Counter.query().filter(Counter.entity==self).all()

    @property
    def attrs(self):
        value_attrs = Attribute.query().filter(
            Attribute.entity == self).filter(
            Attribute.datatype != 'relation').all()
        relation_attrs = Attribute.query().filter(
            Attribute.entity == self).filter(
            Attribute.datatype == 'relation').all()

        relation_entity_ids = [relation_attr.relation_id for relation_attr in relation_attrs]
        if relation_entity_ids:
            relation_entities = Entity.query().filter(
                Entity.entity_id.in_(relation_entity_ids)).all()
        else:
            relation_entities = []
        relation_drivers = dict([(e.entity_id, clusto.drivers.base.Driver(e))
                                 for e in relation_entities])

        for relation_attr in relation_attrs:
            if relation_attr.relation_id in relation_drivers:
                setattr(relation_attr, '_clusto_writable_preloaded_relation_value',
                        relation_drivers[relation_attr.relation_id])
        return value_attrs + relation_attrs

    @property
    def references(self):
        return Attribute.query().filter(Attribute.relation_id==self.entity_id).all()


    def add_attr(self, *args, **kwargs):

        return Attribute(self, *args, **kwargs)

    @ProtectedObj.writer
    def delete(self):
        "Delete self and all references to self."

        clusto.begin_transaction()
        try:
            for i in self.references:
                i.delete()

            for i in self.attrs:
                i.delete()

            for i in self.counters:
                i.delete()

            if SESSION.clusto_versioning_enabled:
                self.deleted_at_version = working_version()
            else:
                SESSION.delete(self)
                SESSION.flush()

            clusto.commit()
            audit_log.info('delete entity %s', self.name)
        except Exception, x:
            clusto.rollback_transaction()
            raise x

    @classmethod
    def _version_args(cls):
        args = []
        del_version_args = [cls.deleted_at_version==None]
        if SESSION.clusto_version != None:
          del_version_args.append(cls.deleted_at_version>SESSION.clusto_version)
          args.append(cls.version<=SESSION.clusto_version)

        args.append(or_(*del_version_args))
        return args

    @classmethod
    def query(cls):
        return SESSION.query(cls).filter(and_(*cls._version_args()))


    @ProtectedObj.writer
    def _set_driver_and_type(self, driver, clusto_type):
        """sets the driver and type for the entity

        this shouldn't be too dangerous, but be careful

        params:
          driver: the driver name
          clusto_type: the type name
        """

        try:
            clusto.begin_transaction()

            self.type = clusto_type
            self.driver = driver

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x


mapper(ClustoVersioning, CLUSTO_VERSIONING)

mapper(Counter, COUNTER_TABLE,
       properties = {'entity': relation(Entity, lazy=True, uselist=False)},

       )

mapper(Attribute, ATTR_TABLE,
       properties = {'relation_value': relation(Entity, lazy=True,
                                                primaryjoin=ATTR_TABLE.c.relation_id==ENTITY_TABLE.c.entity_id,
                                                uselist=False,
                                                passive_updates=False),
                     'entity': relation(Entity, lazy=True, uselist=False,
                                        primaryjoin=ATTR_TABLE.c.entity_id==ENTITY_TABLE.c.entity_id)})


## might be better to make the relationships here dynamic_loaders in the long
## term.
mapper(Entity, ENTITY_TABLE,

       )
