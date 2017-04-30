import os
class DevelopmentConfig(object):
	SQLALCHEMY_DATABASE_URI = "postgresql://stephen:thinkful@localhost:5432/blogful"
	DEBUG = True
	SECRET_KEY = os.environ.get("BLOGFUL_SECRET_KEY", os.urandom(12))
