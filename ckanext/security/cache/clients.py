from builtins import object
import redis
from ckan.common import config


class RedisClient(object):
    prefix = ''

    def __init__(self):
        host = config['ckanext.security.redis.host']
        port = config['ckanext.security.redis.port']
        db = config['ckanext.security.redis.db']
        pwd = config.get('ckanext.security.redis.password', None)
        ssl = config.get('ckanext.security.redis.ssl', False).lower() == 'true'
        ssl_keyfile = config.get('ckanext.security.redis.ssl_keyfile', None)
        ssl_certfile = config.get('ckanext.security.redis.ssl_certfile', None)
        ssl_cert_reqs = config.get('ckanext.security.redis.ssl_cert_reqs', None)
        ssl_ca_certs = config.get('ckanext.security.redis.ssl_ca_certs', None)


        self.client = redis.StrictRedis(host=host, port=port, db=db, password=pwd, ssl=ssl, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile, ssl_cert_reqs=ssl_cert_reqs, ssl_ca_certs=ssl_ca_certs)        

    def get(self, key):
        return self.client.get(self.prefix + key)

    def set(self, key, value):
        return self.client.set(self.prefix + key, value)

    def delete(self, key):
        return self.client.delete(self.prefix + key)


class ThrottleClient(RedisClient):
    prefix = 'security_throttle_'
