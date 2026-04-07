# analysis_pipline_v2 说明文档

本文档说明 `/data/haotianwu/biojson/rag/analysis_pipline_v2` 目录下各个 Python 脚本的：

- 输入是什么
- 输出是什么
- 如何实现的
- 脚本内部函数调用顺序
- 整体 pipeline 运行顺序

---

## 一、这个 pipeline 需要 LLM 吗？

**不需要。**

这个目录中的流程不是基于大模型（LLM）的，也不会调用 OpenAI、Claude、GPT、embedding 等接口。它主要依赖：

1. **人工提供的基因名和物种名**
2. **NCBI Entrez / efetch 接口**
3. **外部 CRISPR 设计网站**
4. **本地 SOP 模板替换**

也就是说，它是一个：

> **基因名输入 → accession 查询 → 序列下载 → CRISPR 靶点推荐 → SOP 实验方案生成**

的自动化脚本流程，而不是一个自然语言理解或文献抽取流程。

---

## 二、整体运行顺序

根据 `pipline.txt`，整体执行顺序如下：

```bash
python gene2accession.py -i gene_to_edit.txt -o accession.txt
python accession2sequence.py -i accession.txt -o sequence.fas
python crispr_target.py -i sequence.fas -o crispr_target_recommented.txt
python experiment_design.py
```

也就是：

```text
gene_to_edit.txt
    ↓
gene2accession.py
    ↓
accession.txt
    ↓
accession2sequence.py
    ↓
sequence.fas
    ↓
crispr_target.py
    ↓
crispr_target_recommented.txt
    ↓
experiment_design.py + SOP模板
    ↓
最终实验方案 txt 文件
```

---

## 三、各个 Python 文件说明

---

## 1. `gene2accession.py`

### 1.1 它的作用

这个脚本负责把用户提供的：

- 基因名（gene name）
- 物种名（species name）

映射成 NCBI 中对应的 **accession**。

它是整个流程的第一步。

---

### 1.2 输入是什么

输入文件通常是：

- `gene_to_edit.txt`

格式是一个两列表格，默认使用 **tab 分隔**：

```text
GmMYB4	Glycine max
GmIFS2	Glycine max
```

含义是：

- 第 1 列：基因名
- 第 2 列：物种名

命令行输入参数：

```bash
python gene2accession.py -i gene_to_edit.txt -o accession.txt
```

其中：

- `-i / --input`：输入文件
- `-o / --output`：输出文件
- `--email`：NCBI Entrez 使用邮箱
- `--api-key`：可选的 NCBI API key
- `--delimiter`：输入输出分隔符
- `--header`：输入文件是否带表头

---

### 1.3 输出是什么

输出通常是：

- `accession.txt`

格式是在原始两列后面追加第 3 列 accession，例如：

```text
GmMYB4	Glycine max	NM_001...
GmIFS2	Glycine max	XM_123...
```

即：

- 第 1 列：gene_name
- 第 2 列：species_name
- 第 3 列：accession

---

### 1.4 它是如何实现的

核心思路是：

1. 读取每一行基因名和物种名
2. 规范化物种名格式
3. 查询 NCBI Gene 数据库
4. 从 Gene 结果跳转到 Nuccore 数据库
5. 拿到候选核酸记录摘要
6. 通过启发式规则选择最合适的 accession
7. 如果主路径失败，则直接搜索 Nuccore 兜底

#### 具体函数说明

##### `normalize_species_name(species)`

作用：

- 规范化物种名
- 比如把 `G. max` 转成 `Glycine max`

目的：

- 让 NCBI 更容易识别物种名，降低检索失败率

---

##### `search_gene_ids(gene_name, species, retmax=10)`

作用：

- 去 NCBI Gene 里检索 gene ID

检索条件：

- gene name
- organism（如果提供）

输出：

- Gene ID 列表

---

##### `link_gene_to_nuccore(gene_id)`

作用：

- 从 Gene ID 跳转到 Nuccore 记录

输出：

- Nuccore ID 列表

意义：

- Gene 是“基因实体库”
- Nuccore 才是后续真正要取 accession / sequence 的核酸序列库

---

##### `fetch_nuccore_summaries(nuccore_ids)`

作用：

- 批量获取 Nuccore 记录摘要

