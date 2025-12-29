from django.urls import path
from . import views

urlpatterns = [
    path("library/", views.library, name="library"),
    path("library/add/<int:deck_id>/", views.add_to_library, name="library_add"),
    path("library/remove/<int:deck_id>/", views.remove_from_library, name="library_remove"),
    path("library/settings/<int:deck_id>/", views.deck_settings, name="deck_settings"),
    path("library/decks/new/", views.deck_create, name="deck_create"),
    path("library/decks/<int:deck_id>/manage/", views.deck_manage, name="deck_manage"),
    path("library/decks/<int:deck_id>/cards/new/", views.card_create, name="card_create"),
    path("library/cards/<int:card_id>/edit/", views.card_edit, name="card_edit"),
]