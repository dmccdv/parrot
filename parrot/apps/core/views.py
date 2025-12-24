from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render
from apps.core.models import Language, Deck


def explore(request):
    languages = Language.objects.all().prefetch_related(
        Prefetch("decks", queryset=Deck.objects.all().order_by("title"))
    )
    return render(request, "core/explore.html", {"languages": languages})
