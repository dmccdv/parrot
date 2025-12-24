from django.utils import timezone
from apps.core.models import Flashcard
from apps.study.models import CardProgress


def select_session_queue(user, deck, chunk_size: int, new_ratio: float, daily_new_limit: int):

    now = timezone.now()

    due_qs = Flashcard.objects.filter(
        deck_cards__deck=deck,
        progress__user=user,
        progress__due_at__lte=now,
    ).distinct().order_by("progress__due_at")

    due_ids = list(due_qs.values_list("id", flat=True)[:chunk_size])

    if len(due_ids) >= chunk_size:
        return due_ids
    
    remaining = chunk_size - len(due_ids)
    new_target = int(round(chunk_size * new_ratio))
    new_target = min(new_target, remaining, daily_new_limit)

    if new_target <= 0:
        return due_ids
    
    new_qs = Flashcard.objects.filter(deck_cards__deck=deck).exclude(progress__user=user).distinct()
    new_ids = list(new_qs.order_by("frequency_rank", "id").values_list("id", flat=True)[:new_target])

    return due_ids + new_ids