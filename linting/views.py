from django.shortcuts import render
import string
import re

# Library configuration for quick search links
LIBRARIES = [
    ("Scholar", "http://scholar.google.de/scholar?hl=en&q="),
    ("Google", "https://www.google.com/search?q="),
    ("DBLP", "http://dblp.org/search/index.php#query="),
    ("IEEE", "http://ieeexplore.ieee.org/search/searchresult.jsp?queryText="),
    ("ACM", "http://dl.acm.org/results.cfm?query="),
]

# Required fields definition
REQUIRED_FIELDS = {
    "article": ["author", "title", "journaltitle/journal", "year/date"],
    "book": ["author", "title", "year/date"],
    "mvbook": "book",
    "inbook": ["author", "title", "booktitle", "year/date"],
    "bookinbook": "inbook",
    "suppbook": "inbook",
    "booklet": ["author/editor", "title", "year/date"],
    "collection": ["editor", "title", "year/date"],
    "mvcollection": "collection",
    "incollection": ["author", "title", "booktitle", "year/date"],
    "suppcollection": "incollection",
    "manual": ["author/editor", "title", "year/date"],
    "misc": ["author/editor", "title", "year/date"],
    "online": ["author/editor", "title", "year/date", "url"],
    "patent": ["author", "title", "number", "year/date"],
    "periodical": ["editor", "title", "year/date"],
    "suppperiodical": "article",
    "proceedings": ["title", "year/date"],
    "mvproceedings": "proceedings",
    "inproceedings": ["author", "title", "booktitle", "year/date"],
    "reference": "collection",
    "mvreference": "collection",
    "inreference": "incollection",
    "report": ["author", "title", "type", "institution", "year/date"],
    "thesis": ["author", "title", "type", "institution", "year/date"],
    "unpublished": ["author", "title", "year/date"],
    "mastersthesis": ["author", "title", "institution", "year/date"],
    "techreport": ["author", "title", "institution", "year/date"],
    "conference": "inproceedings",
    "electronic": "online",
    "phdthesis": "mastersthesis",
    "www": "online",
    "school": "mastersthesis",
}

def resolve_required_fields(entry_type):
    target = REQUIRED_FIELDS.get(entry_type.lower(), "misc")
    while isinstance(target, str):
        target = REQUIRED_FIELDS.get(target, ["author", "title", "year/date"])
    return target

def index(request):
    return render(request, "index.html")

def validate(request):
    file_content = request.POST.get("file", "")
    if not file_content:
        return render(request, "index.html", {"error": "No content provided"})

    problems = []
    ids_seen = set()
    
    # Current entry state
    current_entry = {
        "id": "",
        "type": "",
        "title": "",
        "raw": [],
        "fields": set(),
        "subproblems": [],
    }
    
    counters = {
        "Missing Fields": 0,
        "Flawed Names": 0,
        "Wrong Types": 0,
        "Duplicate IDs": 0,
        "Wrong Fields": 0,
        "Missing Commas": 0
    }

    remove_punctuation = str.maketrans("", "", string.punctuation)
    last_line_num = -1

    lines = file_content.splitlines()
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # New Entry Start
        if line_stripped.startswith("@"):
            if current_entry["id"]:
                finalize_entry(current_entry, problems, counters, ids_seen)
            
            try:
                cid = line_stripped.split("{")[1].rstrip(", ")
            except IndexError:
                cid = "unknown"
                
            current_entry = {
                "id": cid,
                "type": line_stripped.split("{")[0].strip("@ "),
                "title": "",
                "raw": [line],
                "fields": set(),
                "subproblems": [],
            }
            
            if line_stripped[-1] != ",":
                current_entry["subproblems"].append(f"Missing comma at '@{cid}' definition")
                counters["Missing Commas"] += 1

        # Entry Closing
        elif line_stripped.startswith("}"):
            current_entry["raw"].append(line)
            finalize_entry(current_entry, problems, counters, ids_seen)
            current_entry = {"id": "", "type": "", "title": "", "raw": [], "fields": set(), "subproblems": []}

        # Entry Fields
        elif "=" in line_stripped:
            current_entry["raw"].append(line)
            field_name = line_stripped.split("=")[0].strip().lower()
            field_value = line_stripped.split("=")[1].strip(", {}")
            current_entry["fields"].add(field_name)
            
            if field_name == "title":
                current_entry["title"] = re.sub(r"\}|\{", "", field_value)
            
            # Simple heuristic checks
            if current_entry["type"].lower() == "proceedings" and field_name == "pages":
                current_entry["subproblems"].append("Maybe should be 'inproceedings' (has pages)")
                counters["Wrong Types"] += 1
            
            if line_stripped[-1] != ",":
                current_entry["subproblems"].append(f"Missing comma at end of '{field_name}' field")
                counters["Missing Commas"] += 1
        
        elif line_stripped:
            current_entry["raw"].append(line)

    # Calculate final stats
    total_problems = sum(len(p["subproblems"]) for p in problems)
    
    # Pre-render logic for links
    for p in problems:
        cleaned_title = p["title"].translate(remove_punctuation)
        p["links"] = [{"name": name, "url": f"{url}{cleaned_title}"} for name, url in LIBRARIES]
        p["raw_display"] = "<br>".join(p["raw"])

    return render(request, "results.html", {
        "problems": problems,
        "problemCount": total_problems,
        "counters": counters,
        "entriesCount": len(problems),
    })

def finalize_entry(entry, problems_list, counters, ids_seen):
    if not entry["id"]:
        return

    # Unique ID check
    if entry["id"] in ids_seen:
        entry["subproblems"].append(f"Non-unique ID: '{entry['id']}'")
        counters["Duplicate IDs"] += 1
    else:
        ids_seen.add(entry["id"])

    # Required field check
    req = resolve_required_fields(entry["type"])
    for r_field in req:
        options = r_field.split("/")
        if entry["fields"].isdisjoint(options):
            entry["subproblems"].append(f"Missing field: '{r_field}'")
            counters["Missing Fields"] += 1
            
    problems_list.append(entry)
