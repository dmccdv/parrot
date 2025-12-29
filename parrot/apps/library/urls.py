from django.urls import path
from . import views

urlpatterns = [
    path("library/", views.library, name="library"),
    path("library/add/<int:deck_id>/", views.add_to_library, name="library_add"),
    path("library/remove/<int:deck_id>/", views.remove_from_library, name="library_remove"),
]