输出内容主要有：

- accession
- title

用途：

- title 用于判断哪个候选记录更像目标转录本

---

##### `pick_best_accession(records, gene_name)`

作用：

- 从多个候选记录中选择一个最合适的 accession

优先级规则：

1. title 包含 gene_name
2. title 中带有 `mRNA` / `cDNA` / `transcript`
3. 如果都不满足，选第一条

这是一个 **启发式规则**，不是严格生物学判断。

---

##### `direct_nuccore_search(gene_name, species)`

作用：

- 当前面“Gene → Nuccore”路径失败时，直接在 Nuccore 中搜索

用途：

- 作为兜底策略，避免 Gene 数据库关联不完整时完全查不到结果

---

##### `find_accession_for_gene(gene_name, species, pause=0.34)`

作用：

- 这是总控函数，负责串起整个 accession 查询逻辑

流程：

1. 标准化物种名
2. 查 Gene ID
3. 从 Gene 跳到 Nuccore
4. 取摘要
5. 选 accession
6. 如果失败则 direct search 兜底

---

##### `process_table(input_file, output_file, delimiter, has_header)`

作用：

- 批量读取整个输入表
- 对每一行调用 accession 查询逻辑
- 把结果写回输出表

这是脚本级别的真正批处理函数。

---

##### `parse_args()`

作用：

- 解析命令行参数

---

##### `main()`

作用：

- 程序入口
- 调用 `parse_args()`
- 配置 `Entrez.email`
- 调用 `process_table()`

---

### 1.5 这个脚本内部运行顺序

```text
main
 ├─ parse_args
 └─ process_table
     └─ find_accession_for_gene
         ├─ normalize_species_name
         ├─ search_gene_ids
         ├─ link_gene_to_nuccore
         ├─ fetch_nuccore_summaries
         ├─ pick_best_accession
         └─ direct_nuccore_search (如果主路径失败)
             └─ fetch_nuccore_summaries
```

---

## 2. `accession2sequence.py`

### 2.1 它的作用

这个脚本负责把 accession 列表转换为 FASTA 序列文件。

它是整个流程的第二步。

---

### 2.2 输入是什么

输入通常是：

- `accession.txt`

也就是上一步产生的三列表格，默认读取第 3 列 accession。

命令：

```bash
python accession2sequence.py -i accession.txt -o sequence.fas
```

命令行参数包括：

- `-i / --input`：输入表格
- `-o / --output`：输出 FASTA 文件
- `--sep`：分隔符（默认 tab）
- `--email`：NCBI 请求邮箱
- `--tool`：工具名
- `--delay`：每次请求之间的等待时间

---

### 2.3 输出是什么

输出通常是：

- `sequence.fas`

内容示例：

```fasta
>NM_001...
ATGCGT...
>XM_123...
ATGGGA...
```

也就是所有 accession 对应序列拼接在同一个 FASTA 文件里。

---

### 2.4 它是如何实现的

核心思路：

1. 读取输入表格中的 accession 列
2. 调用 NCBI efetch 接口下载序列
3. 把 FASTA header 简化为 accession
4. 依次写入输出 FASTA 文件

#### 具体函数说明

##### `read_accessions(file_path, col_index=2, sep=None)`

作用：

- 从输入表格中读取 accession 列

默认：

- 第 3 列（索引 2）

输出：

- accession 字符串列表

---

##### `fetch_fasta(accession, email, tool)`

作用：

- 调用 NCBI efetch 下载某个 accession 对应的 FASTA 文本

它会：

- 发 HTTP GET 请求
- 检查返回状态是否正常
- 检查返回内容是否真的是 FASTA

---

##### `simplify_header(fasta_text, accession)`

作用：

- 把 FASTA 第一行简化为 `>accession`

好处：

- 后续处理更清晰
- 名称和 accession 保持一致

---

##### `main()`

作用：

- 主入口
- 解析参数
- 调用 `read_accessions()`
- 对每个 accession 调用 `fetch_fasta()`
- 调用 `simplify_header()`
- 写入输出 FASTA 文件

---

### 2.5 这个脚本内部运行顺序

```text
main
 ├─ read_accessions
 ├─ fetch_fasta   (对每个 accession 调用)
 └─ simplify_header (对每个 accession 调用)
```

