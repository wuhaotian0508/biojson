"""
Chunker 字段分组与常量定义。
"""

# ============================================================
# 版本
# ============================================================
CHUNKER_VERSION = "v2.2026-04"

# ============================================================
# 空值判定
# ============================================================
EMPTY_VALUES = (None, "NA", "", "null", "Not established", "not established",
                "Unknown", "unknown")

# ============================================================
# Plant_Genes 字段分组
# ============================================================
PLANT_FIELD_GROUPS = {
    "identity": [
        "Gene_Name", "Gene_Accession_Number", "Chromosome_Position",
        "Species", "Species_Latin_Name", "Variety",
        "Reference_Genome_Version", "QTL_or_Locus_Name",
    ],
    "overview": [
        "Summary_key_Findings_of_Core_Gene",
        "Summary_Key_Findings_of_Core_Gene",   # 兼容两种拼写
        "Core_Phenotypic_Effect",
        "Research_Topic", "Trait_Category",
    ],
    "mechanism": [
        "Regulatory_Mechanism", "Regulatory_Pathway",
        "Biosynthetic_Pathway", "Upstream_or_Downstream_Regulation",
        "Protein_Family_or_Domain", "Subcellular_Localization",
        "Interacting_Proteins", "Expression_Pattern",
    ],
    "phenotype": [
        "Quantitative_Phenotypic_Alterations",
        "Other_Phenotypic_Effects",
        "Key_Environment_or_Treatment_Factor",
    ],
    "variant_breeding": [
        "Key_Variant_Site", "Key_Variant_Type",
        "Favorable_Allele", "Superior_Haplotype",
        "Breeding_Application_Value",
        "Field_Trials", "Genetic_Population",
        "Genomic_Selection_Application",
    ],
    "methods": [
        "Experimental_Methods", "Experimental_Materials",
        "Core_Validation_Method", "Gene_Discovery_or_Cloning_Method",
    ],
}

# ============================================================
# Pathway_Genes 字段分组
# ============================================================
PATHWAY_FIELD_GROUPS = {
    "identity": [
        "Gene_Name", "Enzyme_Name", "EC_Number",
        "Protein_Family_or_Domain", "Gene_Accession_Number",
    ],
    "reaction": [
        "Primary_Substrate", "Primary_Product",
        "Catalyzed_Reaction_Description",
        "Biosynthetic_Pathway",
        "Pathway_Branch_or_Subpathway",
        "Metabolic_Step_Position",
        "End_Product_Connection_Type",
        "Rate_Limiting_or_Key_Control_Step",
    ],
    "terminal": [
        "Terminal_Metabolite", "Terminal_Metabolite_Class",
        "Terminal_Metabolite_Function",
        "Terminal_Metabolite_Accumulation_Site",
    ],
    "species_host": [
        "Source_Species", "Source_Species_Latin_Name",
        "Applied_Species", "Applied_Species_Latin_Name",
        "Source_Species_Variety", "Applied_Species_Variety",
    ],
    "expression": [
        "Expression_Pattern_of_Source_Species",
        "Expression_Pattern_of_Applied_Species",
        "Subcellular_Localization", "Applied_Promoters",
    ],
    "function": [
        "Core_Phenotypic_Effect",
        "Summary_Key_Findings_of_Core_Gene",
        "Core_Validation_Method",
        "Environment_or_Treatment_Factor",
    ],
    "interactions": ["Interacting_Proteins"],
    "engineering": [
        "Breeding_or_Engineering_Application_Value",
        "Potential_Tradeoffs",
        "Other_Important_Info",
    ],
}

# ============================================================
# Regulation_Genes 独占字段
# ============================================================
REGULATION_CORE_FIELDS = [
    "Regulator_Type", "Regulation_Mode",
    "Primary_Regulatory_Targets", "Regulatory_Effect_on_Target_Genes",
    "Upstream_Signals_or_Inputs", "Metabolic_Process_Controlled",
    "Decisive_Influence_on_Target_Product",
    "Feedback_or_Feedforward_Regulation",
    "Protein_Complex_Involvement",
    "Epigenetic_Regulation",
]

# ============================================================
# Chunk 长度控制
# ============================================================
CHUNK_MIN_BODY_LEN = 80
CHUNK_MAX_BODY_LEN = 1500
CHUNK_TARGET_BODY_LEN = (300, 600)
