"""
Fetch all Chekhov short stories from lib.ru (Библиотека Мошкова).

Usage:
    python manage.py fetch_chekhov_originals
    python manage.py fetch_chekhov_originals --dry-run
    python manage.py fetch_chekhov_originals --skip-existing
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'chekhov'
ORIGINALS_DIR = FIXTURES_DIR / 'originals'
MANIFEST_PATH = FIXTURES_DIR / 'chekhov_manifest.json'

BASE_URL = 'https://lib.ru/LITRA/CHEHOW/'
# lib.ru uses mixed encodings: some pages are cp1251, some koi8-r
ENCODINGS = ['koi8-r', 'cp1251']

# Skip these — they are NOT short stories (novels, plays, memoirs, compilations, etc.)
SKIP_FILES = {
    'sakhalin.txt',      # Остров Сахалин (travel notes, very long)
    'bezotcowshina.txt', # Безотцовщина (play)
    'chajka.txt',        # Чайка (play)
    'sestry.txt',        # Три сестры (play)
    'vanya.txt',         # Дядя Ваня (play)
    'sad.txt',           # Вишнёвый сад (play)
    'ivanov.txt',        # Иванов (play)
    'rasskazy.txt',      # Сборник рассказов (compilation page)
    'vosp.txt',          # Воспоминания современников
    'about_kireev.txt',  # О Кирееве
    'chrono.txt',        # Хронологическая таблица
    'budilnik.txt',      # Будильник (not a story)
    'reading.txt',       # Чтение (article)
}

# Manually curated slug overrides for known stories
SLUG_OVERRIDES = {
    'r_hameleon.txt': 'hameleon',
    'r_anna.txt': 'anna-na-shee',
    'r_kazak.txt': 'kazak',
    'r_kleveta.txt': 'kleveta',
    'r_knyaginya.txt': 'knyaginya',
    'r_korrespondent.txt': 'korrespondent',
    'r_which.txt': 'kotoraya-iz-nih',
    'r_mstitel.txt': 'mstitel',
    'r_ch_week.txt': 'na-ezhenedelnoy-besede',
    'r_letter.txt': 'pismo',
    'r_pari.txt': 'pari',
    'r_poceluj.txt': 'poceluy',
    'r_student.txt': 'student',
    'r_francuz.txt': 'francuz',
    '22.txt': 'kashtanka-22',
    'kashtanka.txt': 'kashtanka',
    '6.txt': 'palata-6',
    '2906.txt': 'dvadcat-devyatogo-avgusta',
}


def detect_encoding(raw_bytes: bytes) -> str:
    """Auto-detect encoding by trying koi8-r and cp1251 and checking for valid Cyrillic."""
    for enc in ENCODINGS:
        try:
            text = raw_bytes.decode(enc)
            # Check if the decoded text contains common Russian words
            # in the title tag (which should always have "Чехов")
            if 'Чехов' in text:
                return enc
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return 'cp1251'  # fallback


def make_slug(filename: str) -> str:
    """Generate a URL-safe slug from filename."""
    if filename in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[filename]
    slug = filename.replace('.txt', '')
    # Remove common prefixes
    for prefix in ('r_', 'ch_'):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
    # Transliterate and clean
    slug = slug.replace('_', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or filename.replace('.txt', '')


def clean_text(raw_html: str) -> str:
    """Clean lib.ru HTML/text: remove headers, footers, HTML tags."""
    soup = BeautifulSoup(raw_html, 'html.parser')

    # Remove <head> (contains <title> text that leaks into get_text)
    head = soup.find('head')
    if head:
        head.decompose()

    # Remove the download form
    for form in soup.find_all('form'):
        form.decompose()

    # Remove <h2> title tags (we'll extract title separately)
    for h2 in soup.find_all('h2'):
        h2.decompose()

    # Remove <ul> wrappers around titles
    for ul in soup.find_all('ul'):
        if not ul.get_text(strip=True):
            ul.decompose()

    # Get text content
    text = soup.get_text()

    # Remove trailing metadata
    text = re.split(r'\n\s*Последнее изменение:', text)[0]
    text = re.split(r'\n\s*Last-modified:', text)[0]

    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)

    # Clean up whitespace
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.rstrip()
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Remove excessive blank lines (max 2 in a row)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_title_from_html(raw_html: str) -> str:
    """Extract the story title from HTML <title> tag."""
    soup = BeautifulSoup(raw_html, 'html.parser')
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Remove "Антон Павлович Чехов. " prefix
        title = re.sub(r'^.*Чехов[.,]\s*', '', title)
        return title.strip()
    return 'Unknown'


class Command(BaseCommand):
    help = 'Fetch all Chekhov short stories from lib.ru'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Only list stories without downloading'
        )
        parser.add_argument(
            '--skip-existing', action='store_true',
            help='Skip files that already exist'
        )
        parser.add_argument(
            '--delay', type=float, default=1.0,
            help='Delay between requests in seconds (default: 1.0)'
        )
        parser.add_argument(
            '--file', type=str, default=None,
            help='Fetch only a specific file (e.g. r_hameleon.txt)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        delay = options['delay']
        single_file = options.get('file')

        ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)

        if single_file:
            stories = [(single_file, make_slug(single_file))]
        else:
            stories = self._fetch_story_list()

        if not stories:
            self.stderr.write(self.style.ERROR('No stories found!'))
            return

        self.stdout.write(f'Found {len(stories)} stories to process\n')

        if dry_run:
            for filename, slug in stories:
                self.stdout.write(f'  {filename} -> {slug}')
            self.stdout.write(self.style.SUCCESS(f'\nDry run: {len(stories)} stories'))
            return

        manifest = []
        fetched = 0
        skipped = 0
        errors = 0

        for i, (filename, slug) in enumerate(stories, 1):
            out_path = ORIGINALS_DIR / f'{slug}.ru.txt'

            if skip_existing and out_path.exists():
                self.stdout.write(f'  [{i}/{len(stories)}] SKIP {slug} (exists)')
                text = out_path.read_text(encoding='utf-8')
                manifest.append({
                    'slug': slug,
                    'filename': filename,
                    'title_ru': slug,
                    'chars': len(text),
                    'status': 'existing',
                })
                skipped += 1
                continue

            try:
                self.stdout.write(
                    f'  [{i}/{len(stories)}] Fetching {filename} -> {slug}...',
                    ending=''
                )

                url = BASE_URL + filename
                resp = requests.get(url, timeout=30)

                if resp.status_code != 200:
                    self.stdout.write(f' ERROR {resp.status_code}')
                    errors += 1
                    manifest.append({
                        'slug': slug,
                        'filename': filename,
                        'title_ru': '',
                        'chars': 0,
                        'status': f'error_{resp.status_code}',
                    })
                    continue

                # lib.ru uses mixed encodings, auto-detect
                encoding = detect_encoding(resp.content)
                decoded = resp.content.decode(encoding, errors='replace')
                title = extract_title_from_html(decoded)
                text = clean_text(decoded)

                if len(text) < 100:
                    self.stdout.write(f' TOO SHORT ({len(text)} chars), skipping')
                    errors += 1
                    continue

                out_path.write_text(text, encoding='utf-8')

                manifest.append({
                    'slug': slug,
                    'filename': filename,
                    'title_ru': title,
                    'chars': len(text),
                    'status': 'fetched',
                })

                self.stdout.write(f' OK ({len(text)} chars) "{title}"')
                fetched += 1

                if i < len(stories):
                    time.sleep(delay)

            except Exception as e:
                self.stdout.write(f' ERROR: {e}')
                errors += 1
                manifest.append({
                    'slug': slug,
                    'filename': filename,
                    'title_ru': '',
                    'chars': 0,
                    'status': f'error: {str(e)[:100]}',
                })

        # Save manifest
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Fetched: {fetched}, Skipped: {skipped}, Errors: {errors}'
        ))
        self.stdout.write(f'Manifest saved to: {MANIFEST_PATH}')

    def _fetch_story_list(self) -> list[tuple[str, str]]:
        """Fetch the index page and extract story links."""
        self.stdout.write('Fetching story index from lib.ru...')

        try:
            resp = requests.get(BASE_URL, timeout=30)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to fetch index: {e}'))
            return []

        encoding = detect_encoding(resp.content)
        decoded = resp.content.decode(encoding, errors='replace')
        soup = BeautifulSoup(decoded, 'html.parser')

        stories = []
        seen_files = set()

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Only .txt files
            if not href.endswith('.txt'):
                continue

            # Extract just the filename
            filename = href.split('/')[-1]

            # Skip non-story files
            if filename in SKIP_FILES:
                continue

            # Skip duplicates
            if filename in seen_files:
                continue
            seen_files.add(filename)

            slug = make_slug(filename)
            stories.append((filename, slug))

        return stories
