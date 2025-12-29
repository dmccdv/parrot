from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Exists, OuterRef, Max
from django.db import transaction

from apps.core.models import Deck, Flashcard, DeckCard
from apps.library.models import UserDeck
from apps.library.services.counts import compute_due_new_counts
from apps.library.forms import UserDeckSettingsForm, DeckCreateForm, CardCreateForm, CardEditForm, DeckVisibilityForm
from apps.study.models import StudySession

def _require_deck_owner(request, deck: Deck):
    if deck.created_by_id != request.user.id:
        return HttpResponseForbidden("You can only manage decks you created.")
    return None


@login_required
def library(request):
    user_decks = (
        UserDeck.objects.select_related("deck", "deck__language")
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
            ud.save(
                update_fields=[
                    "cached_due_count",
                    "cached_new_count",
                    "cached_total_in_deck",
                    "cached_at",
                ]
            )

    return render(request, "library/library.html", {"user_decks": user_decks})


@login_required
def add_to_library(request, deck_id: int):
    deck = get_object_or_404(Deck, id=deck_id)
    if not deck.is_public:
        return HttpResponseForbidden("This deck is private.")
    UserDeck.objects.get_or_create(user=request.user, deck=deck)
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


@login_required
def deck_settings(request, deck_id: int):
    ud = get_object_or_404(UserDeck, user=request.user, deck_id=deck_id)

    if request.method == "POST":
        form = UserDeckSettingsForm(request.POST, instance=ud)
        if form.is_valid():
            form.save()
            messages.success(request, "Deck settings saved.")
            return redirect("library")
    else:
        form = UserDeckSettingsForm(instance=ud)

    return render(request, "library/deck_settings.html", {"ud": ud, "form": form})


@login_required
@transaction.atomic
def deck_create(request):
    if request.method == "POST":
        form = DeckCreateForm(request.POST)
        if form.is_valid():
            deck: Deck = form.save(commit=False)
            deck.is_generated = False
            deck.created_by = request.user
            deck.save()

            UserDeck.objects.get_or_create(user=request.user, deck=deck)

            return redirect("deck_manage", deck_id=deck.id)
    else:
        form = DeckCreateForm()

    return render(request, "library/deck_create.html", {"form": form})


@login_required
def deck_manage(request, deck_id: int):
    deck = get_object_or_404(Deck.objects.select_related("language"), id=deck_id)

    get_object_or_404(UserDeck, user=request.user, deck=deck)

    denied = _require_deck_owner(request, deck)
    if denied:
        return denied

    cards = (
        Flashcard.objects
        .filter(deck_cards__deck=deck)
        .distinct()
        .order_by("deck_cards__position", "id")
    )

    return render(request, "library/deck_manage.html", {"deck": deck, "cards": cards})


@login_required
@transaction.atomic
def card_create(request, deck_id: int):
    deck = get_object_or_404(Deck.objects.select_related("language"), id=deck_id)
    get_object_or_404(UserDeck, user=request.user, deck=deck)

    denied = _require_deck_owner(request, deck)
    if denied:
        return denied
    
    if request.method == "POST":
        form = CardCreateForm(request.POST)
        if form.is_valid():
            card: Flashcard = form.save(commit=False)
            card.language = deck.language
            card.created_by = request.user
            card.save()

            max_pos = DeckCard.objects.filter(deck=deck).aggregate(m=Max("position"))["m"] or 0
            DeckCard.objects.create(deck=deck, card=card, position=max_pos + 1)

            return redirect("deck_manage", deck_id=deck.id)
    else:
        form = CardCreateForm()

    return render(request, "library/card_create.html", {"deck": deck, "form": form})


@login_required
@transaction.atomic
def card_edit(request, card_id: int):
    card = get_object_or_404(Flashcard.objects.select_related("language"), id=card_id)

    if card.created_by_id != request.user.id:
        return HttpResponseForbidden("You can only edit cards you created.")

    if request.method == "POST":
        form = CardEditForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or "library")
    else:
        form = CardEditForm(instance=card)

    return render(request, "library/card_edit.html", {"card": card, "form": form, "next": request.GET.get("next", "")})


@login_required
def deck_visibility(request, deck_id: int):
    deck = get_object_or_404(Deck.objects.select_related("language"), id=deck_id)

    if deck.created_by_id != request.user.id:
        return HttpResponseForbidden("Only the creator can change visibility.")

    if request.method == "POST":
        form = DeckVisibilityForm(request.POST, instance=deck)
        if form.is_valid():
            form.save()
            messages.success(request, "Deck visibility updated.")
            return redirect("library")
    else:
        form = DeckVisibilityForm(instance=deck)

    return render(request, "library/deck_visibility.html", {"deck": deck, "form": form})