from google.appengine.ext import ndb

class Book(ndb.Model):
	title = ndb.StringProperty(required=True)
	author = ndb.StringProperty(required=True)
	checked_out = ndb.BooleanProperty(required=True)
	isbn = ndb.StringProperty()