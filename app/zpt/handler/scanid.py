import re
from datetime import datetime
from os.path import dirname, join, realpath

from pandas import DataFrame, read_sql
from sqlalchemy import create_engine

from .mjd import datetime2mjd


class ScanInfo:
    def __init__(self, db_connect_string: str):
        self.engine = create_engine(db_connect_string)

    @property
    def scanid_query(self):
        dir = dirname(realpath(__file__))
        query_file = join(dir, "get_scan_info.sql")
        with open(query_file, "r") as query:
            query_psql = query.read()
        query_psycopg = re.sub(r":'(\w+)'", r"%(\1)s", query_psql)
        return query_psycopg

    def get_scan_info(
        self, start_interval: datetime, end_interval: datetime
    ) -> DataFrame:
        parameters = {
            "start": str(datetime2mjd(start_interval)),
            "end": str(datetime2mjd(end_interval)),
        }
        return read_sql(self.scanid_query, params=parameters, con=self.engine)
