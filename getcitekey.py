import re
import string
import hashlib
import os

def load_abbreviations(filepath):
    abbrev_map = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    abbrev_map[parts[1].strip().lower()] = parts[0].strip()
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    return abbrev_map

def get_entry_hash(author, year, title):
    # Creates a unique fingerprint to detect papers already in the output file
    raw_str = f"{author.lower()}{year}{title.lower()}".replace(" ", "")
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()

def get_first_author(author_str):
    first_author_full = author_str.split(' and ')[0].strip()
    last_name = first_author_full.split(',')[0].strip() if ',' in first_author_full else first_author_full.split(' ')[-1].strip()
    return re.sub(r'[^a-zA-Z]', '', last_name).capitalize()

def parse_entries(content):
    # Helper to find all BibTeX entries in a string
    return re.findall(r'@(\w+)\s*\{\s*([^,]+)\s*,\s*(.*?)\n\}', content, re.DOTALL)

def update_bib_keys(input_file, output_file, abbrev_file):
    abbrevs = load_abbreviations(abbrev_file)
    
    # 1. Load existing data from output.bib to see what is already processed
    seen_hashes = set()
    used_keys = {}
    existing_content = ""
    
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            existing_entries = parse_entries(existing_content)
            for _, key, body in existing_entries:
                # Track keys and hashes so we don't repeat them
                auth = re.search(r'author\s*=\s*[\{{\"]?(.*?)[\}}\"]?\s*,?\n', body, re.I)
                yr = re.search(r'year\s*=\s*[\{{\"]?(.*?)[\}}\"]?\s*,?\n', body, re.I)
                ttl = re.search(r'title\s*=\s*[\{{\"]?(.*?)[\}}\"]?\s*,?\n', body, re.I)
                if auth and yr and ttl:
                    seen_hashes.add(get_entry_hash(auth.group(1), yr.group(1), ttl.group(1)))
                
                # Strip the numeric suffix to track base key usage (e.g., Maity2024ApJ)
                base = re.sub(r'\d+$', '', key)
                used_keys[base] = max(used_keys.get(base, 0), int(re.search(r'(\d+)$', key).group(1) if re.search(r'\d+$', key) else 0))

    # 2. Read input.bib
    with open(input_file, 'r', encoding='utf-8') as f:
        input_content = f.read()
    
    new_entries = parse_entries(input_content)
    added_count = 0
    updated_entries = []

    for entry_type, _, body in new_entries:
        def get_field(name):
            m = re.search(fr'{name}\s*=\s*[\{{\"]?(.*?)[\}}\"]?\s*,?\n', body, re.I)
            return m.group(1).strip() if m else ""

        author = get_field('author')
        year = get_field('year')
        title = get_field('title')
        journal = get_field('journal').lower()

        # Check if this paper is already in the output.bib
        fingerprint = get_entry_hash(author, year, title)
        if fingerprint in seen_hashes:
            continue

        # Generate New Key with Numeric Suffix
        first_author = get_first_author(author)
        journal_short = abbrevs.get(journal, "Misc")
        base_key = f"{first_author}{year}{journal_short}"
        
        used_keys[base_key] = used_keys.get(base_key, 0) + 1
        final_key = f"{base_key}{used_keys[base_key]}"

        updated_entries.append(f"@{entry_type}{{{final_key},\n{body}\n}}")
        seen_hashes.add(fingerprint)
        added_count += 1

    # 3. Append only new entries to the existing output file
    if updated_entries:
        with open(output_file, 'a', encoding='utf-8') as f:
            if existing_content and not existing_content.endswith('\n\n'):
                f.write('\n\n')
            f.write("\n\n".join(updated_entries))
        print(f"Added {added_count} new papers to {output_file}.")
    else:
        print("No new papers to add.")

if __name__ == "__main__":
    update_bib_keys('input.bib', 'updated_metadata.bib', 'JournalAbbrev.list')
