from django.shortcuts import render
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from pylatexenc.latex2text import LatexNodes2Text
import string
import re

# Library configuration for quick search links
LIBRARIES = [
    ("GScholar", "http://scholar.google.com/scholar?hl=en&q="),
    ("S2", "https://www.semanticscholar.org/search?q="),
    ("Google", "https://www.google.com/search?q="),
    ("DBLP", "http://dblp.org/search/index.php#query="),
    ("IEEE", "http://ieeexplore.ieee.org/search/searchresult.jsp?queryText="),
    ("ACM", "http://dl.acm.org/results.cfm?query="),
]

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

    # Setup parser with unicode conversion
    parser = BibTexParser()
    parser.customization = convert_to_unicode
    try:
        bib_database = bibtexparser.loads(file_content, parser=parser)
    except Exception as e:
        return render(request, "index.html", {"error": f"Failed to parse BibTeX: {str(e)}"})

    problems = []
    counters = {
        "Missing Fields": 0,
        "Abbreviations": 0,
        "Author Format": 0,
        "Wrong Types": 0,
        "Duplicate IDs": 0,
        "Wrong Fields": 0,
    }
    
    ids_seen = set()
    l2t = LatexNodes2Text()
    
    # Extraction of validation options
    ignore_legacy = request.POST.get("ignore_legacy") == "on"
    ignore_abbreviations = request.POST.get("ignore_abbreviations") == "on"
    ignore_author_format = request.POST.get("ignore_author_format") == "on"

    for entry in bib_database.entries:
        entry_id = entry.get("ID", "unknown")
        entry_type = entry.get("ENTRYTYPE", "unknown").lower()
        
        # Structure for template
        current_entry = {
            "id": entry_id,
            "type": entry_type,
            "title": "",
            "raw": [], # bibtexparser doesn't give raw easily, we'll reconstruct or skip
            "fields": set(entry.keys()),
            "subproblems": [],
        }
        
        # 1. Title handling with pylatexenc
        raw_title = entry.get("title", "")
        if raw_title:
            try:
                current_entry["title"] = l2t.latex_to_text(raw_title)
            except:
                current_entry["title"] = re.sub(r"\}|\{", "", raw_title)
        
        # 2. Duplicate ID Check
        if entry_id in ids_seen:
            current_entry["subproblems"].append(f"Non-unique ID: '{entry_id}'")
            counters["Duplicate IDs"] += 1
        else:
            ids_seen.add(entry_id)

        # 3. Required Fields
        req = resolve_required_fields(entry_type)
        for r_field in req:
            options = r_field.split("/")
            if current_entry["fields"].isdisjoint(options):
                current_entry["subproblems"].append(f"Missing field: '{r_field}'")
                counters["Missing Fields"] += 1

        # 4. Detailed Field-level checks
        for field, value in entry.items():
            if field in ["ENTRYTYPE", "ID"]: continue
            
            # 4a. Abbreviations
            if not ignore_abbreviations and field in ["author", "editor", "journal", "journaltitle", "booktitle"]:
                if "." in value:
                    current_entry["subproblems"].append(f"Abbreviation ('.') found in '{field}'")
                    counters["Abbreviations"] += 1
            
            # 4b. Missing comma in Author (Author Format)
            if not ignore_author_format and field == "author" and "," not in value and " and " not in value.lower():
                 current_entry["subproblems"].append("Author name might be missing a comma (expected 'Last, First')")
                 counters["Author Format"] += 1

            # 4c. Legacy BibTeX fields
            if not ignore_legacy and field in ["journal", "year", "address"]:
                 suggestion = {"journal": "journaltitle", "year": "date", "address": "location"}[field]
                 current_entry["subproblems"].append(f"Legacy BibTeX field '{field}' found. Consider using '{suggestion}'")
                 counters["Wrong Fields"] += 1

            # 4d. Wrong Entry Type heuristic
            if entry_type == "proceedings" and field == "pages":
                current_entry["subproblems"].append("Maybe should be 'inproceedings' (found 'pages' in 'proceedings')")
                counters["Wrong Types"] += 1

        # Reconstruct a pseudo-raw for display
        current_entry["raw"] = [f"@{entry_type}{{{entry_id},"]
        for f, v in entry.items():
            if f not in ["ENTRYTYPE", "ID"]:
                current_entry["raw"].append(f"  {f} = {{{v}}},")
        current_entry["raw"].append("}")
        current_entry["raw_display"] = "<br>".join(current_entry["raw"])
        
        # Links
        remove_punctuation = str.maketrans("", "", string.punctuation)
        base_query = current_entry["title"]
        author = entry.get("author", "")
        if author:
            # Take first author or clean up
            base_query += f" {author.split(' and ')[0]}"
        
        cleaned_query = base_query.translate(remove_punctuation)
        current_entry["links"] = [{"name": name, "url": f"{url}{cleaned_query}"} for name, url in LIBRARIES]

        problems.append(current_entry)

    total_problems = sum(len(p["subproblems"]) for p in problems)

    return render(request, "results.html", {
        "problems": problems,
        "problemCount": total_problems,
        "counters": counters,
        "entriesCount": len(problems),
    })
