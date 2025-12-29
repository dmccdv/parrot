from django.db import models
from django.conf import settings
from django.utils import timezone


class UserDeck(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_decks")
    deck = models.ForeignKey("core.Deck", on_delete=models.CASCADE, related_name="user_decks")
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    daily_new_limit = models.PositiveIntegerField(default=20)
    chunk_size = models.PositiveIntegerField(default=20)
    new_ratio = models.FloatField(default=2.0)
    
    cached_due_count = models.PositiveIntegerField(default=0)
    cached_new_count = models.PositiveIntegerField(default=0)
    cached_total_in_deck = models.PositiveIntegerField(default=0)
    cached_at = models.DateTimeField(null=True, blank=True)

    last_studied_at = models.DateTimeField(null=True, blank=True)
    reviews_today = models.PositiveIntegerField(default=0)
    reviews_today_date = models.DateField(null=True, blank=True)
    total_reviews = models.PositiveIntegerField(default=0)
    total_new_seen = models.PositiveIntegerField(default=0)

    new_today = models.PositiveIntegerField(default=0)
    new_today_date = models.DateField(null=True, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "deck"], name="uniq_user_deck"),
        ]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "last_studied_at"])
        ]

    def bump_today(self, n=1):
        today = timezone.localdate()
        if self.reviews_today_date != today:
            self.reviews_today_date = today
            self.reviews_today = 0
        self.reviews_today += n
        self.total_reviews += n
        self.last_studied_at = timezone.now()
    
    def bump_new_today(self, n=1):
        today = timezone.localdate()
        if self.new_today_date != today:
            self.new_today_date = today
            self.new_today = 0
        self.new_today += n
        self.total_new_seen += n