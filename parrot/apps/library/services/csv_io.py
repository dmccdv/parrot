import csv
import io
from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.db.models import Max

from apps.core.models import Deck, Flashcard, DeckCard


@dataclass
class ParsedRow:
    rank: int | None
    word: str
    translation: str
    context: str


def parse_csv_bytes(data: bytes) -> tuple[list[ParsedRow], list[str]]:

    errors: list[str] = []
    rows: list[ParsedRow] = []

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        errors.append("CSV must be UTF-8 encoded.")
        return [], errors

    f = io.StringIO(text, newline="")
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        return [], ["CSV has no header row."]

    fieldnames = {h.strip().lower() for h in reader.fieldnames if h}
    if "word" not in fieldnames:
        return [], [f"CSV must include a 'word' column. Found: {sorted(fieldnames)}"]

    for i, row in enumerate(reader, start=2):  
        word = (row.get("word") or row.get("Word") or "").strip()
        if not word:
            continue

        rank_raw = (row.get("rank") or row.get("Rank") or "").strip()
        rank: int | None = None
        if rank_raw:
            try:
                rank = int(rank_raw)
            except ValueError:
                errors.append(f"Line {i}: invalid rank '{rank_raw}' (must be an integer).")

        translation = (row.get("translation") or row.get("Translation") or "").strip()
        context = (
            (row.get("context") or row.get("Context") or "")
            or (row.get("context_sentence") or row.get("Context_sentence") or row.get("Context Sentence") or "")
        ).strip()

        rows.append(ParsedRow(rank=rank, word=word, translation=translation, context=context))

    return rows, errors


@transaction.atomic
def import_rows_into_deck(*, deck: Deck, user, rows: Iterable[ParsedRow]) -> dict:

    rows = list(rows)
    if not rows:
        return {"created": 0, "attached": 0, "skipped": 0}

    existing_words = set(
        Flashcard.objects.filter(deck_cards__deck=deck)
        .values_list("word", flat=True)
    )

    max_pos = DeckCard.objects.filter(deck=deck).aggregate(m=Max("position"))["m"] or 0
    next_pos = max_pos + 1

    created = attached = skipped = 0

    for r in rows:
        if r.word in existing_words:
            skipped += 1
            continue

        card = Flashcard.objects.create(
            language=deck.language,
            word=r.word,
            translation=r.translation,
            context_sentence=r.context,
            frequency_rank=r.rank,
            created_by=user,
        )
        created += 1

        DeckCard.objects.create(deck=deck, card=card, position=next_pos)
        attached += 1
        next_pos += 1

    return {"created": created, "attached": attached, "skipped": skipped}


def export_deck_to_csv_text(deck: Deck) -> str:

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["rank", "word", "translation", "context"])

    for dc in (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("position", "id")
    ):
        c = dc.card
        writer.writerow([dc.position, c.word, c.translation, c.context_sentence])

    return output.getvalue()
