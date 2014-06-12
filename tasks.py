import webapp2
import os
import json
import random

import logging

from urllib import quote, urlencode
from collections import Counter
from operator import attrgetter

from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.api.taskqueue import TaskRetryOptions

import headers
from models import Quiz, QuizScore, QuizAverage, QuizResults, QuizResult, QuizNeedingRecalculation, QuizSummary

def update_summary(path, score):

	logging.info("Summarising %s" % path)

	key = ndb.Key('QuizSummary', path)

	summary = key.get()

	int_score = int(score)

	if not summary:
		summary = QuizSummary(key=key, total_score=int_score, total_scores_submitted=1)
		summary.score_distributions = {score : 1}
		summary.put()
		return

	summary.total_score += int_score
	summary.total_scores_submitted += 1

	distributions = summary.score_distributions

	if not score in distributions:
		distributions[score] = 0
	
	distributions[score] = distributions[score] + 1
	logging.info(distributions)

	summary.put()

	return summary.key



def generate_summary(parent_quiz_key):
	quiz = parent_quiz_key.get()
	logging.debug(quiz.path)

	def read_score(key):
		score_data = key.get_async()
		return score_data.get_result().score

	scores = QuizScore.query(ancestor=parent_quiz_key).map(read_score, keys_only=True, batch_size=5000, deadline=100, limit=100000)

	for score in scores:
		score_total = sum(scores)
		number_of_scores = len(scores)

	if scores:
		average = score_total / number_of_scores

		summary = ndb.Key('QuizAverage', quiz.path).get()

		if not summary:
			summary = QuizAverage(id=quiz.path, average_score=average).put()
		else:
			summary.average_score = average
			summary.put()
		#logging.info("Average: %d" % average)

		results = ndb.Key('QuizResults', quiz.path).get()

		if not results:
			results = QuizResults(id=quiz.path)

		counter = Counter(scores)
		#logging.info(counter)

		summary_data = [(k, counter[k], int((float(counter[k]) / len(scores)) * 100)) for k in sorted(counter.keys())]
		#logging.info(summary_data)

		results.results = [QuizResult(score=s, number_of_scores=n, percentage=p) for (s,n,p) in summary_data]

		results.put()


	return summary

class GenerateQuizSummaries(webapp2.RequestHandler):
	def get(self):
		for quiz in QuizNeedingRecalculation.query():
			quiz_data = ndb.Key(Quiz, quiz.path).get()
			if quiz_data:
				deferred.defer(generate_summary, quiz_data.key, _countdown=random.randint(1, 30), _queue='quiz-results')
				quiz.key.delete()

		headers.json(self.response)
		self.response.out.write(json.dumps({"status" : "Summaries scheduled"}))

app = webapp2.WSGIApplication([('/tasks/summaries/generate', GenerateQuizSummaries)],
                              debug=True)