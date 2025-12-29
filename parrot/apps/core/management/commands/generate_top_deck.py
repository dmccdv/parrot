import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Language, Deck, Flashcard, DeckCard


class Command(BaseCommand):
    help = "Generate/update a Top N deck from a CSV file for a given language."

    def add_arguments(self, parser):
        parser.add_argument("--lang", required=True, help="Language code, e.g. cs, pt-BR, es")
        parser.add_argument("--name", required=False, help="Language display name, e.g. Czech")
        parser.add_argument("--title", required=True, help='Deck title, e.g. "Top 1000"')
        parser.add_argument("--csv", required=True, help="Path to CSV file")
        parser.add_argument("--n", type=int, default=1000, help="How many rows to load (default 1000)")
        parser.add_argument("--source", default="csv", help="Deck source label (default csv)")
        parser.add_argument("--deck-version", default="", help="Deck version label (optional)")

    def handle(self, *args, **opts):
        lang_code: str = opts["lang"].strip()
        lang_name: str | None = opts.get("name")
        deck_title: str = opts["title"].strip()
        csv_path = Path(opts["csv"])
        n: int = opts["n"]
        source: str = opts["source"]
        version: str = opts["deck_version"]

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        rows: list[dict] = []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV has no header row.")
            if "word" not in reader.fieldnames:
                raise CommandError(f"CSV must contain a 'word' column. Found: {reader.fieldnames}")

            for i, row in enumerate(reader, start=1):
                if i > n:
                    break
                word = (row.get("word") or "").strip()
                if not word:
                    continue

                rows.append({
                    "rank": int(row.get("rank") or i),
                    "word": word,
                    "translation": (row.get("translation") or "").strip(),
                    "context": (row.get("context") or row.get("context_sentence") or "").strip(),
                })

        if not rows:
            raise CommandError("No valid rows found in CSV.")

        rows.sort(key=lambda r: r["rank"])

        with transaction.atomic():
            language_defaults = {}
            if lang_name:
                language_defaults["name"] = lang_name.strip()

            language, created = Language.objects.get_or_create(
                code=lang_code,
                defaults=language_defaults or None,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created language {language.code}"))
            else:
                if lang_name and language.name != lang_name.strip():
                    language.name = lang_name.strip()
                    language.save(update_fields=["name"])

            deck, deck_created = Deck.objects.get_or_create(
                language=language,
                title=deck_title,
                defaults={
                    "description": "",
                    "is_generated": True,
                    "source": source,
                    "version": version,
                },
            )
            if not deck_created:
                changed = False
                if not deck.is_generated:
                    deck.is_generated = True
                    changed = True
                if deck.source != source:
                    deck.source = source
                    changed = True
                if version and deck.version != version:
                    deck.version = version
                    changed = True
                if changed:
                    deck.save(update_fields=["is_generated", "source", "version"])

            created_cards = 0
            updated_cards = 0
            attached = 0

            for r in rows:
                card, c_created = Flashcard.objects.get_or_create(
                    language=language,
                    word=r["word"],
                    defaults={
                        "translation": r["translation"],
                        "context_sentence": r["context"],
                        "frequency_rank": r["rank"],
                    },
                )
                if c_created:
                    created_cards += 1
                else:
                    changed_fields = []
                    if r["translation"] and card.translation != r["translation"]:
                        card.translation = r["translation"]
                        changed_fields.append("translation")
                    if r["context"] and card.context_sentence != r["context"]:
                        card.context_sentence = r["context"]
                        changed_fields.append("context_sentence")
                    if card.frequency_rank is None or (r["rank"] and r["rank"] < card.frequency_rank):
                        card.frequency_rank = r["rank"]
                        changed_fields.append("frequency_rank")

                    if changed_fields:
                        card.save(update_fields=changed_fields)
                        updated_cards += 1

                dc, dc_created = DeckCard.objects.get_or_create(
                    deck=deck,
                    card=card,
                    defaults={"position": r["rank"]},
                )
                if not dc_created and dc.position != r["rank"]:
                    dc.position = r["rank"]
                    dc.save(update_fields=["position"])
                if dc_created:
                    attached += 1

            self.stdout.write(self.style.SUCCESS(
                f"Deck '{deck.title}' ({language.code}) ready. "
                f"Cards created: {created_cards}, updated: {updated_cards}, attached: {attached}."
            ))
