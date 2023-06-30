from sqlalchemy import create_engine
from pandas import read_sql
con = create_engine('postgresql+psycopg://odin@127.0.0.1/odin?sslmode=verify-ca')
df = read_sql(query,con=con)