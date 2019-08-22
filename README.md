# kingdomlib
Web development some useful libs

# Install
```shell
$ pip install git+https://github.com/nadostar/kingdomlib.git

$ git clone git://github.com/nadostar/kingdomlib.git $ cd kingdomlib $ python setup.py install
```

# Testing
```shell
$ pytest -v
```

# kingdomlib.sqlalchemy
```python
from flask_sqlalchemy import SQLAlchemy
from kingdomlib.sqlalchemy import BaseMixin, CacheProperty

db = SQLAlchemy(session_options={
    'expire_on_commit': False,
    'autoflush': False,
})

class Base(db.Model, BaseMixin):
    __abstract__ = True
    cache = CacheProperty(db)

class Todo(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
```

```shell
$ flask shell

$ t1 = Todo(name='python')
$ t2 = Todo(name='flask')

$ db.session.add_all([t1, t2])
$ db.sessionn.commit()

$ Todo.query.get(1)
$ Todo.cache.get(1)
```