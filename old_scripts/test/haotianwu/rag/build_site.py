"""
Build a static HTML website from the gene JSON data.
Produces a single index.html that displays gene information
in a review-article style with source citations.
"""
import json
from pathlib import Path
from collections import defaultdict
from html import escape

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent / "site"


def load_all_data(data_dir: Path):
    """Load all JSON files, return list of dicts."""
    docs = []
    for f in sorted(data_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                doc = json.load(fp)
                doc["_file"] = f.stem  # e.g. "34998383"
                docs.append(doc)
        except Exception as e:
            print(f"Skipping {f.name}: {e}")
    return docs


TRAIT_GROUPS = [
    ("Abiotic Stress Tolerance", ["drought", "salt", "cold", "heat", "temperature", "osmotic", "abiotic", "freezing", "chilling", "dehydration", "waterlogging", "flood", "heavy metal", "cadmium", "aluminum", "UV", "oxidative"]),
    ("Biotic Stress / Disease Resistance", ["disease", "pathogen", "fungal", "bacterial", "virus", "resistance", "immune", "defense", "biotic", "blight", "blast", "rust", "smut", "wilt", "insect", "herbivore"]),
    ("Nutrient / Vitamin / Mineral Content", ["vitamin", "mineral", "iron", "zinc", "calcium", "selenium", "nutrient", "biofortif", "folate", "carotenoid", "provitamin", "tocopherol", "ascorb"]),
    ("Yield / Growth / Development", ["yield", "grain", "growth", "biomass", "tiller", "flowering", "heading", "maturity", "plant height", "root", "seed size", "panicle", "fruit"]),
    ("Quality / Starch / Protein", ["quality", "starch", "protein", "amylose", "gluten", "storage protein", "grain quality", "milling", "cooking"]),
    ("Lipid / Fatty Acid Metabolism", ["lipid", "fatty acid", "oil content", "wax", "cutin", "suberin", "triacylglycerol"]),
    ("Amino Acid / Nitrogen Metabolism", ["amino acid", "nitrogen", "glutam", "aspart", "lysine", "tryptophan", "proline", "nitrate", "ammonium"]),
    ("Flavonoid / Phenylpropanoid / Secondary Metabolism", ["flavonoid", "anthocyanin", "phenylpropanoid", "lignin", "phenolic", "isoflavone", "chalcone", "secondary metabol"]),
    ("Hormone Signaling", ["hormone", "auxin", "gibberellin", "ethylene", "abscisic", "cytokinin", "brassinosteroid", "jasmonate", "salicylic acid"]),
    ("Photosynthesis / Carbon Fixation", ["photosyn", "chloro", "carbon fixation", "rubisco", "light harvest", "thylakoid"]),
    ("Sugar / Sucrose Metabolism", ["sugar", "sucrose", "fructose", "glucose", "trehalose", "hexose"]),
    ("Transcription Factor / Gene Regulation", ["transcription factor", "WRKY", "MYB", "bHLH", "NAC", "AP2", "ERF", "MADS", "zinc finger"]),
]


def classify_trait(raw_trait):
    """Map a raw Trait_Category string to a broad group."""
    low = raw_trait.lower()
    for group_name, keywords in TRAIT_GROUPS:
        for kw in keywords:
            if kw.lower() in low:
                return group_name
    return "Other"


def collect_genes(docs):
    """Collect all genes grouped by broad trait category."""
    by_trait = defaultdict(list)
    articles = {}

    for doc in docs:
        title = doc.get("Title", "Unknown")
        journal = doc.get("Journal", "Unknown")
        doi = doc.get("DOI", "")
        file_id = doc.get("_file", "")

        ref_key = file_id
        articles[ref_key] = {
            "title": title,
            "journal": journal,
            "doi": doi,
            "file_id": file_id,
        }

        for cat_key in ("Plant_Genes", "Animal_Genes", "Microbial_Genes"):
            for gene in doc.get(cat_key, []):
                raw_trait = gene.get("Trait_Category") or ""
                # Also check research topic for classification
                raw_topic = gene.get("Research_Topic") or ""
                combined = raw_trait + " " + raw_topic
                trait = classify_trait(combined)
                gene_entry = {
                    "gene": gene,
                    "ref_key": ref_key,
                    "category": cat_key.replace("_Genes", ""),
                    "original_trait": raw_trait,
                }
                by_trait[trait].append(gene_entry)

    return by_trait, articles


def esc(text):
    """Escape HTML, return empty string for None."""
    if not text:
        return ""
    return escape(str(text))


def make_citation(ref_key, articles, ref_numbers):
    """Create a numbered inline citation like [1]."""
    art = articles.get(ref_key, {})
    num = ref_numbers.get(ref_key, "?")
    title = art.get("title", "Unknown")
    journal = art.get("journal", "")
    doi = art.get("doi", "")
    tooltip = f"{title}. {journal}"
    if doi:
        return f'<a class="citation" href="#ref-{esc(ref_key)}" title="{esc(tooltip)}">[{num}]</a>'
    return f'<a class="citation" href="#ref-{esc(ref_key)}" title="{esc(tooltip)}">[{num}]</a>'


def render_gene_card(gene_entry, articles, ref_numbers, idx):
    """Render a single gene as an HTML card."""
    g = gene_entry["gene"]
    ref_key = gene_entry["ref_key"]
    cat = gene_entry["category"]
    citation = make_citation(ref_key, articles, ref_numbers)

    gene_name = esc(g.get("Gene_Name", "Unknown"))
    species = esc(g.get("Species_Latin_Name") or g.get("Species", ""))

    parts = []
    parts.append(f'<div class="gene-card" id="gene-{idx}">')
    parts.append(f'  <h3><span class="gene-name">{gene_name}</span>')
    if species:
        parts.append(f'    <span class="species">({species})</span>')
    parts.append(f'    <span class="cat-badge cat-{cat.lower()}">{cat}</span>')
    parts.append(f'  </h3>')

    # Key findings - the most important section
    findings = g.get("Summary_key_Findings_of_Core_Gene")
    if findings:
        parts.append(f'  <div class="section">')
        parts.append(f'    <h4>Key Findings</h4>')
        # Split numbered findings
        lines = findings.strip().split("\n")
        parts.append(f'    <ul class="findings">')
        for line in lines:
            line = line.strip()
            if line:
                # Remove leading "1. " etc.
                clean = line.lstrip("0123456789. ")
                parts.append(f'      <li>{esc(clean)} {citation}</li>')
        parts.append(f'    </ul>')
        parts.append(f'  </div>')

    # Core phenotypic effect
    effect = g.get("Core_Phenotypic_Effect")
    if effect:
        parts.append(f'  <div class="section">')
        parts.append(f'    <h4>Core Phenotypic Effect</h4>')
        parts.append(f'    <p>{esc(effect)} {citation}</p>')
        parts.append(f'  </div>')

    # Regulatory mechanism
    mech = g.get("Regulatory_Mechanism")
    if mech:
        parts.append(f'  <div class="section">')
        parts.append(f'    <h4>Regulatory Mechanism</h4>')
        parts.append(f'    <p>{esc(mech)} {citation}</p>')
        parts.append(f'  </div>')

    # Pathways
    pathways = []
    for pkey, plabel in [("Regulatory_Pathway", "Regulatory"),
                          ("Biosynthetic_Pathway", "Biosynthetic")]:
        val = g.get(pkey)
        if val:
            pathways.append((plabel, val))
    if pathways:
        parts.append(f'  <div class="section">')
        parts.append(f'    <h4>Pathways</h4>')
        for plabel, pval in pathways:
            parts.append(f'    <p><strong>{plabel}:</strong> {esc(pval)} {citation}</p>')
        parts.append(f'  </div>')

    # Details table for other fields
    detail_fields = [
        ("Protein_Family_or_Domain", "Protein Family / Domain"),
        ("Expression_Pattern", "Expression Pattern"),
        ("Core_Validation_Method", "Validation Method"),
        ("Breeding_Application_Value", "Breeding Application Value"),
        ("Key_Environment_or_Treatment_Factor", "Environment / Treatment"),
    ]
    has_details = any(g.get(k) for k, _ in detail_fields)
    if has_details:
        parts.append(f'  <details class="more-details">')
        parts.append(f'    <summary>More Details</summary>')
        parts.append(f'    <table class="detail-table">')
        for k, label in detail_fields:
            val = g.get(k)
            if val:
                parts.append(f'      <tr><td class="dl">{label}</td><td>{esc(val)}</td></tr>')
        parts.append(f'    </table>')
        parts.append(f'  </details>')

    parts.append(f'</div>')
    return "\n".join(parts)


def build_html(by_trait, articles):
    """Build the full HTML page."""
    # Sort traits by number of genes (descending)
    sorted_traits = sorted(by_trait.items(), key=lambda x: -len(x[1]))

    total_genes = sum(len(v) for v in by_trait.values())
    total_articles = len(articles)

    # Build reference number mapping (sorted by file_id for consistency)
    sorted_refs = sorted(articles.keys())
    ref_numbers = {ref_key: i + 1 for i, ref_key in enumerate(sorted_refs)}

    # Build TOC and body
    toc_items = []
    body_sections = []
    gene_idx = 0

    for trait, gene_entries in sorted_traits:
        section_id = f"trait-{hash(trait) % 100000}"
        toc_items.append(
            f'<li><a href="#{section_id}">{esc(trait)}</a> <span class="count">({len(gene_entries)})</span></li>'
        )

        cards = []
        for ge in gene_entries:
            cards.append(render_gene_card(ge, articles, ref_numbers, gene_idx))
            gene_idx += 1

        body_sections.append(f"""
<section id="{section_id}">
  <h2>{esc(trait)} <span class="count">({len(gene_entries)} genes)</span></h2>
  {"".join(cards)}
</section>
""")

    # Build references section
    ref_items = []
    for ref_key in sorted_refs:
        art = articles[ref_key]
        num = ref_numbers[ref_key]
        doi_link = ""
        if art["doi"]:
            doi_link = f' DOI: <a href="https://doi.org/{esc(art["doi"])}" target="_blank">{esc(art["doi"])}</a>'
        ref_items.append(
            f'<li id="ref-{esc(ref_key)}" value="{num}">{esc(art["title"])}. <i>{esc(art["journal"])}</i>.{doi_link}</li>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Crop Gene Knowledge Base - Review Report</title>
<style>
:root {{
  --primary: #1a5276;
  --accent: #2980b9;
  --bg: #fdfdfd;
  --card-bg: #fff;
  --border: #e0e0e0;
  --text: #333;
  --text-light: #666;
  --plant: #27ae60;
  --animal: #e67e22;
  --microbial: #8e44ad;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
  color: var(--text);
  background: var(--bg);
  line-height: 1.7;
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 24px 60px;
}}
header {{
  text-align: center;
  padding: 40px 0 30px;
  border-bottom: 2px solid var(--primary);
  margin-bottom: 30px;
}}
header h1 {{
  font-size: 1.8em;
  color: var(--primary);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}}
header .subtitle {{
  font-size: 1em;
  color: var(--text-light);
  font-style: italic;
}}
header .stats {{
  margin-top: 12px;
  font-size: 0.9em;
  color: var(--text-light);
}}

/* Search */
.search-box {{
  margin: 20px 0;
  text-align: center;
}}
.search-box input {{
  width: 100%;
  max-width: 500px;
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
}}
.search-box input:focus {{
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(41,128,185,0.15);
}}

/* TOC */
nav {{
  background: #f7f9fb;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px 24px;
  margin-bottom: 30px;
}}
nav h2 {{
  font-size: 1.1em;
  color: var(--primary);
  margin-bottom: 10px;
}}
nav ul {{
  list-style: none;
  columns: 2;
  column-gap: 24px;
}}
nav li {{
  padding: 3px 0;
  font-size: 0.9em;
}}
nav a {{
  color: var(--accent);
  text-decoration: none;
}}
nav a:hover {{
  text-decoration: underline;
}}
.count {{
  color: var(--text-light);
  font-size: 0.85em;
  font-weight: normal;
}}

/* Sections */
section {{
  margin-bottom: 36px;
}}
section > h2 {{
  font-size: 1.3em;
  color: var(--primary);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin-bottom: 16px;
}}

/* Gene cards */
.gene-card {{
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 16px;
  transition: box-shadow 0.2s;
}}
.gene-card:hover {{
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}}
.gene-card h3 {{
  font-size: 1.1em;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}}
.gene-name {{
  color: var(--primary);
  font-family: "Courier New", monospace;
  font-weight: bold;
}}
.species {{
  font-style: italic;
  font-weight: normal;
  font-size: 0.9em;
  color: var(--text-light);
}}
.cat-badge {{
  font-size: 0.7em;
  padding: 2px 8px;
  border-radius: 10px;
  color: #fff;
  font-weight: normal;
}}
.cat-plant {{ background: var(--plant); }}
.cat-animal {{ background: var(--animal); }}
.cat-microbial {{ background: var(--microbial); }}

.gene-card .section {{
  margin-bottom: 10px;
}}
.gene-card h4 {{
  font-size: 0.95em;
  color: var(--primary);
  margin-bottom: 4px;
}}
.gene-card p {{
  font-size: 0.92em;
  text-align: justify;
}}
.findings {{
  list-style: disc;
  margin-left: 20px;
  font-size: 0.92em;
}}
.findings li {{
  margin-bottom: 4px;
}}

/* Citations */
.citation {{
  font-size: 0.75em;
  color: var(--accent);
  text-decoration: none;
  vertical-align: super;
  line-height: 0;
  font-weight: 600;
}}
.citation:hover {{
  text-decoration: underline;
}}

/* Details */
.more-details {{
  margin-top: 8px;
  font-size: 0.9em;
}}
.more-details summary {{
  cursor: pointer;
  color: var(--accent);
  font-size: 0.9em;
}}
.detail-table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}}
.detail-table td {{
  padding: 6px 10px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
  font-size: 0.9em;
}}
.detail-table .dl {{
  width: 180px;
  font-weight: 600;
  color: var(--text-light);
  white-space: nowrap;
}}

