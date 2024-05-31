from django.urls import path, include
from . import views

urlpatterns = [
	path('', views.index),
	path('get_answer', views.get_answer),
	# path('get_feedback_stats', views.get_feedback_stats),
	# path('set_feedback', views.set_feedback),
]
