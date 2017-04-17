import os
class DevelopmentConfig(object):
	SQLALCHEMY_DATABASE_URI = "postgresql://stephen:thinkful@localhost:5432/blogful"
	DEBUG = True