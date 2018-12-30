from peewee import *
from playhouse.sqlite_ext import *

from flask_security import RoleMixin, UserMixin
import os

from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.migrate import SqliteMigrator, migrate

DB_DIR="sdb"
userdb = SqliteDatabase(os.path.join(DB_DIR, 'users.db'))
querydb = SqliteDatabase(os.path.join(DB_DIR, 'queries.db'))

class QueryModel(Model):
    class Meta:
        database = querydb

class UserModel(Model):
    class Meta:
        database = userdb

class SavedQuery(QueryModel):
    user = IntegerField(index=True)
    table = CharField(index=True)

    hashid = CharField(index=True)
    created = TimestampField(index=True, utc=True)
    updated = TimestampField(utc=True)

    results = JSONField()
    compare = JSONField()
    parsed = JSONField()

    def toObject(self):
        return { 
            "results" : self.results,
            "parsed" : self.parsed,
            "created" : self.created

        }

    class Meta:
        database = querydb

class Role(UserModel, RoleMixin):
    name = CharField(unique=True)
    description = TextField(null=True)

class User(UserModel, UserMixin):
    email = TextField()
    password = TextField()
    active = BooleanField(default=True)
    confirmed_at = DateTimeField(null=True)

class UserRoles(UserModel):
    # Because peewee does not come with built-in many-to-many
    # relationships, we need this intermediary class to link
    # user to roles.
    user = ForeignKeyField(User, related_name='roles')
    role = ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)


def create_db_if_not():
    try:
        os.makedirs(DB_DIR)
    except Exception, e:
        pass

    for c in [SavedQuery, User]:
        c._meta.database.connect()
        c._meta.database.create_tables([c])

    # query DB migrations
    migrator = SqliteMigrator(querydb)
    migrate(
        migrator.add_column('savedquery', 'compare', JSONField(default='')),
    )

if __name__ == "__main__":
    if "RESET" in os.environ:
        create_db_if_not()