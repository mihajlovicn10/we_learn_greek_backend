import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from conjugator import content as verbs
from declinator import content as nouns
from greek_to_greek import content as greek_to_greek

# content/<type>/ directory name -> loader module with validate(data, tier) and sync(rows, tier).
# Types without a loader yet are skipped with a warning, so adding their files early
# doesn't break a deploy.
LOADERS = {
    "nouns": nouns,
    "verbs": verbs,
    "greek-to-greek": greek_to_greek,
}
TIER_FILE = re.compile(r"^tier-([1-9]\d*)\.json$")


class Command(BaseCommand):
    help = "Validate content/<type>/tier-N.json files and load them into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check", action="store_true",
            help="Only validate the files; don't touch the database (used by CI).",
        )
        parser.add_argument(
            "--dir", default=None,
            help="Content directory (default: <project>/content).",
        )

    def handle(self, *args, check=False, dir=None, **options):
        root = Path(dir) if dir else Path(settings.BASE_DIR) / "content"
        if not root.is_dir():
            raise CommandError(f"Content directory not found: {root}")

        loaded, errors = [], []
        for type_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            loader = LOADERS.get(type_dir.name)
            if loader is None:
                self.stderr.write(self.style.WARNING(f"Skipping {type_dir.name}/: no loader for this content type yet"))
                continue
            for path in sorted(type_dir.glob("*.json")):
                rel = path.relative_to(root)
                match = TIER_FILE.match(path.name)
                if not match:
                    errors.append(f"{rel}: file name must be tier-<number>.json")
                    continue
                tier = int(match.group(1))
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"{rel}: not valid UTF-8 JSON ({exc})")
                    continue
                rows, file_errors = loader.validate(data, tier)
                errors.extend(f"{rel}: {e}" for e in file_errors)
                if not file_errors:
                    loaded.append((rel, loader, tier, rows))

        if errors:
            raise CommandError(
                f"{len(errors)} problem(s) in content files; nothing was loaded:\n  " + "\n  ".join(errors)
            )
        if check:
            for rel, _, _, rows in loaded:
                self.stdout.write(f"{rel}: OK ({len(rows)} items)")
            self.stdout.write(self.style.SUCCESS(f"All {len(loaded)} content file(s) are valid."))
            return

        with transaction.atomic():  # all files or none
            results = [(rel, loader.sync(rows, tier)) for rel, loader, tier, rows in loaded]
        for rel, counts in results:
            self.stdout.write(f"{rel}: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(results)} content file(s)."))
