from django.db import models
from django.conf import settings


class Language(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}  ({self.code})"
    

class Deck(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="decks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_generated = models.BooleanField(default=False)
    source = models.CharField(max_length=200, blank=True)
    version = models.CharField(max_length=64, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    is_public = models.BooleanField(null=False, default=False)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_decks",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["language", "title"], name="uniq_deck_title_per_language"),
        ]
        indexes = [
            models.Index(fields=["language", "is_generated"]),
        ]
        ordering = ["language__name", "title"]
    def __str__(self):
        return f"{self.title} ({self.language.code})"


class Flashcard(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="cards")
    word = models.CharField(max_length=200)
    translation = models.CharField(max_length=400, blank=True)
    context_sentence = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    frequency_rank = models.PositiveIntegerField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_cards",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["language", "word"], name="uniq_word_per_language"),
        ]
        indexes = [
            models.Index(fields=["language", "frequency_rank"]),
        ]
        ordering = ["language__name", "frequency_rank", "word"]

    def __str__(self):
        return f"{self.word} ({self.language.code})"
    

class DeckCard(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="deck_cards")
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name="deck_cards")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["deck", "card"], name="uniq_card_in_deck"),
        ]
        indexes = [
            models.Index(fields=["deck", "position"]),
            models.Index(fields=["deck", "card"]),
        ]
        ordering= ["deck_id", "position"]