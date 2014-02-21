import webapp2
import os
import json
import logging
from urllib import quote, urlencode
from collections import Counter

from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb

import headers
from models import Quiz, QuizScore, QuizAverage, QuizResults, QuizResult

def generate_summary(quiz):
	score_entries = [e for e in QuizScore.query(ancestor=quiz.key)]
	scores = [s.score for s in score_entries]

	if scores:
		average = sum(scores) / len(scores)

		summary = ndb.Key('QuizAverage', quiz.path).get()

		if not summary:
			summary = QuizAverage(id=quiz.path, average_score=average).put()
		else:
			summary.average_score = average
			summary.put()
		#logging.info("Average: %d" % average)

	if score_entries:
		results = ndb.Key('QuizResults', quiz.path).get()

		if not results:
			results = QuizResults(id=quiz.path)

		scores = sorted([s.score for s in QuizScore.query(ancestor=quiz.key)])
		counter = Counter(scores)

		summary_data = [(k, counter[k], int((float(counter[k]) / len(scores)) * 100)) for k in sorted(counter.keys())]

		results.results = [QuizResult(score=s, number_of_scores=n, percentage=p) for (s,n,p) in summary_data]

		results.put()


	return summary

class GenerateQuizSummaries(webapp2.RequestHandler):
	def get(self):
		for quiz in Quiz.query():
			deferred.defer(generate_summary, quiz)

		headers.json(self.response)
		self.response.out.write(json.dumps({"status" : "Summaries scheduled"}))

app = webapp2.WSGIApplication([('/tasks/summaries/generate', GenerateQuizSummaries)],
                              debug=True)