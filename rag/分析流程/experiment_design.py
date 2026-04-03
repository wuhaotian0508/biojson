import csv

with open('CRISPR_SpCas9_Gene_Editing_base.txt', mode='r', encoding='utf-8') as f_base:
    text = f_base.read()

with open('crispr_target_reccomented.txt', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        accession = row['Seq_name']
        target_number = row['Target_number']
        squence = row['Sequence']
        pam = row['PAM']
        sequence_rc = row['Sequence_RC']
        text = text.replace('_gene_accession_', accession)
        text = text.replace('_target_number_', target_number)
        text = text.replace('_sequence_', squence)
        text = text.replace('_PAM_', pam)
        text = text.replace('_sequence_rc_', sequence_rc)

        with open(f'CRISPR_SpCas9_Gene_Editing_{accession}.txt', mode='w', encoding='utf-8') as f_gene:
            f_gene.write(text)