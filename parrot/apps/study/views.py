from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from apps.core.models import Deck, Flashcard
from apps.library.models import UserDeck
from apps.library.services.counts import compute_due_new_counts
from apps.study.models import CardProgress, StudySession, ReviewLog
from apps.study.services.selector import select_session_queue
from apps.study.services.scheduler import sm2_update


@login_required
def study_start(request, deck_id: int):
    deck = get_object_or_404(Deck, id=deck_id)
    ud = get_object_or_404(UserDeck, user=request.user, deck=deck)

    queue = select_session_queue(
        user=request.user,
        deck=deck,
        chunk_size=ud.chunk_size,
        new_ratio=ud.new_ratio,
        daily_new_limit=ud.daily_new_limit,
    )

    if not queue:
        return (render, "study/empty.html", {"deck": deck})
    
    session = StudySession.objects.create(user=request.user, deck=deck, queue=queue, index=0)
    session.rotate_nonce()
    session.save(update_fields=["current_nonce"])

    first_card = Flashcard.objects.get(ud=queue[0])
    return render(request, "study/study.html", {"deck": deck, "session": session, "card": first_card})


@login_required
@transaction.atomic
def grade_card(request, session_id: int):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    session = get_object_or_404(StudySession.objects.select_for_update(), id=session_id, user=request.user)

    if session.status != "active":
        return render(request, "study/done_partial.html")

    try:
        expected_index = int(request.POST["index"])
        quality = int(request.POST["quality"])
        nonce = request.POST["nonce"]
    except (KeyError, ValueError):
        return HttpResponseBadRequest("Bad payload")

    if expected_index != session.index or nonce != session.current_nonce:
        if session.index >= len(session.queue):
            return render(request, "study/done_partial.html")
        current_card = Flashcard.objects.get(id=session.queue[session.index])
        return render(request, "study/card_partial.html", {"session": session, "card": current_card})

    if session.index >= len(session.queue):
        return render(request, "study/done_partial.html")

    card_id = session.queue[session.index]
    card = Flashcard.objects.get(id=card_id)

    progress, _ = CardProgress.objects.get_or_create(
        user=request.user,
        card=card,
        defaults={"due_at": timezone.now(), "state": "new"},
    )

    due_before = progress.due_at
    ease_before = progress.ease
    interval_before = progress.interval_days

    sm2_update(progress, quality, now=timezone.now())
    progress.save()

    ReviewLog.objects.create(
        session=session,
        user=request.user,
        deck=session.deck,
        card=card,
        quality=max(0, min(5, quality)),
        due_before=due_before,
        due_after=progress.due_at,
        ease_before=ease_before,
        ease_after=progress.ease,
        interval_before=interval_before,
        interval_after=progress.interval_days,
    )

    ud = UserDeck.objects.select_for_update().get(user=request.user, deck=session.deck)
    ud.bump_today(1)
    if interval_before == 0 and progress.repetitions >= 1:
        ud.total_new_seen += 1
    ud.save(update_fields=["last_studied_at", "reviews_today", "reviews_today_date", "total_reviews", "total_new_seen"])

    session.index += 1
    if session.index >= len(session.queue):
        session.status = "finished"
        session.finished_at = timezone.now()
        session.save(update_fields=["index", "status", "finished_at"])
        due, new, total = compute_due_new_counts(request.user, session.deck)
        ud.cached_due_count, ud.cached_new_count, ud.cached_total_in_deck, ud.cached_at = due, new, total, timezone.now()
        ud.save(update_fields=["cached_due_count", "cached_new_count", "cached_total_in_deck", "cached_at"])
        return render(request, "study/done_partial.html")

    session.rotate_nonce()
    session.save(update_fields=["index", "current_nonce"])

    next_card = Flashcard.objects.get(id=session.queue[session.index])
    return render(request, "study/card_partial.html", {"session": session, "card": next_card})