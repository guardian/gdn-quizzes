from google.appengine.ext import ndb

class Configuration(ndb.Model):
	key = ndb.StringProperty()
	value = ndb.StringProperty()

class Quiz(ndb.Model):
	path = ndb.StringProperty()

class QuizScore(ndb.Model):
	score = ndb.IntegerProperty()

class QuizAverage(ndb.Model):
	average_score = ndb.IntegerProperty(required=True)

class QuizResult(ndb.Model):
	score = ndb.IntegerProperty(required=True)
	number_of_scores = ndb.IntegerProperty(required=True)
	percentage = ndb.IntegerProperty(required=True)

class QuizResults(ndb.Model):
	results = ndb.StructuredProperty(QuizResult, repeated=True)

class QuizNeedingRecalculation(ndb.Model):
	path = ndb.StringProperty(required=True)

class QuizSummary(ndb.Model):
	total_score = ndb.IntegerProperty(required=True, default=0)
	total_scores_submitted = ndb.IntegerProperty(required=True, default=0)
	current_average_score = ndb.ComputedProperty(lambda self: self.total_score / self.total_scores_submitted)
	score_distributions = ndb.JsonProperty()