/* References */
#references {{
  margin-top: 40px;
  border-top: 2px solid var(--primary);
  padding-top: 20px;
}}
#references h2 {{
  font-size: 1.3em;
  color: var(--primary);
  margin-bottom: 12px;
}}
#references ol {{
  font-size: 0.85em;
  line-height: 1.6;
  padding-left: 24px;
}}
#references li {{
  margin-bottom: 6px;
}}

/* Hide helper */
.hidden {{
  display: none !important;
}}

/* Responsive */
@media (max-width: 600px) {{
  body {{ padding: 12px; }}
  nav ul {{ columns: 1; }}
  .detail-table .dl {{ width: auto; white-space: normal; }}
}}
</style>
</head>
<body>

<header>
  <h1>Crop Nutrient Metabolism Gene Knowledge Base</h1>
  <p class="subtitle">A structured review of key genes extracted from scientific literature</p>
  <p class="stats">{total_articles} articles &middot; {total_genes} gene entries &middot; {len(sorted_traits)} trait categories</p>
</header>

<div class="search-box">
  <input type="text" id="searchInput" placeholder="Search genes, species, pathways..." oninput="filterCards(this.value)">
</div>

<nav>
  <h2>Table of Contents</h2>
  <ul>
    {"".join(toc_items)}
  </ul>
</nav>

{"".join(body_sections)}

<section id="references">
  <h2>References</h2>
  <ol>
    {"".join(ref_items)}
  </ol>
</section>

<script>
function filterCards(query) {{
  query = query.toLowerCase().trim();
  document.querySelectorAll('.gene-card').forEach(card => {{
    if (!query) {{
      card.classList.remove('hidden');
    }} else {{
      const text = card.textContent.toLowerCase();
      card.classList.toggle('hidden', !text.includes(query));
    }}
  }});
}}
</script>

</body>
</html>"""
    return html


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Loading data from {DATA_DIR} ...")
    docs = load_all_data(DATA_DIR)
    print(f"Loaded {len(docs)} documents")

    by_trait, articles = collect_genes(docs)
    print(f"Found {sum(len(v) for v in by_trait.values())} genes in {len(by_trait)} trait categories")

    html = build_html(by_trait, articles)
    out_path = OUTPUT_DIR / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Website generated: {out_path}")
    print(f"Open in browser: file://{out_path.resolve()}")


if __name__ == "__main__":
    main()
