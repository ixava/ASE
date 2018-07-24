from sqlalchemy import Table, Column,  Integer, String, MetaData, ForeignKey, UniqueConstraint,text
from sqlalchemy.dialects.mysql import INTEGER, TIMESTAMP, DOUBLE
from sqlalchemy.sql.functions import current_timestamp

metadata = MetaData()

users = Table('users', metadata,
	Column('id', Integer, primary_key=True),
	Column('ip_id', Integer, ForeignKey('ips.id')),
	Column('name_id', Integer, ForeignKey('names.id')),
	Column('steamid_id', Integer, ForeignKey('steamids.id')),
	Column('hostname_id', Integer, ForeignKey('hostnames.id')),
	Column('hwid_id', Integer, ForeignKey('hwids.id')),
	Column('first_seen', TIMESTAMP(), server_default=current_timestamp()),
	Column('last_seen', TIMESTAMP(), server_default=current_timestamp()),
	UniqueConstraint('ip_id', 'name_id', 'steamid_id', 'hwid_id', 'hostname_id',\
		name='unique_user')
	)
ips = Table('ips', metadata,
	Column('id', Integer, primary_key=True),
	Column('ip', String(15), unique=True, nullable=False),
	Column('ip_int', INTEGER(unsigned=True), unique=True, nullable=False),
	Column('risk', DOUBLE(), server_default='0.00')
	)
hostnames = Table('hostnames', metadata,
	Column('id', Integer, primary_key=True),
	Column('hostname', String(100), unique=True, nullable=False)
	)
steamids = Table('steamids', metadata,
	Column('id', Integer, primary_key=True),
	Column('steamid', String(20), unique=True, nullable=False)
	)
hwids = Table('hwids', metadata,
	Column('id', Integer, primary_key=True),
	Column('hwid', String(20), unique=True, nullable=False)
	)
names = Table('names', metadata,
	Column('id', Integer, primary_key=True),
	Column('name', String(30), unique=True, nullable=False)
	)