---

## 3. `crispr_target.py`

### 3.1 它的作用

这个脚本负责：

1. 读取 FASTA 序列
2. 把序列提交到外部 CRISPR 设计网站
3. 解析网页中的候选靶点
4. 选择第一个 exon 区域靶点
5. 输出为表格

它是整个流程的第三步。

---

### 3.2 输入是什么

输入通常是：

- `sequence.fas`

命令：

```bash
python crispr_target.py -i sequence.fas -o crispr_target_recommented.txt
```

参数包括：

- `-i / --input`：输入 FASTA 文件
- `-o / --output`：输出 TSV 文件
- `--sep`：输出分隔符

---

### 3.3 输出是什么

输出通常是：

- `crispr_target_recommented.txt`

包含字段：

- `Seq_name`
- `On_score`
- `Target_number`
- `Sequence`
- `PAM`
- `Region`
- `%GC`
- `Sequence_RC`

示意：

```text
Seq_name	On_score	Target_number	Sequence	PAM	Region	%GC	Sequence_RC
NM_001...	0.72	1	ACGT...	NGG	exon	50	...
```

---

### 3.4 它是如何实现的

核心思路：

1. 逐条解析 FASTA
2. 校验序列是否合法
3. 构造网站请求表单
4. 提交到 CRISPR 网站
5. 解析返回 HTML
6. 提取候选靶点表格
7. 选第一个 exon 候选
8. 写成输出 TSV

#### 具体函数说明

##### `build_parser()`

作用：

- 构建命令行参数解析器

---

##### `parse_fasta(path)`

作用：

- 逐条读取 FASTA 文件
- 返回 `(seq_name, sequence)`

它还会：

- 检查文件是否存在
- 检查 FASTA 格式是否正确
- 对序列调用 `validate_sequence()`

---

##### `validate_sequence(sequence, name)`

作用：

- 检查序列是否为空
- 检查是否只包含 `A/C/G/T/N`
- 去除空格

意义：

- 避免非法序列导致后续提交失败

---

##### `build_payload(sequence)`

作用：

- 构造提交给外部 CRISPR 网站的 POST 表单

其中包括：

- PAM
- oligo
- template
- spacer_length
- sequence

这里绝大部分参数是写死的，只有 `sequence` 是动态变化的。

---

##### `fetch_result_page(sequence)`

作用：

- 调用 `build_payload()`
- 发 POST 请求到 CRISPR 网站
- 返回网页 HTML

---

##### `extract_rows(html_text)`

作用：

- 解析返回的 HTML
- 用 XPath 抓取候选靶点所在表格行
- 提取字段：
  - `Target_number`
  - `On_score`
  - `Sequence`
  - `PAM`
  - `Region`
  - `%GC`
- 同时生成 `Sequence_RC`

这是这个脚本的核心解析函数。

---

##### `reverse_complement(seq)`

作用：

- 生成候选序列的反向互补序列

---

##### `find_first_exon_row(rows)`

作用：

- 在候选结果中选取第一个 `Region == exon` 的记录

注意：

- 它没有做复杂排序
- 只是简单地选第一个 exon 命中的行

---

##### `build_output_row(seq_name, row)`

作用：

- 把选中的候选靶点转换成统一输出格式

---

##### `write_table(path, rows, sep)`

作用：

- 把结果列表写入 TSV / 表格文件

---

##### `main()`

作用：

- 主入口
- 调用 `parse_fasta()` 逐条取序列
- 对每条序列调用 `fetch_result_page()`
- 调用 `extract_rows()` 解析候选
- 调用 `find_first_exon_row()` 取推荐项
- 调用 `build_output_row()` 整理结果
- 调用 `write_table()` 写出结果

---

### 3.5 这个脚本内部运行顺序

```text
main
 ├─ build_parser
 ├─ parse_fasta
 │   └─ validate_sequence
 ├─ fetch_result_page
 │   └─ build_payload
 ├─ extract_rows
 │   └─ reverse_complement
 ├─ find_first_exon_row
 ├─ build_output_row
 └─ write_table
```

---

## 4. `experiment_design.py`

### 4.1 它的作用

这个脚本负责把：

- 基因 / 物种信息
- CRISPR 推荐靶点信息
- SOP 模板文件

