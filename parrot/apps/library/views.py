from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Exists, OuterRef

from apps.core.models import Deck
from apps.library.models import UserDeck
from apps.library.services.counts import compute_due_new_counts
from apps.study.models import StudySession


@login_required
def library(request):
    user_decks = (
        UserDeck.objects
        .select_related("deck", "deck__language")
        .filter(user=request.user)
        .annotate(
            has_active_session=Exists(
                StudySession.objects.filter(
                    user=request.user,
                    deck_id=OuterRef("deck_id"),
                    status="active",
                )
            )
        )
        .order_by("deck__language__name", "deck__title")
    )

    for ud in user_decks:
        if ud.cached_at is None:
            due, new, total = compute_due_new_counts(request.user, ud.deck)
            ud.cached_due_count = due
            ud.cached_new_count = new
            ud.cached_total_in_deck = total
            ud.cached_at = timezone.now()
            ud.save(update_fields=["cached_due_count", "cached_new_count", "cached_total_in_deck", "cached_at"])

    return render(request, "library/library.html", {"user_decks": user_decks})


@login_required
def add_to_library(request, deck_id: int):
    deck = get_object_or_404(Deck, id=deck_id)
    obj = UserDeck.objects.get_or_create(user=request.user, deck=deck)
    print(obj)
    if request.headers.get("HX-Request"):
        return HttpResponse("OK")
    return redirect("library")


@login_required
def remove_from_library(request, deck_id: int):
    deck = get_object_or_404(Deck, id=deck_id)
    UserDeck.objects.filter(user=request.user, deck=deck).delete()
    if request.headers.get("HX-Request"):
        return HttpResponse("OK")
    return redirect("library")
