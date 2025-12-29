from django.utils import timezone
from apps.core.models import Flashcard

def select_session_queue(user, deck, chunk_size: int, new_ratio: float, daily_new_limit: int, new_today: int):
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
    new_target = min(new_target, remaining)

    remaining_new_today = max(0, daily_new_limit - new_today)
    new_target = min(new_target, remaining_new_today)

    if new_target <= 0:
        return due_ids

    new_qs = (
        Flashcard.objects
        .filter(deck_cards__deck=deck)
        .exclude(progress__user=user)
        .distinct()
        .order_by("frequency_rank", "id")
    )
    new_ids = list(new_qs.values_list("id", flat=True)[:new_target])

    return due_ids + new_ids
