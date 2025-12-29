from django.db.models import Prefetch, Q, Count, Exists, OuterRef
from django.shortcuts import render
from apps.core.models import Language, Deck
from apps.library.models import UserDeck
from apps.study.models import StudySession


def explore(request):
    decks_qs = Deck.objects.filter(is_public=True).order_by("title")

    if request.user.is_authenticated:
        decks_qs = decks_qs.annotate(
            total_cards=Count("deck_cards", distinct=True),
            known_cards=Count(
                "deck_cards__card__progress",
                filter=Q(deck_cards__card__progress__user=request.user),
                distinct=True,
            ),
            in_library=Exists(
                UserDeck.objects.filter(
                    user=request.user,
                    deck=OuterRef("pk"),
                )
            ),
            has_active_session=Exists(
                StudySession.objects.filter(
                    user=request.user,
                    deck=OuterRef("pk"),
                    status="active",
                )
            ),
        )
    else:
        decks_qs = decks_qs.annotate(
            total_cards=Count("deck_cards", distinct=True),
        )

    languages = Language.objects.all().prefetch_related(
        Prefetch("decks", queryset=decks_qs)
    ).order_by("name")

    return render(request, "core/explore.html", {"languages": languages})
