from datetime import timedelta
from django.utils import timezone


def sm2_update(progress, quality: int, now=None):

    now = now or timezone.now()
    q = max(0, min(5, int(quality)))

    progress.last_reviewed_at = now

    ease_before = progress.ease
    interval_before = progress.interval_days

    if q < 3:
        progress.repetitions = 0
        progress.interval_days = 1
        progress.lapses += 1
        progress.state = "relearning"
    else:
        if progress.repetitions == 0:
            progress.interval_days = 1
            progress.lapses += 1
        elif progress.repetitions == 1:
            progress.interval_days = 6
        else:
            progress.interval_days = int(round(progress.interval_days * progress.ease))

        progress.repetitions += 1
        progress.state = "review"

    progress.ease = progress.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.002))
    if progress.ease < 1.3:
        progress.ease = 1.3

    progress.due_at = now + timedelta(days=progress.interval_days)

    return {
        "ease_before": ease_before,
        "ease_after": progress.ease,
        "interval_before": interval_before,
        "interval_after": progress.interval_days,
        "due_before": None,
        "due_after": progress.due_at,
    }