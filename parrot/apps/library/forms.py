from django import forms
from apps.library.models import UserDeck


class UserDeckSettingsForm(forms.ModelForm):
    class Meta:
        model = UserDeck
        fields = ["is_active", "daily_new_limit", "chunk_size", "new_ratio"]

    def clean_daily_new_limit(self):
        v = self.cleaned_data["daily_new_limit"]
        if v > 200:
            raise forms.ValidationError("Daily new limit is too high (max 200).")
        return v

    def clean_chunk_size(self):
        v = self.cleaned_data["chunk_size"]
        if v < 5:
            raise forms.ValidationError("Chunk size must be at least 5.")
        if v > 200:
            raise forms.ValidationError("Chunk size is too large (max 200).")
        return v

    def clean_new_ratio(self):
        v = self.cleaned_data["new_ratio"]
        if v < 0:
            raise forms.ValidationError("New ratio must be >= 0.")
        if v > 1:
            raise forms.ValidationError("New ratio should be between 0 and 1 (e.g. 0.3).")
        return v
