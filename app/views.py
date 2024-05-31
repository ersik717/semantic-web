import json

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers

from app.db import *
from app.qa import *

# Create your views here.
def index(request):
	return render(request, 'index.html')

def get_answer(request):
	if request.method == 'GET':
		question = request.GET['question']
		language = request.GET['language']
		print(json.dumps(ask(question, language=language)))
		return HttpResponse(json.dumps(json_object), content_type="application/json")
	    # question = request.GET['question']
	    # language = request.GET['language']
	    # json_object = {
	    # 		'question': question,
	    # 		'language': language
	    # 		}
	    # return HttpResponse(json.dumps(json_object), content_type="application/json")
	    # return JsonResponse(json_object)
	    # return json.dumps(ask(question, language=language))
    
def set_feedback(request):
	if request.method == 'POST':
	    question = request.POST['question']
	    language = request.POST['language']
	    is_correct = request.POST['isCorrect']
	    DB().put_qa(question, language, is_correct)
	    json_success = {
	    		'success': True
	    }
	    # return HttpResponse(json.dumps({'success': True}), content_type="application/json")
	    # return HttpResponse(json.dumps(json_success), content_type="application/json")
	    return json.dumps(json_success)

def get_feedback_stats(request):
	return HttpResponse(json.dumps(DB().get_qa_quality()), content_type="application/json")
