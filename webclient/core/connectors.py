import redis
from django.utils.encoding import force_str

from webclient.settings.base import get_plain_redis_pass


class RedisConnector:
    r = None

    @classmethod
    def _create_connection(cls):
        cls.r = redis.Redis(host="redis", port=6379, password=get_plain_redis_pass())

    @classmethod
    def get_connection(cls):
        if not cls.r:
            cls._create_connection()
        return cls.r

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