拼装成最终实验方案文本。

它是整个流程的最后一步。

---

### 4.2 输入是什么

这个脚本依赖以下输入：

1. `accession.txt`
2. `crispr_target_recommented.txt`
3. 各物种的 SOP 模板文件，例如：
   - `SOP_Glycine_CRISPR_SpCas9_base.txt`
   - `SOP_Arabidopsis_CRISPR_SpCas9_base.txt`
   - `SOP_Universal_Plant_CRISPR_SpCas9_base.txt`

它没有命令行参数，直接运行：

```bash
python experiment_design.py
```

---

### 4.3 输出是什么

输出是每个基因对应的 SOP 文本文件，例如：

- `SOP_Glycine_CRISPR_SpCas9_GmMYB4.txt`
- `SOP_Glycine_CRISPR_SpCas9_GmIFS2.txt`

也就是最终可读的实验设计文本。

---

### 4.4 它是如何实现的

这个脚本没有函数封装，而是顶层顺序执行。

核心逻辑是：

1. 逐行读取 `accession.txt`
2. 取出每一行的 `gene_name` 和 `organism`
3. 根据物种属名选择一个 SOP 模板
4. 读取 `crispr_target_recommented.txt`
5. 提取推荐靶点字段：
   - `Seq_name`
   - `Target_number`
   - `Sequence`
   - `PAM`
   - `Sequence_RC`
6. 把这些真实值替换进模板中的占位符：
   - `_gene_accession_`
   - `_target_number_`
   - `_sequence_`
   - `_PAM_`
   - `_sequence_rc_`
7. 把替换后的完整文本写成新的 SOP 文件

---

### 4.5 需要特别注意的问题

这个脚本当前实现里有一个逻辑特点：

- 它会对 `accession.txt` 的每一行都读取一次整个 `crispr_target_recommented.txt`
- 然后不断进行 `text.replace(...)`

这意味着它更像是一个“简单批量模板替换脚本”，
而不是一个严格按 accession 一一配对的精确映射脚本。

换句话说：

> 它的实现比较直接，适合快速生成 SOP，但如果后续要做更严谨的一一对应，建议再重构。

---

### 4.6 这个脚本内部运行顺序

因为它没有函数，执行顺序就是代码从上到下：

```text
读取 accession.txt 每一行
  ├─ 提取 gene_name / organism
  ├─ 选择 SOP 模板
  ├─ 读取模板文本
  ├─ 读取 crispr_target_recommented.txt
  ├─ 逐行取 target 信息
  ├─ 替换模板占位符
  └─ 输出最终 SOP 文件
```

---

## 四、每个文件的输入 / 输出 / 实现总表

| 文件 | 输入 | 输出 | 如何实现 |
|---|---|---|---|
| `gene2accession.py` | `gene_to_edit.txt`（gene + species） | `accession.txt` | 调 NCBI Gene / Nuccore，查 accession，并追加为第 3 列 |
| `accession2sequence.py` | `accession.txt` | `sequence.fas` | 读取 accession，调 NCBI efetch 下载 FASTA |
| `crispr_target.py` | `sequence.fas` | `crispr_target_recommented.txt` | 提交序列到 CRISPR 网站，解析 HTML，选 exon 靶点 |
| `experiment_design.py` | `accession.txt` + `crispr_target_recommented.txt` + SOP 模板 | `SOP_*.txt` | 读取模板并替换占位符，生成实验方案 |

---

## 五、总结

这个目录下的流程，本质上是一个 **CRISPR 实验设计自动化 pipeline**：

1. 用户先手动给出目标基因名和物种名
2. 程序到 NCBI 查 accession
3. 再下载对应核酸序列
4. 再调用外部 CRISPR 网站获取推荐靶点
5. 最后把结果填进 SOP 模板，生成实验方案文本

它的特点是：

- **不依赖 LLM**
- **不从论文里自动抽取基因名**
- **主要依赖外部数据库和网站接口**
- **最后一步是模板拼装，不是模型生成**

如果你后续愿意，我还可以继续帮你补一个：

1. **更适合汇报的流程图版 Markdown**，或者
2. **逐行解释 `experiment_design.py` 当前潜在 bug / 可重构点**。