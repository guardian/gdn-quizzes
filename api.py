import webapp2
from webapp2 import abort
import jinja2
import os
import json
import logging

from urllib import quote, urlencode
from operator import attrgetter

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.api import memcache
from google.appengine.ext import deferred

import headers
import tasks

from models import Quiz, QuizScore, QuizNeedingRecalculation, QuizSummary

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

class ScoreHandler(webapp2.RequestHandler):
	def get(self):
		headers.json(self.response)
		self.response.out.write(json.dumps({"hello" : "world"}))

	def post(self):
		headers.cors(self.response)

		if not "score" in self.request.params:
			abort(400, "No score posted")
		if not "path" in self.request.params:
			abort(400, "No path supplied")

		score = self.request.params.get("score")
		path = self.request.params.get("path")

		quiz = ndb.Key(Quiz, path).get()

		if not quiz:
			quiz = Quiz(id=path, path=path)
			quiz.put()

		QuizScore(parent=quiz.key, score=int(score)).put()

		recalculation_flag = ndb.Key(QuizNeedingRecalculation, path).get()

		if not recalculation_flag:
			QuizNeedingRecalculation(id=path, path=path).put()

		deferred.defer(tasks.update_summary, path, score, _queue='quiz-results')

		headers.json(self.response)
		self.response.out.write(json.dumps({"score" : score}))

class ResultsHandler(webapp2.RequestHandler):
	def get(self):
		headers.cors(self.response)
		headers.json(self.response)

		if not "path" in self.request.params:
			abort(400, "No path supplied")

		path = self.request.params.get("path")

		data = memcache.get(path, namespace="results")

		if data:
			self.response.write(data)
			return
		
		quiz = ndb.Key(Quiz, path).get()

		quiz_average = ndb.Key('QuizAverage', quiz.path).get()

		if not quiz_average:
			abort(404, 'No results available')

		data = {'average_score' : quiz_average.average_score}

		results = ndb.Key('QuizResults', quiz.path).get()

		if results:
			sorted_scores = sorted(results.results, key=attrgetter('score'))

			def score_summary(results):
				return {'score': results.score,
					'percentage' : results.percentage,}

			data['scores'] = map(score_summary, sorted_scores)
			data['max_percentage'] = max([s.percentage for s in sorted_scores])
		
		quiz_summary = ndb.Key(QuizSummary, path).get()
		data['average_score'] = quiz_summary.current_average_score

		percentages = [int((float(v) * int(k) / quiz_summary.total_score) * 100) for k, v in quiz_summary.score_distributions.items()]
		quiz_summary.max_percentage = max(percentages)
		data['max_percentage'] = quiz_summary.max_percentage

		data['summary'] = quiz_summary.score_distributions

		def calculate_width2(max_percentage, score_percentage):
			if max_percentage > 0:
				return (float(score_percentage) / max_percentage) * 100
			return 0

		sorted_keys = map(str, sorted(map(int, quiz_summary.score_distributions.keys())))
		sorted_scores = [{"score" : key, "percentage" : int((float(quiz_summary.score_distributions[key]) / quiz_summary.total_scores_submitted) * 100)} for key in sorted_keys]


		data['scores'] = sorted_scores

		self.response.out.write(json.dumps(data))

app = webapp2.WSGIApplication([('/api/score', ScoreHandler),
	('/api/results', ResultsHandler),],
                              debug=True)