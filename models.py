from google.appengine.ext import ndb

class Configuration(ndb.Model):
	key = ndb.StringProperty()
	value = ndb.StringProperty()

class Quiz(ndb.Model):
	path = ndb.StringProperty()

class QuizScore(ndb.Model):
	score = ndb.IntegerProperty()