#!/usr/bin/env python3

import argparse
import csv
import re
import sys
import time
from typing import Optional, List

from Bio import Entrez

# ----------------------------
# User-configurable species map
# ----------------------------
SPECIES_ABBREV_MAP = {
    "G. max": "Glycine max",
    "A. thaliana": "Arabidopsis thaliana",
    "O. sativa": "Oryza sativa",
    "Z. mays": "Zea mays",
    "N. tabacum": "Nicotiana tabacum",
}

# Optional genus fallback for patterns like "G. max"
GENUS_MAP = {
    "G.": "Glycine",
    "A.": "Arabidopsis",
    "O.": "Oryza",
    "Z.": "Zea",
    "N.": "Nicotiana",
}


def normalize_species_name(species: str) -> str:
    """
    Convert abbreviated species names like 'G. max' to 'Glycine max'.
    If already a full binomial name, return unchanged.
    """
    if not species:
        return ""

    s = species.strip()

    if s in SPECIES_ABBREV_MAP:
        return SPECIES_ABBREV_MAP[s]

    # Already looks like "Genus species"
    if re.match(r"^[A-Z][a-z]+ [a-z][a-zA-Z-]*$", s):
        return s

    # Try expanding patterns like "G. max"
    m = re.match(r"^([A-Z]\.)\s+([a-z][a-zA-Z-]*)$", s)
    if m:
        genus_abbrev, epithet = m.groups()
        genus = GENUS_MAP.get(genus_abbrev)
        if genus:
            return f"{genus} {epithet}"

    return s


def search_gene_ids(gene_name: str, species: str, retmax: int = 10) -> List[str]:
    """
    Search NCBI Gene for gene IDs using gene name + organism.
    """
    query = f'"{gene_name}"[Gene Name]'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)

    return record.get("IdList", [])


def link_gene_to_nuccore(gene_id: str) -> List[str]:
    """
    Follow Gene -> Nuccore links.
    """
    with Entrez.elink(dbfrom="gene", db="nuccore", id=gene_id) as handle:
        record = Entrez.read(handle)

    nuccore_ids = []
    for linksetdb in record[0].get("LinkSetDb", []):
        for link in linksetdb.get("Link", []):
            nuccore_ids.append(link["Id"])

    return nuccore_ids


def fetch_nuccore_summaries(nuccore_ids: List[str]) -> List[dict]:
    """
    Fetch accession/version and title for Nuccore records.
    """
    if not nuccore_ids:
        return []

    with Entrez.esummary(db="nuccore", id=",".join(nuccore_ids)) as handle:
        summary = Entrez.read(handle)

    results = []
    for item in summary:
        results.append({
            "accession": item.get("AccessionVersion", ""),
            "title": item.get("Title", ""),
        })
    return results


def direct_nuccore_search(gene_name: str, species: str, retmax: int = 10) -> List[dict]:
    """
    Fallback direct search in nuccore if gene->nuccore linking fails.
    """
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="nuccore", term=query, retmax=retmax) as handle:
        rec = Entrez.read(handle)

    ids = rec.get("IdList", [])
    if not ids:
        return []

    return fetch_nuccore_summaries(ids)


def pick_best_accession(records: List[dict], gene_name: str) -> str:
    """
    Pick the best accession from candidate nuccore records.
    Preference:
      1. title containing the exact gene name
      2. titles mentioning mRNA/cDNA/transcript
      3. otherwise first record
    """
    if not records:
        return ""

    gene_name_lower = gene_name.lower()

    exact_gene = [
        r for r in records
        if gene_name_lower in r.get("title", "").lower()
    ]
    if exact_gene:
        transcript_like = [
            r for r in exact_gene
            if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
        ]
        return (transcript_like[0] if transcript_like else exact_gene[0]).get("accession", "")

    transcript_like = [
        r for r in records
        if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
    ]
    if transcript_like:
        return transcript_like[0].get("accession", "")

    return records[0].get("accession", "")


def find_accession_for_gene(gene_name: str, species: str, pause: float = 0.34) -> str:
    """
    Main lookup logic:
      1. Search Gene
      2. Link Gene -> Nuccore
      3. Pick best accession
      4. Fallback to direct nuccore search
    """
    normalized_species = normalize_species_name(species)

    # First try Gene -> Nuccore
    gene_ids = search_gene_ids(gene_name, normalized_species)
    time.sleep(pause)

    all_records = []
    for gid in gene_ids:
        nuccore_ids = link_gene_to_nuccore(gid)
        time.sleep(pause)

        if nuccore_ids:
            summaries = fetch_nuccore_summaries(nuccore_ids)
            all_records.extend(summaries)
            time.sleep(pause)

    accession = pick_best_accession(all_records, gene_name)
    if accession:
        return accession

    # Fallback: direct nuccore search
    direct_records = direct_nuccore_search(gene_name, normalized_species)
    time.sleep(pause)

    return pick_best_accession(direct_records, gene_name)


def process_table(
    input_file: str,
    output_file: str,
    delimiter: str,
    has_header: bool
) -> None:
    """
    Read 2-column table and write 3-column output:
      gene_name, species_name, accession
    """
    with open(input_file, "r", newline="", encoding="utf-8") as infile, \
         open(output_file, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.reader(infile, delimiter=delimiter)
        writer = csv.writer(outfile, delimiter=delimiter)

        first_row = True
        for row_num, row in enumerate(reader, start=1):
            if not row:
                writer.writerow(row + [""])
                continue

            if len(row) < 2:
                print(f"Warning: row {row_num} has fewer than 2 columns; leaving accession blank.", file=sys.stderr)
                writer.writerow(row + [""])
                continue

            gene_name = row[0].strip()
            species_name = row[1].strip()

            if first_row and has_header:
                writer.writerow(row + ["accession"])
                first_row = False
                continue

            first_row = False

            accession = ""
            try:
                if gene_name and species_name:
                    accession = find_accession_for_gene(gene_name, species_name)
            except Exception as e:
                print(
                    f"Warning: lookup failed for row {row_num} "
                    f"(gene='{gene_name}', species='{species_name}'): {e}",
                    file=sys.stderr
                )

            if accession:
                writer.writerow(row + [accession])
                print(f"Processed row {row_num}: gene: '{gene_name}', species: '{species_name}', accession found: '{accession}'")
            else:
                print(f"Processed row {row_num}: gene: '{gene_name}', species: '{species_name}', accession not found")
        print(f"Output file: {output_file}")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Read a two-column table of gene names and species names, "
            "search NCBI Nucleotide, and write a new table with a third "
            "column containing the accession number."
        )
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input 2-column table file"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file with appended accession column"
    )
    parser.add_argument(
        "--email",
        default="my_email@example.com",
        help="Email address for NCBI Entrez"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional NCBI API key"
    )
    parser.add_argument(
        "--delimiter",
        default="\t",
        help=r"Input/output delimiter. Default is tab. Use ',' for CSV."
    )
    parser.add_argument(
        "--header",
        action="store_true",
        help="Indicate that the input file has a header row"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    Entrez.email = args.email
    if args.api_key:
        Entrez.api_key = args.api_key

    process_table(
        input_file=args.input,
        output_file=args.output,
        delimiter=args.delimiter,
        has_header=args.header
    )


if __name__ == "__main__":
    main()