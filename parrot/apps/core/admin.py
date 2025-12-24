from django.contrib import admin
from .models import Language, Deck, Flashcard, DeckCard

class DeckCardInline(admin.TabularInline):
    model = DeckCard
    extra = 0

@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("title", "language", "is_generated", "source")
    list_filter = ("language", "is_generated")
    search_fields = ("title",)
    inlines = [DeckCardInline]

admin.site.register(Language)
admin.site.register(Flashcard)
