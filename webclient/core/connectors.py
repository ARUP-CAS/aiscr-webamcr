from django.conf import settings
from django.utils.encoding import force_str

import redis
from webclient.settings.base import get_plain_redis_pass


class RedisConnector:
    r = None
    r_decode = None

    @classmethod
    def _create_connection(cls):
        cls.r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass())

    # tento connector vrací přímo string, takže není potřeba volat value.decode("utf-8")
    @classmethod
    def _create_connection_decode(cls):
        cls.r_decode = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass(), decode_responses=True
        )

    @classmethod
    def get_connection(cls) -> redis.Redis:
        if not cls.r:
            cls._create_connection()
        return cls.r

    @classmethod
    def get_connection_decode(cls) -> redis.Redis:
        if not cls.r_decode:
            cls._create_connection_decode()
        return cls.r_decode

    @staticmethod
    def prepare_model_for_redis(table):
        columns = table.columns.iterall()
        row = table.rows[0]
        data = {}
        for column in columns:
            value = row.get_cell_value(column.name)
            if value and "nahled" not in column.name:
                data[column.name] = force_str(value)
            else:
                data[column.name] = ""
        return data
