import csv


# 这个脚本的作用：
# 1. 读取 accession.txt 中的基因名和物种信息；
# 2. 根据物种选择对应的 SOP 模板；
# 3. 读取 crispr_target_recommented.txt 中的推荐靶点；
# 4. 将 accession、target number、sequence、PAM 等内容替换到模板占位符中；
# 5. 为每个基因生成一个最终的实验方案文本文件。
#
# 注意：
# - 这个脚本当前没有封装成函数，而是“顶层顺序执行脚本”；
# - 也就是说运行 `python experiment_design.py` 时，会从第 4 行开始逐行执行。


for line in open('accession.txt', mode='r', encoding='utf-8'):
    # 逐行读取 accession.txt。
    # 这里假设每一行至少包含：基因名、物种名、accession。
    # 当前只显式用到了前两列：
    # - 第 1 列：gene_name
    # - 第 2 列：organism
    gene_name = line.strip().split('\t')[0]
    organism = line.strip().split('\t')[1].split(' ')[0]

    # 根据物种所属属名选择专用 SOP 模板。
    # 如果不在已知列表中，则退回到通用植物模板 Universal_Plant。
    if organism not in ['Oryza', 'Zea', 'Nicotiana', 'Triticum', 'Glycine', 'Arabidopsis']:
        organism = 'Universal_Plant'

    # 读取对应物种的 SOP 基础模板。
    # 模板里预先放了多个占位符，例如：
    # _gene_accession_、_target_number_、_sequence_、_PAM_、_sequence_rc_
    with open(f'SOP_{organism}_CRISPR_SpCas9_base.txt', mode='r', encoding='utf-8') as f_base:
        text = f_base.read()

    # 读取上一步 CRISPR 靶点推荐结果表。
    # 每一行对应一个 accession/序列的推荐靶点信息。
    with open(f'crispr_target_recommented.txt', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # 从 CRISPR 推荐结果中提取需要写入模板的字段。
            accession = row['Seq_name']
            target_number = row['Target_number']
            squence = row['Sequence']
            pam = row['PAM']
            sequence_rc = row['Sequence_RC']

            # 用真实值替换 SOP 模板中的占位符。
            text = text.replace('_gene_accession_', accession)
            text = text.replace('_target_number_', target_number)
            text = text.replace('_sequence_', squence)
            text = text.replace('_PAM_', pam)
            text = text.replace('_sequence_rc_', sequence_rc)

            # 将替换后的实验方案写出为单独文件。
            # 文件名格式：SOP_{organism}_CRISPR_SpCas9_{gene_name}.txt
            with open(f'SOP_{organism}_CRISPR_SpCas9_{gene_name}.txt', mode='w', encoding='utf-8') as f_gene:
                f_gene.write(text)


