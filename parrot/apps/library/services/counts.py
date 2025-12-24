from django.utils import timezone
from apps.core.models import Flashcard


def compute_due_new_counts(user, deck):

    now = timezone.now()

    due_count = Flashcard.objects.filter(
        deck_cards__deck=deck,
        progress__user=user,
        progress__due_at__lte=now,
    ).distinct().count()

    new_count = Flashcard.objects.filter(
        deck_cards__deck=deck,\
    ).exclude(
        progress__user=user
    ).distinct().count()

    total = Flashcard.objects.filter(deck_cards__deck=deck).distinct().count()
    return due_count, new_count, total