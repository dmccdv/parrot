from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class CardProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="card_progress")
    card = models.ForeignKey("core.Flashcard", on_delete=models.CASCADE, related_name="progress")

    due_at = models.DateTimeField(default=timezone.now())
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    ease = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=0)
    repetitions = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)

    state = models.CharField(max_length=16, default="new", choices=[
        ("new", "new"),
        ("learning", "learning"),
        ("review", "review"),
        ("relearning", "relearning")
    ])

    algorithm = models.CharField(max_length=16, default="sm2")
    algo_state = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="uniq_user_card_progress"),
        ]
        indexes = [
            models.Index(fields=["user", "due_at"]),
            models.Index(fields=["user", "card"]),
        ]


class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_sessions")
    deck = models.ForeignKey("core.Deck", on_delete=models.CASCADE, related_name="study_sessions")

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, default="active", choices=[
        ("active", "active"),
        ("finishe", "finished"),
        ("abandoned", "abandoned"),
    ])

    queue = models.JSONField(default=list)
    index = models.PositiveIntegerField(default=0)

    current_nonce = models.CharField(max_length=36, default="", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "started_at"]),
            models.Index(fields=["deck", "status"]),
        ]

    def rotate_nonce(self):
        self.current_nonce = str(uuid.uuid4())


class ReviewLog(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_logs")
    deck = models.ForeignKey("core.Deck", on_delete=models.CASCADE, related_name="review_logs")
    card = models.ForeignKey("core.Flashcard", on_delete=models.CASCADE, related_name="review_logs")

    quality = models.PositiveSmallIntegerField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    due_before = models.DateTimeField(null=True, blank=True)
    due_after = models.DateTimeField(null=True, blank=True)
    ease_before = models.FloatField(null=True, blank=True)
    ease_after = models.FloatField(null=True, blank=True)
    interval_before = models.PositiveIntegerField(null=True, blank=True)
    interval_after = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "reviewed_at"]),
            models.Index(fields=["user", "deck", "reviewed_at"])
        ]