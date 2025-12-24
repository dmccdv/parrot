from django.urls import path
from . import views
urlpatterns = [
    path("study/start/<int:deck_id>/", views.study_start, name="study_start"),
    path("study/grade/<int:session_id>/", views.grade_card, name="grade_card"),
]