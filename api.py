import webapp2
from webapp2 import abort
import jinja2
import os
import json
import logging
from urllib import quote, urlencode
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

import headers

from models import Quiz, QuizScore

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
			quiz = Quiz(id = path)
			quiz.put()

		QuizScore(parent=quiz.key, score=int(score)).put()

		headers.json(self.response)
		self.response.out.write(json.dumps({"score" : score}))

app = webapp2.WSGIApplication([('/api/score', ScoreHandler)],
                              debug=True)