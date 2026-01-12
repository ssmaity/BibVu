import re
import string

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

def get_first_author(author_str):
    # Extracts the first author's last name
    first_author_full = author_str.split(' and ')[0].strip()
    if ',' in first_author_full:
        last_name = first_author_full.split(',')[0].strip()
    else:
        last_name = first_author_full.split(' ')[-1].strip()
    
    # Clean name (remove braces and non-letters)
    clean_name = re.sub(r'[^a-zA-Z]', '', last_name)
    return clean_name.capitalize()

def update_bib_keys(input_file, output_file, abbrev_file):
    abbrevs = load_abbreviations(abbrev_file)
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex captures: 1=Type, 2=OldKey, 3=Body
    entries = re.findall(r'@(\w+)\s*\{\s*([^,]+)\s*,\s*(.*?)\n\}', content, re.DOTALL)

    used_keys = {}
    updated_entries = []

    for entry_type, old_key, body in entries:
        def get_field(field_name):
            pattern = fr'{field_name}\s*=\s*[\{{\"]?(.*?)[\}}\"]?\s*,?\n'
            match = re.search(pattern, body, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        author = get_field('author')
        year = get_field('year')
        journal = get_field('journal').lower()

        # Generate Key
        first_author = get_first_author(author)
        journal_short = abbrevs.get(journal, "Misc")
        base_key = f"{first_author}{year}{journal_short}"

        # Handle Repetition (a, b, c suffix)
        if base_key not in used_keys:
            used_keys[base_key] = 0
            final_key = base_key
        else:
            used_keys[base_key] += 1
            suffix = string.ascii_lowercase[used_keys[base_key] - 1]
            final_key = f"{base_key}{suffix}"

        updated_entries.append(f"@{entry_type}{{{final_key},\n{body}\n}}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(updated_entries))

if __name__ == "__main__":
    # Ensure your input file is named 'input.bib' or change it here
    update_bib_keys('input.bib', 'updated_metadata.bib', 'JournalAbbrev.list')
    print("Successfully created updated_metadata.bib")
