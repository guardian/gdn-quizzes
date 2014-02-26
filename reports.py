import webapp2
import jinja2
import os
import json
import logging

from webapp2 import abort
from urllib import quote, urlencode
import urlparse
from collections import Counter
from operator import attrgetter

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Quiz, QuizScore, QuizResults

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

class MainPage(webapp2.RequestHandler):
	def get(self):
		template = jinja_environment.get_template('reports/index.html')
		
		template_values = {}

		self.response.out.write(template.render(template_values))

class ResultsHandler(webapp2.RequestHandler):
	def get(self):

		if not "quiz_url" in self.request.params:
			abort(400, "No quiz url supplied")

		template = jinja_environment.get_template('reports/quiz-results.html')
		
		template_values = {}

		quiz_url = self.request.params.get("quiz_url")

		path = urlparse.urlparse(quiz_url).path
		
		quiz = ndb.Key(Quiz, path).get()

		if not quiz:
			abort(404, "No entry for that quiz")

		results = ndb.Key('QuizResults', quiz.path).get()

		if not results:
			abort(404, "No results for this quiz")

		sorted_scores = sorted(results.results, key=attrgetter('score'))

		max_percentage = max([s.percentage for s in sorted_scores])

		def calculate_width(score_summary):
			if max_percentage > 0:
				score_summary.width = (float(score_summary.percentage) / max_percentage) * 100
			return score_summary

		enhanced_scores = map(calculate_width, sorted_scores)

		template_values['max_percentage'] = max_percentage

		template_values['scores'] = enhanced_scores
		template_values['total_scores'] = sum([result.number_of_scores for result in results.results])

		self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/reports', MainPage),
	('/reports/quiz', ResultsHandler),],
                              debug=True)