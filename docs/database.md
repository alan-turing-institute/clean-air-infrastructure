# Database

To connect to a database using the cleanair package you need to do x, y, z


```python

from cleanair.database import DbWriter

my_connection = DBWriter(secretfile = 'mysecret')

with my_connection.dbcnx.open_session() as session:

    session.query(MetaPoint).filter().all()

```

This is more some prose about how this works.