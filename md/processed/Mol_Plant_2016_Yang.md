# A Maize Gene Regulatory Network for Phenolic Metabolism

Fan Yang1,2, Wei Li2,3, Nan Jiang1,2, Haidong $\mathsf { Y u } ^ { 1 , 2 }$ , Kengo Morohashi1,2, Wilberforce Zachary Ouma1,2,4, Daniel E. Morales-Mantilla2,3,5, Fabio Andres Gomez-Cano1,2, Eric Mukundi1,2, Luis Daniel Prada-Salcedo2,3, Roberto Alers Velazquez2,3,5, Jasmin Valentin2,3,5, Maria Katherine Mejı´a-Guerra1,2, John Gray6, Andrea I. Doseff2,3 and Erich Grotewold1,2, * 

1 Center for Applied Sciences (CAPS) 

2 Department of Molecular Genetics 

3 Department of Physiology and Cell Biology, Heart and Lung Research Institute 

4 Molecular, Cellular, and Developmental Biology (MCDB) Graduate Program 

5 Success in Graduate Education (SiGuE) Program 

The Ohio State University, Columbus, OH 43210, USA 

6 Department of Biological Sciences, University of Toledo, Toledo, OH 43560, USA 

*Correspondence: Erich Grotewold (grotewold.1@osu.edu) 

http://dx.doi.org/10.1016/j.molp.2016.10.020 

# ABSTRACT

The translation of the genotype into phenotype, represented for example by the expression of genes encoding enzymes required for the biosynthesis of phytochemicals that are important for interaction of plants with the environment, is largely carried out by transcription factors (TFs) that recognize specific cis-regulatory elements in the genes that they control. TFs and their target genes are organized in gene regulatory networks (GRNs), and thus uncovering GRN architecture presents an important biological challenge necessary to explain gene regulation. Linking TFs to the genes they control, central to understanding GRNs, can be carried out using gene- or TF-centered approaches. In this study, we employed a gene-centered approach utilizing the yeast one-hybrid assay to generate a network of protein–DNA interactions that participate in the transcriptional control of genes involved in the biosynthesis of maize phenolic compounds including general phenylpropanoids, lignins, and flavonoids. We identified 1100 protein–DNA interactions involving 54 phenolic gene promoters and 568 TFs. A set of 11 TFs recognized 10 or more promoters, suggesting a role in coordinating pathway gene expression. The integration of the gene-centered network with information derived from TF-centered approaches provides a foundation for a phenolics GRN characterized by interlaced feed-forward loops that link developmental regulators with biosynthetic genes. 

Key words: phenylpropanoid, flavonoid, yeast one-hybrid, chromatin immunoprecipitation 

Yang F., Li W., Jiang N., Yu H., Morohashi K., Ouma W.Z., Morales-Mantilla D.E., Gomez-Cano F.A., Mukundi E., Prada-Salcedo L.D., Velazquez R.A., Valentin J., Mejı´a-Guerra M.K., Gray J., Doseff A.I., and Grotewold E. (2017). A Maize Gene Regulatory Network for Phenolic Metabolism. Mol. Plant. 10, 498–515. 

# INTRODUCTION

The interpretation of the genotype into the biological processes that ultimately establish an organism is largely carried out by transcription factors (TFs), a large group of sequence-specific DNA-binding proteins. Across the eukaryotes, TFs represent $5 \% - 1 0 \%$ of all genes (Chandler, 2003; Mitsuda and Ohme-Takagi, 2009; Yilmaz et al., 2009). TFs often control the expression of genes encoding other TFs, resulting in elaborate regulatory networks that are ultimately responsible for the spatial and temporal expression of all genes in an organism. Gene 

regulatory grids (GRGs) provide static representations of gene regulatory networks (GRNs), portraying all possible connections between TFs and potential target genes. Thus, GRNs afford a spatiotemporal manifestation of a set of the GRGs (Mejia-Guerra et al., 2012). GRGs and GRNs are often represented by directed graphs in which the nodes denote the genes and proteins encoded by them, and the edges symbolize the TF–target gene 

interactions (Barabasi and Oltvai, 2004). Therefore, a major thrust in gene regulation is to identify TF target genes, which involves determining the edges that characterize the protein–DNA interaction space of GRGs and GRNs. The identification of protein–DNA interactions (PDIs) is carried out by TF- or genecentered approaches (or combinations thereof). TF-centered approaches are useful when the TF is known, but not its targets, and include chromatin immunoprecipitation (ChIP)-based methods, such as microarray hybridization (ChIP-chip) and highthroughput sequencing (ChIP-seq). In contrast, gene-centered approaches are employed to determine which TFs control one or a set of genes, and yeast one-hybrid (Y1H) assays provide one of the most common methods (Reece-Hoyes et al., 2011; Reece-Hoyes and Marian Walhout, 2012). 

Plants accumulate thousands of phenolic compounds, many of them synthesized through the phenylpropanoid pathway, accounting for up to $30 \%$ of all the fixed carbon. One main product of the phenylpropanoid pathway is lignin, essential for structural support and integrity of the vascular system, formed by the polymerization of the monolignols $p$ -coumaryl alcohol, coniferyl alcohol, or sinapyl alcohol (Figure 1). Maize is the most widely grown cereal crop in the world, with more than one billion metric tonnes produced in 2013. In addition to the grain, maize stover provides a source of biomass for liquid fuel and power production (Trivedi et al., 2015), and is also extensively used as a major forage component (Khan et al., 2015). Lignin and $p$ -hydroxycinnamic acids (e.g., ferulic acid) are considered as major culprits for the recalcitrance of lignocellulosic biomass to hydrolysis (Me´ chin et al., 2000; de Oliveira et al., 2015). 

Enzymes involved in phenylpropanoid and lignin biosynthesis have been extensively characterized in a number of plants, providing multiple opportunities for the metabolic engineering of the pathway to alter phenolic composition and content (reviewed by Vanholme et al., 2012; Wang et al., 2015). Significant progress has also been made in Arabidopsis, through the identification of key TFs that regulate secondary cell wall formation. These TFs include members of the NAC (NAM, ATAF, and CUC) and R2R3-MYB (myeloblastosis) families, which in turn control the expression of other TFs that directly activate or repress pathway genes (reviewed by Gray et al., 2012; Zhong and Ye, 2015). Transcriptional regulation of lignin biosynthesis is under the control of a transcriptional network that activates the entire secondary wall biosynthetic program. In Arabidopsis, 10 NACs (AtVND 1–7 and AtNST 1–3) provide the first regulatory tier for the control of the lignification of vessel cells and interfascicular fibers, respectively (Kubo et al., 2005; Mitsuda et al., 2005, 2007; Zhong et al., 2006, 2007b; Mitsuda and Ohme-Takagi, 2008; Yamaguchi et al., 2010; Zhou et al., 2014). The second-tier R2R3-MYB master switches include AtMYB46 and AtMYB83, which were identified as direct downstream targets of the NST regulators, preferentially expressed in the xylem and interfascicular fibers (Zhong et al., 2007a; Ko et al., 2009; McCarthy et al., 2009). Three other regulators, AtMYB58, AtMYB63, and AtMYB85, were identified as direct targets of AtMYB46/MYB83, and function as lignin biosynthesis gene transcriptional activators (Zhong et al., 2008; Zhou et al., 2009). A genome-wide gene-centered screen (using the Y1H system) with secondary cell wall gene promoters and an Arabidopsis ORFeome library containing more than 1600 full-length TFs 

resulted in the identification of E2Fc as an upstream regulator of AtVND7 (Taylor-Teeples et al., 2015), linking cell-cycle regulators with metabolic control. 

Rice and maize NAC and R2R3-MYB regulators capable of complementing Arabidopsis mutants deficient in secondary wall thickening have been identified (Zhong et al., 2011), but the regulation of the phenolic pathway continues to be significantly less understood in maize and other grasses (Gray et al., 2012; Handakumbura and Hazen, 2012). A few TFs that participate in the regulation of specific pathway genes have been characterized from maize, including the ZmMYB40/ZmMYB95 paralogs (Dias et al., 2003; Heine et al., 2007); ZmMYB31/ZmMYB42/ZmMYB11, which belong to subgroup 4 of the R2R3-MYB family, and which function as pathway repressors (Sonbol et al., 2009; Fornale´ et al., 2010; Ve´ lez-Bermu´ dez et al., 2015; Agarwal et al., 2016); and ZmMYB111 (GRMZM2G104551; ZmMYB152 in grassius.org) and ZmMYB148 (GRMZM2G097636; ZmMYB5 in grassius.org), which were recently proposed to control the expression of maize PAL genes (Zhang et al., 2016). 

Products from the phenylpropanoid pathway also serve as precursors for the synthesis of other important compounds that include flavonoids, coumarins, and lignans (Boerjan et al., 2003; Vogt, 2010). Genes involved in maize flavonoid biosynthesis have been extensively characterized, thanks to the pigmentation phenotypes of many of the respective gene mutations (Grotewold, 2006). The R2R3-MYB and bHLH (basic helix-loop-helix) regulators of the maize flavonoid pathway have been known for many years (Petroni and Tonelli, 2011; Falcone Ferreyra et al., 2012). However, flavonoid regulators known in other species remain to be identified in maize. 

Here, we describe a comprehensive gene-centered approach to map the GRG associated with phenolic biosynthesis in maize. We used the promoter sequences of 54 biosynthetic genes in a Y1H assay to identify, from a collection of 1901 maize TFs, the regulatory events potentially involved in the control of maize phenolic biosynthesis. The identified grid comprises 568 TFs and 1100 PDIs, and includes a few previously known TF–target gene interactions. To determine the biological significance of the identified interactions, we interrogated an unbiased set by ChIP, which provided unique perspectives on the strengths and limitations of each approach. Results from this gene-centered approach were integrated with published maize ChIP-seq data to generate a framework for a maize phenolic GRG. These results should be useful to direct future studies and efforts geared at manipulating the regulation of the pathway and demonstrate the tremendous utility of the maize TFome as a resource to advance the dissection of GRNs operating in monocots. 

# RESULTS

# Generation of Yeast Strains for Y1H Assays

We selected a total of 54 genes representing key steps in the maize phenolic pathway (Figure 1, shaded gray squares). Because we wanted to specifically identify TFs that bind to regulatory regions upstream of transcript initiation sites, whenever possible we parsed available maize CAGE (cap analysis of gene expression) data to define transcription start 


General Phenylpropanoids


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/56bc687fe2a1663af89f666161273dae3a9c7eac3003282ee3f1342e31f0930c.jpg)



Figure 1. Schematic Representation of the Maize Phenolic Biosynthesis Pathway Resulting in the Formation of General Phenylpropanoids, Lignins, and Flavonoids.


The general phenylpropanoid part of the pathway includes enzymes such as: PAL, phenylalanine ammonia lyase; C4H, cinnamate 4-hydroxylase; 4CL, 4-coumarate CoA ligase. The lignin part of the pathway includes enzymes such as: HCT, hydroxycinnamoyl CoA:shikimate hydroxycinnamoyl transferase; C3H, $p$ -coumaroyl shikimate 3-hydroxylase; CSE, caffeoyl shikimate esterase; CCoAOMT, caffeoyl CoA O-methyltransferase; F5H, ferulate 5-hydroxylase; COMT, caffeic acid O-methyltransferase; CCR, cinnamoyl CoA reductase; CAD, cinnamyl alcohol dehydrogenase; ALDH, aldehyde dehydrogenase. The flavonoid part of the pathway includes enzymes such as: CHS, chalcone synthase; CHI, chalcone isomerase; F3H, flavanone 3-hydroxylase; FLS, flavonol synthase; FNS, flavone synthase; $\mathsf { F } 3 ^ { \prime } \mathsf { H }$ , flavonoid ${ \mathfrak { z } } ^ { \prime }$ -hydroxylase; F2H, flavanone 2-hydroxylase; DFR, dihydroflavonol reductase; LDOX/ANS, leucoanthocyanidin dioxygenase; UGT, UDP-glycosyltransferase; GST, glutathione S-transferase; CGT, C-glycosyl transferase; RHM, rhamnose synthase. Enzyme genes for which promoters were used in Y1H assays are indicated in blue, otherwise they are shown in black. Dashed arrows indicate reaction steps that remain uncertain in maize, or for which enzymes have not yet been identified. The squares indicate the number of genes encoding each enzyme. Shaded gray squares correspond to genes for which promoters were used in Y1H assays. 

sites (TSSs) (Mejia-Guerra et al., 2015). When this information was available, we cloned 1 kb upstream of the TSS from the maize B73 inbred line (Supplemental Figure 1). Otherwise, we cloned 1 kb upstream of the translation initiation codon, as annotated in the reference maize genome (Maize B73 RefGen v3). Using 1-kb fragments upstream of the TSS is justified by 

studies in other organisms that show TFs binding with the highest frequency close to the TSS (Lee et al., 2012; Whitfield et al., 2012; Heyndrickx et al., 2014). 

Promoter fragments were cloned into a recombination-ready pDONR vector and recombined with a vector harboring the 

HIS3 selectable marker, resulting in the collection of PromoterpMW#2 plasmids (see Methods). These plasmids were then used for individual integration into the genome of yeast strain YM4271 (Liu et al., 1993), which was verified by PCR, giving rise to 54 different bait strains, each harboring one maize promoter::HIS3 construct (Yang et al., 2016). Because a low level of HIS3 expression is often sufficient for yeast growth in synthetic medium without histidine and uracil (SD-His-Ura), we tested each yeast bait strain for growth in SD-His-Ura medium containing increasing concentrations $\left( 0 { - } 1 0 0 \ m \mathsf { M } \right)$ of 3-amino-1,2,4-triazole (3-AT), establishing an ideal 3-AT concentration for each bait yeast strain (Supplemental Table 1). 

# Gene-Centered Approach to Identify PDIs

We previously generated a large collection of maize TF open reading frames (TFome) cloned in a recombination-ready pENTRY vector (Burdo et al., 2014; Gray et al., 2015). From this collection, 1901 TFs were individually recombined into the pAD-GAL4-GW-C1 plasmid, derived from pAD-GAL4 by insertion of the Gateway cassette (Machemer et al., 2011), and pooled into the AD-TFome plasmid library. To ensure comparable representation of each TF in the plasmid library, we randomly selected 18 TFs and determined copy number by qPCR. While we found some variation in the plasmid representation, ${ \sim } 8 0 \%$ of the plasmids tested differed by less than 10-fold from each other, and, as will become evident later, representation in the library was not correlated to how many times a TF was selected in the screens (Supplemental Figure 2). 

Each yeast bait strain was then transformed with the AD-TFome library to obtain the equivalent of at least 20 000 transformants ( ${ \sim } 1 0$ fold redundancy), which were selected in SD-His-Ura-Leu medium, with the appropriately determined concentration of 3-AT (Supplemental Table 1). After 7–13 days, colonies were picked, re-streaked in SD-His-Ura-Leu $^ { + 3 }$ -AT medium, and subjected to PCR with vector primers flanking the TFs insert in the AD-TF plasmids. PCR products were purified and sequenced, revealing the identity of the TF that enabled growth of the bait strain in the selection medium. 

For validation of the PDIs identified from the Y1H screen, a naive isolate of the bait strain was individually transformed with each of the original AD-TF clones, grown in SD-His-Ura-Leu with varying amounts of 3-AT, and compared with the strain transformed with the empty vector (EV) control. We considered a positive in the Y1H screen as confirmed only when the TF permitted growth at a 3-AT concentration in which the EV-transformed strain failed to grow. Using this approach, 944 PDIs were confirmed (Supplemental Table 2). The validation frequency was very variable, ranging as high as $3 5 \%$ for some promoters, while for PAL6 we could not validate any of the identified candidates (all the TFs that recognize PAL6 [Supplemental Table 2] were identified by direct Y1H assays, see below). It is unclear why such a variation occurred but, as discussed later, it could be in part a consequence of two or more TFs functioning together in a single cell during the initial screening, something that would not be recapitulated during the validation with individual AD-TFs. Unfortunately, the published literature does not usually report the validation frequency for Y1H-identified interactions (Deplancke et al., 2006a; Brady et al., 2011; Li et al., 2014; 

Taylor-Teeples et al., 2015), hence we do not know whether such a variation is a general phenomenon or whether it is specific to the promoters investigated here. 

Given that false negatives are a frequent feature of Y1H assays (Walhout, 2011), we expanded the screen by performing directed Y1H assays. Several criteria were used to select which TFs to be tested on which bait strains. For example, to understand how a small gene family is controlled, we tested every TF identified in a screen on a PAL gene promoter on each one of the nine PAL genes represented in the collection (Figure 1). We also tested TFs corresponding to TFs paralogs identified in our screens. Finally, we selected orthologs of TFs reported in the literature as controlling phenolic genes. In total, we tested 527 TF/yeast bait strain combinations. Of these, 156 were determined to be positive, based on the criteria outlined above (Supplemental Table 3). Thus, by combining the Y1H screens and directed assays, we identified a total of 1100 PDIs involving 54 promoters and 568 different regulators (Supplemental Figure 3 and Supplemental Table 2). We did not find any correlation between the length of the promoters used (Supplemental Figure 1) and the number of TFs that bind to them in Y1H. The names of the TFs used in this study follow previous published recommendations (Gray et al., 2009), and correspond to the names used in GRASSIUS (grassius.org; Yilmaz et al., 2009). 

# Testing In Vivo Protein–DNA Interactions Identified by Y1H

To investigate how often PDIs identified by Y1H had the potential to occur in maize, we adapted the maize protoplast transformation system previously described (Kong et al., 2012; Casas et al., 2016). In brief, we transformed maize protoplasts obtained from B73 3 Mo17 F1 hybrid seedlings with TF translational fusions to the GFP and assayed the interactions with endogenous promoters by ChIP using anti-GFP (aGFP) antibodies, as described previously (Morohashi and Grotewold, 2009; Kong et al., 2012). For an unbiased test of the identified Y1H interactions, we randomly selected (see Methods) 10 PDIs identified from the Y1H screens as recognizing at least two promoters, involving nine promoters and five TFs (Table 1). As illustrated for MYB100, in Y1H assays it interacts with the HCT6 and COMT1 regulatory regions (Figure 2A). ChIP experiments confirmed that these interactions can occur in maize protoplasts, since the enrichment (compared with input DNA) of GFP-MYB100 on the HCT6 and COMT1 regulatory regions (see Supplemental Figure 1 for primer locations) is significantly $( P < 0 . 0 5$ , two-sided t-test) larger than that of free GFP, and neither recognized Copia elements, used here as a negative control (Figure 2B). In some instances, we also used Actin1 (GRMZM2G126010) as a negative control, but Copia provided more conservative results (i.e., larger amplification that resulted in smaller fold enrichments, making the results more stringent). Of the 10 interactions identified by Y1H, eight were detected as positive by ChIP (Supplemental Figure 4), providing a false discovery rate of $20 \%$ or less (Table 1). This false discovery rate is comparable with what was previously determined for highthroughput Caenorhabditis elegans and Arabidopsis Y1H screens (Deplancke et al., 2006a; Brady et al., 2011). 

As part of this analysis, and rarely investigated in similar studies, we also tested by ChIP several TF–target gene combinations that 

<table><tr><td>TF</td><td>Promoter</td><td>Y1H</td><td>ChIP</td></tr><tr><td rowspan="4">MYB100</td><td>HCT6</td><td>+</td><td>+</td></tr><tr><td>COMT1</td><td>+</td><td>+</td></tr><tr><td>4CL3</td><td>-</td><td>+</td></tr><tr><td>FLS1</td><td>-</td><td>-</td></tr><tr><td rowspan="3">JMJ13</td><td>C2</td><td>+</td><td>+</td></tr><tr><td>4CL3</td><td>+</td><td>-</td></tr><tr><td>ALDH1</td><td>-</td><td>-</td></tr><tr><td rowspan="3">MBF1.3</td><td>Bz2</td><td>+</td><td>+</td></tr><tr><td>PAL5</td><td>+</td><td>+</td></tr><tr><td>4CL3</td><td>-</td><td>+</td></tr><tr><td rowspan="3">GBP20</td><td>CCoAOMT2</td><td>+</td><td>+</td></tr><tr><td>C2</td><td>+</td><td>+</td></tr><tr><td>FLS1</td><td>-</td><td>+</td></tr><tr><td rowspan="4">DOF28</td><td>HCT10</td><td>+</td><td>+</td></tr><tr><td>CCR3</td><td>+</td><td>-</td></tr><tr><td>4CL3</td><td>-</td><td>+</td></tr><tr><td>C2</td><td>-</td><td>+</td></tr></table>


Table 1. Comparison of ChIP- and Y1H-Identified PDIs. ‘‘+’’ indicates a positive interaction and ‘‘ ’’ indicates one that could be validated by Y1H and/or ChIP–PCR (ChIP).


did not display a positive interaction by Y1H. For example, we did not identify 4CL3 and FLS1 as MYB100 candidate targets in our Y1H screens, or by testing direct Y1H interactions (Figure 2A). However, ChIP revealed the ability of MYB100 to be tethered to the 4CL3 promoter (but not to FLS1) in maize protoplasts (Figure 2B). This discrepancy between the Y1H and ChIP analyses may indicate that the TFs bind the promoters beyond the 1 kb used in the Y1H experiments, that they are indirectly recruited, through, for example, another TF, or merely a Y1H type II error. Overall, five out of seven combinations that were not detected by Y1H showed interaction by ChIP (Table 1, Supplemental Figure 4). Taken together, these results demonstrate good concordance between Y1H and ChIP, and highlight the complementary value of these two approaches for discovering novel edges in GRGs. 

We identified 11 TFs that recognize 10 or more phenolic gene promoters (Figure 3A). These include three LBDs (LBD35, LBD24, and LBD20), one member of the DOF (DNA-binding One Zinc Finger) family (DOF28), one CPP (Cysteine-rich Polycomb-like Proteins) family member (CPP8), one member of the NLP (NIN-Like Protein) family (NLP14), one member of the bZIP (basic Leucine Zipper motif) family (bZIP13), one member of C3H Zn-finger family (C3H42), one member of the MBF1 (Multiprotein Bridging Factor1) family (MBF1.3), and two R2R3-MYBs (MYB65 and MYB19). 

MYB65 is the ortholog of Arabidopsis AtMYB58 and AtMYB63. MYB65 recognized a total of 13 maize gene regulatory sequences (Figure 3A), including those of seven PAL genes (PAL1, PAL3, PAL4, PAL5, PAL6, PAL8, and PAL9). We tested these 13 interactions by ChIP in maize protoplasts, and in 

10 of the 13 instances the enrichment over input was significantly larger with MYB65-GFP than with GFP alone (Figure 3B). AtMYB58 and AtMYB63 are positive regulators of phenylpropanoid biosynthesis; hence, we anticipated that MYB65 might activate target gene expression. To test this, we fused the PAL4 regulatory sequence used for Y1H to the luciferase (LUC) reporter (pPAL4::Luc) and assayed by transient expression in maize protoplast the ability of p35S::MYB65-GFP to activate pPAL4::Luc, using p35S::Renilla (REN) as a normalization control (Figure 3C). Our results showed that p35S::MYB65- GFP strongly activated pPAL4::Luc, indicating that it functions as a transcriptional activator in maize, as it does in Arabidopsis (Zhou et al., 2009). 

LBDs have been largely associated with the regulation of plant organ development and responses to phytohormones, salinity, or glucose (Borghi et al., 2007; Bureau et al., 2010; Majer and Hochholdinger, 2011; Mangeon et al., 2011; Chanderbali et al., 2015; He et al., 2016; Xu et al., 2016). Arabidopsis LBD family members also negatively regulate tracheary element differentiation and anthocyanin metabolism (Soyano et al., 2008; Rubin et al., 2009). The AD-TF library contains 33 of 43 maize LBDs, and 12 participated in the PDIs described here (Supplemental Table 2). LBD35, LBD24, and LBD20 recognized respectively 24, 23, and 18 gene promoters in both the phenylpropanoid and flavonoid pathways (Figure 3A and Supplemental Figure 5). AtLBD16 corresponds to the ortholog of LBD24 and functions as a transcriptional activator in controlling lateral root formation (Lee et al., 2009, 2013). The functions of LBD35 and LBD20, or their orthologs in other plants, remain unknown. Our screen also identified Ramosa2 (LBD16, involved in stem cell fate determination in lateral meristems) (Chuck et al., 2010) as binding to the promoters of the A1, Bz1, CHI1, and PAL4 genes. To our knowledge, RA2/LBD16 has not been previously linked in any way to phenylpropanoid/flavonoid regulation. 

DOFs have a great variety of functions including tissue differentiation, seed development, phytohormone and phytochrome signaling, and metabolism regulation (Noguero et al., 2013; Gupta et al., 2015). In Arabidopsis, AtDOF4;2 was reported to repress flavonoid and activate lignin biosynthetic pathway genes (Skirycz et al., 2007). Of the 46 DOF gene family members present in the maize genome, 32 were represented in the AD-TF library. Nine members were shown to bind phenylpropanoid pathway gene promoters, among which DOF28 recognizes 15 gene promoters corresponding to the phenylpropanoid, lignin, and flavonoid branches of the pathway (Figure 3A and Supplemental Figure 5). From the maize DOF genes for which functions are known, we identified only PBF (DOF3) as controlling the PAL1, PAL5, F3H3, Bz1, and F30 H promoters. PBF was previously described as endosperm specific, functioning with Opaque2 (bZIP1) to regulate seed storage protein zein genes (Vicente-Carbajosa et al., 1997). 

NLPs were reported to function as the main regulators governing the primary nitrate response (Chardin et al., 2014). From the 17 NLP members in the maize genome, nine were represented in the AD-TF library. NLP9 recognizes 13 promoters corresponding to all branches of phenolic biosynthesis (Figure 3A and Supplemental Figure 5), suggesting a hitherto unrecognized 


A


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/e3bcab63931d7608be1352ae1a67fb8ede8e064c1b768ff4b79e4541394e4920.jpg)



SD-His-Ura-Leu


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/ff7073d7fe2b666fef7b9f9a6295be0114052883ca7410eaf95c003bbed8140b.jpg)



SD-His-Ura-Leu +3AT (mM)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/94da66a608f8a9a57daeaafc9ed5ef508588e6ba95ace737a90022de243eaf31.jpg)



1,3,5,7: EV


2,4,6,8:AD-MYB100 

B 

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/b321c9e3f3263910a9868f6aefcd0b42da9bae6763f591a704f87e0a1c6b0763.jpg)


potential link between phenolic biosynthesis and N cellular status. 

CPPs correspond to a small TF family that has received significantly less attention compared with other families. Until now, only two CPPs have been functionally characterized in plants (Lu et al., 2013; Zhang et al., 2015). AtTSO1 regulates cytokinesis and cell expansion, meristem organization, and cell division (Liu et al., 1997; Hauser et al., 2000), and CPP1 was reported to regulate leghemoglobin genes in the symbiotic root nodule in soybeans (Cvitanich et al., 2000). Of 13 maize CPP members, five were represented in the AD-TF library. Our Y1H analysis shows that CPP8, CPP12, and CPP9 recognize phenolic gene promoters, and CPP8 in particular binds to 13 promoters across all branches of the phenolic pathway (Figure 3A and Supplemental Figure 5). 

bZIPs are a large TF family with members involved in regulating critical physiological processes, such as plant defense (Alves et al., 2013), stress responses (Fujita et al., 2005), hormone signaling (Choi et al., 2000), development (Abe et al., 2005), senescence (Smykowski et al., 2010), and seedling maturation (Alonso et al., 2009). Maize harbors 125 bZIPs (Wei et al., 2012), and 90 were represented in the AD-TF library. bZIP63 recognized the regulatory regions of 12 genes across all branches of the phenolic pathway (Figure 2 and Supplemental Figure 5). FEA4 (bZIP57), which regulates shoot meristem size in maize (Pautler et al., 2015), was identified as binding to the F5H1 gene. 

The maize genome harbors 67 CCCH zinc finger (C3H) TFs (Peng et al., 2012), 42 of which were represented in the AD-TF library. 


Figure 2. Y1H Identified PDIs and In Vivo Validation.


(A) The interaction of MYB100 with different promoters identified from the Y1H screen is shown in non-selective SD-His-Ura-Leu and selective SD-His-Ura-Leu + 3-AT media plates as an example of how validations were carried out. The empty vector (EV) was used as negative control. 

(B) Validation of the Y1H-identified MYB100 PDIs in maize protoplasts transformed with p35::GFP-MYB100 by ChIP–qPCR using anti-GFP antibodies. qPCR was performed using the primer pairs (Supplemental Table 1) indicated in Supplemental Figure 1 for each of the genes tested. The fold enrichment was calculated using the Copia genomic regions as control, and normalizing to the respective input controls (see Methods). Values represent the mean $\pm$ SE of three independent biological replicates (representing transformation of three independent protoplast preparations from seedlings grown at different times, each done in triplicate), $^ { \star } P < 0 . 0 5$ , two-sided Student’s t-test. 

Functional studies have shown that plant C3H family members are important regulators of seed germination, plant development, hormone responses, and biotic/ abiotic stress responses (Li and Thomas, 

1998; Kong et al., 2006; Kim et al., 2008; Guo et al., 2009; Huang et al., 2012; Bogamuwa and Jang, 2014; Maldonado-Bonilla et al., 2014). From our studies, C3H42 was shown to bind 10 different promoters in the phenolic pathway, including two general phenylpropanoid genes PAL9 and 4CL3, eight lignin genes ALDH1, ALDH5, COMT1, F5H1, HCT6, and HCT10, and two flavonoid genes FLS1 and C2 (Figure 2A and Supplemental Figure 5). 

MBF1 is known as a small group of transcriptional co-activators that enhances transcription of its target genes by bridging the general factor TBP (TATA Binding Protein) and specific TFs bound to their target promoters, as demonstrated in yeast, Drosophila, and Arabidopsis (Takemaru et al., 1998; Jindra et al., 2004; Tsuda et al., 2004). Interestingly, Arabidopsis AtMBF1c binds DNA directly and functions as a transcriptional regulator to control heat stress gene expression (Suzuki et al., 2011). Maize expresses three MBFs and all are presented in the AD-TF library. The Y1H screens revealed that MBF1.3 recognizes 10 phenolic biosynthesis gene promoters. Two (Bz2 and PAL5) were randomly selected to validate the PDIs of MBF1.3 by ChIP in maize protoplasts, and in both cases, in vivo PDIs were detected (Figure 2 and Supplemental Figure 4). 

Our screen for TFs that control phenolic biosynthesis genes identified most of the few known regulators of the pathway, including P1 (ZmMYB3) required for the regulation of 3-deoxyflavonoids, C-glycosyl flavones, and hydroxycinnamic acids (Grotewold et al., 1998); ZmMYB40 (also known as MYB-IF35), capable of inducing chlorogenic and ferulic acids in maize cultured cells (Dias and Grotewold, 2003); and MYB31 (its paralog MYB42 is not in the AD-TF library), involved 

in the repression of lignin biosynthetic genes, including COMT1 (Fornale´ et al., 2010; Agarwal et al., 2016). Consistent with previous studies showing that R (bHLH1) directly binds $B z \mathcal { I }$ , but not A1 (Kong et al., 2012), our studies identified R in the screen of the bait strain harboring the Bz1 promoter, but not A1 (Supplemental Table 2). The R2R3-MYB partner C1, which recruits R to A1, was not found, consistent with the low intrinsic DNA-binding affinity of C1 for DNA making it unable to function in yeast activation experiments (Hernandez et al., 2004). Thus, the TFs identified in the Y1H described here are in good agreement with previous studies. 

It is also interesting to see which TFs described in the literature as phenolic or secondary cell wall regulators did not appear in our screens. One such example is provided by the orthologs of Arabidopsis NAC VND7, which acts as a master switch activating secondary wall biosynthesis in vessels (Kubo et al., 2005; Zhou et al., 2009). In maize, VND7 is represented by three TFs, all present in the AD-TFome collection: NAC103, NAC92, and NAC62 (Zhong et al., 2011; Nakano et al., 2015). We identified, however, NAC62 as a putative regulator of COMT1. This is consistent with the idea that NAC regulators positioned high in the secondary cell wall GRN influence lignin composition by regulating the enzymes that convert precursors of G- to S-lignin (Zhao et al., 2010). We did not find NAC103 nor NAC92 as recognizing any of the 54 promoters tested, suggesting that similar to Arabidopsis, they are primarily involved in the regulation of genes encoding TFs that function at higher levels of the GRN. 

Unexpectedly, our studies also identified members from 16 coregulator families that directly recognize phenolic gene promoters in yeast (Supplemental Figure 3 and Supplemental Table 2). These include 16 members of the AUX/IAA family, nine members of TRAF family, five LIM family members, five HMG (High Mobility Group) family members, two members of the BSDs (BTF2-like TFs, synapse-associated proteins, and DOS2- like proteins), four FHA family members, five components of the Mediator complex, two RCDL (Rcd1-like) family members, and a member each from the MBF1, TAZ (TAZ zinc finger), WAD40, IWS1 (Interact with SP6), and Co-activator p15 families. While there are studies indicating that members of the MBF1, BSD, HMG, and LIM families can function as transcriptional regulators (Kawaoka et al., 2000; Suzuki et al., 2011; Ba et al., 2014; Xia et al., 2014), our studies provide the first evidence that members of the FHA, TRAF, RCDL, TAZ, WAD40, IWS1, and Co-activator p15 can directly control gene expression. 

# Connectivity Properties of the Nascent Maize GRG

To appreciate the potential inherent complexity of maize gene regulation, we investigated how many different regulatory sequences a particular TF is able to recognize (outgoing connectivity), as well as the number of TFs that bound to a particular regulatory sequence (incoming connectivity). As anticipated, the outgoing connectivity followed a power law distribution, which in the case of this GRG portion is characterized by an exponent parameter value of 2.9 (see Methods). Goodness of fit using the Kolmogorov–Smirnov (KS) test comparing the fitted power law distribution and the empirical distribution of the data yielded a significant power law fit (KS D statistic of 0.03, $P$ value of 0.99) 

(Figure 4A) (see Methods). A total of 336 of 568 TFs $( 6 0 \% )$ recognized only one regulatory sequence, and 11 out of 568 $( 2 \% )$ recognized 10 regulatory sequences or more, with the maximum identified so far corresponding to LBD35, a member of the Lateral Organ Boundary (LOB) Domain (LBD) family of TFs (Thatcher et al., 2012), recognizing 24 different regulatory sequences (Figure 3A). 

While the outgoing connectivity distribution observed is likely an emerging property of the maize GRG, the incoming connectivity distribution is very much affected by how deeply we have searched for TFs that recognize each regulatory sequence. Nevertheless, it is interesting that, thus far, four promoters are each recognized by 57 TFs or more (Figure 4B), with those corresponding to COMT1 (encoded by brown midrib3, bm3) and Bz1 (encoding one of the last steps in the anthocyanin biosynthesis pathway) being recognized by 161 and 129 TFs, respectively (Supplemental Table 2 and Supplemental Figure 3). The large number of TFs recognizing the COMT1 and Bz1 promoters is in part a consequence of having screened these in more depth than others. If we normalize the data to the number of transformants screened for each bait strain, we find that HCT6 and HCT10 correspond to the two promoters with the highest proportion of recognizing TFs (Figure 4C). It is in fact not yet known how many TFs can converge in the control of a single gene in maize. If we look in C. elegans, which probably has one of the most comprehensive GRGs resulting from the combination of ChIP-seq and Y1H, 228 gene regulatory regions are targeted by 60 TFs or more, and one gene is bound by 105 TFs (Deplancke et al., 2006a; Niu et al., 2011; Reece-Hoyes et al., 2011; Liu et al., 2014). We expect that in a larger genome with significantly more regulatory factors, the number of TFs that participate in the regulation of a given gene is even larger. Taken together, our results provide a framework for a comprehensive maize GRG involved in the control of phenolic compounds. 

# Identification of TF Combinations for Gene Regulation

We identified 51 instances of two or more plasmids encoding for different TFs present in a single yeast strain growing in selection media (Supplemental Table 4). To determine whether they corresponded to TFs that needed to work together for function, we transformed them separately and together into the corresponding naive yeast bait strain and compared growth, when plated in the selective medium. An example is provided by ZHD14 and EREB12 working cooperatively for the activation of the $B z \eta$ promoter. The results indicate that, on selection medium (SD-Ura-His-Leu $+ 4 0 \ m \mathsf { M } \ 3 { - } \mathsf { A T } )$ , growth was only observed when both TFs were present (Figure 5A, compare #3 to #1 and #2). Similarly, LBD4 and NAC37 were together required for activation of the Bz1 promoter. However, LBD4 alone is sufficient to activate A1 (Figure 5B, #1), and the presence of NAC37 appears to impair the ability of LBD4 to regulate this promoter (Figure 5B, #3). The identification of these TF pairs highlights an unexpected advantage of the transformation Y1H screen over mating methods, providing valuable potential examples of combinatorial gene regulation. 

Transcriptional cooperation can involve many mechanisms, including physical TF–TF interactions. Thus, for a subset of 21 

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/cbc80e133a450bd7bf17c8f8cc88c80259b0c0ed64c20cbcebe879777e57315a.jpg)



B


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/0c791ab2655f0913a8c58ba687917b8e00b2e35f58fe04f52ccdf8a337407153.jpg)



Fold enrichment over input


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/53b12f0782bda3ade3b3791b1e2a9f4a846dad5cec643894e7c742ee04747bd7.jpg)



C


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/0e6c3502bdf326ad39f4fd40b260f773d496fbbe7531b682cd45ff0069517a73.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/9709c2f73e7f7b11acbb89e0cddde36e10631cea4c4c38d87f00ba1790b54c1d.jpg)



Figure 3. Target Validation and Transcriptional Regulatory Activity of MYB65.


(A) Zoom-in of the heatmap depicting all PDIs (Supplemental Figure 3) focusing on the 11 TFs controlling 10 or more promoters. The brown-yellow gradient represents the frequency by which a particular TF participates in PDI identified by Y1H screenings. Blue represents PDIs identified from Y1H-directed assays. 

(B) Validation of MYB65 Y1H-identified PDIs by ChIP–qPCR. The fold enrichment was calculated using the Copia genomic regions as controls. Validation of the Y1H-identified MYB65 PDIs in maize protoplasts transformed with p35S::MYB65-GFP by ChIP–qPCR using anti-GFP antibodies. Fold enrichment 

(legend continued on next page) 

identified TF pairs (Supplemental Table 4), we investigated whether the TF pairs involved physically interacted, using a yeast two-hybrid (Y2H) assay. For this, the respective TFs were cloned into the pBD-GAL4 vector (harboring the TRP1 selectable marker gene) encoding the GAL4 DNA-binding domain (BD-TF). We then transformed the corresponding AD-TF and BD-TF pairs into the pJ69.4a yeast strain harboring the HIS3 and ADE2 selectable markers downstream of GAL4-binding sites (James et al., 1996). In this Y2H assay, growth in SD-Leu-Trp-His and SD-Leu-Trp-His-Ade plates is indicative of interaction. Using this approach, we identified four instances of interacting TFs (ZHD14 with EREB12, LBD4 with NAC37, MYB70 with MYB73, and EREB7 with bHLH148) that needed to be together to activate transcription (Figure 5C). Taken together, our results not only identified multiple instances of TFs that needed a second TF for transcriptional activation in yeast, but also examples of interacting TFs potentially involved in combinatorial phenolic gene regulation. 

# Integration of Y1H with Available ChIP-Seq Data

To generate a more comprehensive phenolic GRG, we integrated Y1H- and ChIP-seq-derived interactions. This resulted in a threetiered integrated GRG (Figure 6A), in which the top-tier nodes correspond to the five TFs for which ChIP-seq data are available (Bolduc et al., 2012; Morohashi et al., 2012; Eveland et al., 2014; Li et al., 2015; Pautler et al., 2015). The middle tier nodes correspond to the 461 unique TFs that corresponded to ChIP-seq targets of the five first-tier TFs, and which participate in at least one PDI with phenolic genes (bottom-tier nodes) in our Y1H assays. While maize ChIP-seq experiments provided about 11 839 PDIs, they involved only five TFs (P1 [MYB3], KN1 [HB1], RAMOSA1, OPAQUE2 [bZIP1], and FEA4 [ZmbZIP57]), demonstrating the low representation of TFs in the ChIP-seqderived grid model. 

From the five maize TFs for which ChIP-seq data are available, only P1 and FEA4 were identified in our Y1H screens (Figure 6B). In the Y1H assays, P1 recognized nine promoters (green plus red in Figure 6B), including those of 4CL3, HCT10, and A1, which were also identified as P1 target by ChIP-seq (Morohashi et al., 2012). However, ChIP-seq identified P1 tethered to an additional 15 phenolic gene promoters (blue in Figure 6B) that were not identified by Y1H. Similarly, none of the phenolic gene promoters recognized by KN1 or O2, and only 1 of 21 of those recognized by FEA4 (RA1 was not present in the AD-TF library) in ChIP-seq, were recognized by these TFs in the Y1H assays (Figure 6B). While there are many possible explanations, it is conceivable that these regulators are recruited to the promoters in vivo through another factor, interactions that would therefore not be identified by Y1H. 

To gain additional resolution on what some of the regulatory motifs in the nascent GRG look like, we focused on the regulation of 

two key phenolic genes, 4CL3 (Figure 6C), encoding an early step in the general phenylpropanoid pathway; and COMT1 (Figure 6D), corresponding to one of the late lignin branch pathway enzymes that control the conversion between G- and S-lignin (Figure 1). The 4CL3-centered subgrid depicts Y1Hderived interactions involving TFs encoded by genes recognized in ChIP-seq by KN1, FEA4, and P1 (Figure 6C). One of the genes, ARF34, is negatively regulated by KN1. In addition, ChIP-seq experiments show that KN1, P1, and FEA4 bind 4CL3, with KN1 exhibiting a positive regulatory interaction, based on RNAseq data (Bolduc et al., 2012). We also identified the P1–4CL3 interaction in our Y1H assays, in addition to the one identified by ChIP-seq. The 4CL3-centered subnetwork contains numerous feed-forward loops (FFLs) consisting of KN1, KN1 targets that are TFs identified in Y1H (for instance ARF34 and EREB), and 4CL3. Similarly, FFLs consisting of P1, TF genes that were P1 targets and which were also identified in our Y1H screens controlling 4CL3, and finally FEA4, FEA4 TF targets, and 4CL3 form another FFL. 

Several well-characterized PDIs participate in the regulation of COMT1, including activation by KN1, FEA4, and P1 (Eveland et al., 2014; Pautler et al., 2015), and repression by MYB11 and MYB31 (Fornale´ et al., 2010; Ve´ lez-Bermu´ dez et al., 2015) (Figure 6D). In addition, KN1 represses GRF4, a ChIP-seqderived target gene that codes for a TF that binds COMT1 in our Y1H screens. The result is an FFL encompassing KN1, GRF4, and COMT1. In addition, several of the KN1 ChIP-seq targets that encode for TFs bind COMT1, resulting again in numerous FFLs (Figure 6D). 

Other motifs that were identified in the integrated subnetworks include bi-fans, motifs that are characterized by TFs binding the same set of target genes. For instance, the 4CL3-centered subnetwork consists of target genes co-bound by KN1, P1, and FEA4, while the COMT1 subnetwork contains bi-fans characterized by targets co-bound by both KN1 and FEA4 (Figure 6C and 6D). Thus, the integrated GRG demonstrates that the richness of TF connections (outgoing connectivity) provided by ChIP-seq is uniquely complemented by the large number of TFs identified by Y1H (incoming connectivity), resulting in the identification of network properties that would otherwise not be captured by using just one approach. 

# DISCUSSION

We present here a gene-centered approach to identify the PDIs involved in the regulation of maize phenolic biosynthesis. Given the important role of TFs as major drivers of genetic variation (Wallace et al., 2014), understanding which TFs control which sets of phenolic biosynthesis genes is important for the rational metabolic engineering of plants with altered lignin or other 


A


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/49dffc016303c98d014f3b064b1252ee6ce2cf46af8d647ec13d6fc3109c49f0.jpg)



B


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/9c73e462587ef3819104df6e81f613fe15b11457ae9603a73930130371ee55c3.jpg)



C


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/2cfafb1cef2a297aa56d82eb93f55ef83254f33d3adc1b8b24dbbe97a230d3bb.jpg)



Figure 4. In and Out Connectivity Properties of the Resulting GRG.



(A) Outgoing connectivity follows a decaying power law distribution (exponent parameter value $= 2 . 9$ ). Most TFs $( 6 0 \% )$ interact with just one promoter. Twelve TFs $( 2 \% )$ interact with 10 or more promoters, and LBD35 interacts with 24 promoters. The inset shows the log–log plot of the out-degree distribution exhibiting a linear relationship, a characteristic of a scale-free network.



(B) Incoming distribution describing the number of promoters that are bound by a range of TFs, from 2 to 161 TFs.



(C) Normalized outgoing connectivity representing the ratio of TFs binding to promoters by the number of transformants screened for each yeast bait strain.


specialized metabolites (Grotewold, 2008), and to exploit genetic diversity in breeding activities. The gene-centered approach used here is based on Y1H and significantly complements ChIP-based TF-centered approaches. 

Rather than using a high-throughput enhanced Y1H assay relaying on a robotic mating platform (Gaudinier et al., 2011; Reece-Hoyes et al., 2011), we screened a TF library followed by validation through individual TF transformations for the identification of high-confidence PDIs. Our study identified more than 1100 PDIs, which included a handful of previously known TF–target gene interactions, upholding the soundness of the method. An unexpected result that would have not been obtained using a mating-based approach was the identification of 51 TF combinations capable of activating transcription as pairs, but not individually. This number is probably an underestimate, since the identification of the TFs present in the yeast 

strains was done by PCR, which results in the preferred amplification of smaller amplicons. However, we think that this high frequency of TFs working as complexes, which potentially alter the DNA-binding specificity of the TFs involved (Jolma et al., 2015), does in part explain the variability in the Y1H validation frequency using individual TFs as well as the modest overlap between the Y1H and ChIP-seq approaches. Combinatorial gene regulation provides a mechanism by which relatively small numbers of TFs form different TF complexes that can control the expression of a much larger number of genes with finely tuned temporal and spatial patterns (Brkljacic and Grotewold, 2017). We determined that TF–TF interactions participate in four of the 51 TF pairs that we identified as required for control of gene expression in yeast. In one clear example of combinatorial control, we show that AD-LBD4 works together (in yeast) and physically interacts with AD-NAC37 to activate the anthocyanin biosynthesis gene $B z \mathcal { I }$ , while 

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/32f00a5ead005d40c263216b4c5e649eb079f462d831aa7b00962e55064fbe21.jpg)



Figure 5. Y1H-Identified TF Cooperation.



(A) Yeast plates showing the ZHD14 and EREB12 cooperation on the Bz1 promoter. This is evidenced by the yeast bait strain growing in selective medium (SD-His-Ura-Leu + 40 mM 3-AT) only when AD-ZHD14 and AD-EREB12 are expressed together, but not when they are expressed separately. AD-GAL4 was used as the bait strain selfactivation control. All the transformants were also grown in non-selective medium (SD-His-Ura-Leu).



(B) Yeast plates showing that LBD4 and NAC37 work together on the Bz1 promoter, but LBD4 activates better alone the A1 promoter.



(C) Plates corresponding to Y2H interactions between ZHD14 and EREB12; LBD4 and NAC37; MYB70 and MYB73; and EREB7 and bHLH148. Transformations with the AD and BD empty plasmids were used as self-activation controls. Transformed colonies were streaked on SD-Leu-Trp, SD-Leu-Trp-His, and SD-Leu-Trp-His-Ade plates, with weaker interactions being evident in SD-Leu-Trp-His and stronger on SD-Leu-Trp-His-Ade selective media.


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/5355b79b54b28fa437540036addc35689f377ea28d430eadcb9b23ceb1aa0285.jpg)



one or more shared TFs (Grotewold, 2008), these are more likely to serve as major regulators of specific branches or the entire phenylpropanoid pathway. Experiments are currently underway to determine whether this is indeed the case. The identification of TFs as potential regulators of plant phenolic compounds provides outstanding opportunities to start investigating how these pathways are regulated in response to environmental stress conditions, and in turn how they participate in the ecophysiology of the plants in which they accumulate (Cheynier et al., 2013). A number of metabolic QTLs associated with phenolic metabolism have been identified in maize over the past few years (Wen et al., 2014, 2016). A statistical test (see Methods) demonstrated that there is a significantly larger overlap between the 568 TFs identified as controlling at least one phenolic promoter and the genes underlying each of the mQTLs, when compared with the 1333 TFs in the AD-TF library that failed to recognize any promoter in our screen. This analysis suggests a


AD-LBD4 can activate A1, another anthocyanin biosynthesis gene, independently of AD-NAC37. Whether these TFs function similarly in maize to control anthocyanin pigment formation remains to be determined. 

We identified 11 TFs that recognize 10 or more phenolic gene promoters, including MYB65, which we showed to function as a transcriptional activator in maize protoplasts (Figure 3). Because metabolic pathway genes are often co-regulated by 

possible path for identifying candidate regulatory genes corresponding to phenolic mQTLs. 

The distinction between a TF and a co-regulator is often operational, and whether a protein is defined as one or the other depends on how it was studied, as it is often the case that a TF can participate in DNA contacts in one promoter but participate in a co-regulator function on another. The MBF1 family provides a good example (Suzuki et al., 2011). Besides MBF1.1, MBF1.2, 


A


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/2ce3e03c8dbefcda1111fc489ccdfd6a96d7925effceafccbbe058c35763f997.jpg)



B


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/78afc21e4c8a4c7e32929b6709423fd478782e85c284918c44f9e5a8953666d9.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/626170208c518e8976b1c25fd03125572b69c9e1abab6c01c80f6d7d380d0ee6.jpg)



D


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-19/5eb1d68e-e99d-4985-a5c8-2bc009bc37b5/72266274900cbc42808a7c4daf9e6a254d17f6cd74cd3bb045392e7704ac28b8.jpg)



Figure 6. Integration of Gene- and TF-Centered Approaches into a Phenolic Gene Regulatory Grid.


(A) Gene regulatory grid (GRG) for phenolic compound biosynthesis derived by the integration of Y1H (green) and ChIP-seq (blue) identified interactions. The three-tiered GRG consists of TFs (represented by squares) for which ChIP-seq interactions are available (RA, FEA4, KN1, O2, and P1; top-tier nodes); a middle tier corresponding to TFs present in the AD-TF collection encoded by genes that were targets of first-tier TFs; and a bottom tier corresponding to the phenolic biosynthetic genes (represented by squares) used as bait in the Y1H screens. 

(B) Bar graph representing the number of phenolic genes represented in the Y1H baits bound by TFs derived from ChIP-seq experiments (blue), from Y1H assays (green), or common to both (red). 

(C) TF interactions (as represented in A) that converge on the regulation of 4CL3. Green lines indicate PDIs identified by Y1H, and blue by ChIP. 

(D) TF interactions (as represented in A) that converge on the regulation of COMT1. Green lines indicate PDIs identified by Y1H, and blue by ChIP. 

and MBF1.3, we identified members from 15 additional coregulator families that recognize phenolic gene promoters (Supplemental Figure 3 and Supplemental Table 2). Whether they directly bind to DNA, as shown for MBF1, or whether they are capable of activating transcription in yeast by another mechanism will require further experimentation. 

Gene- and TF-centered approaches to identify GRG edges are often complementary (Walhout, 2011; Mejia-Guerra et al., 2012), and this is also evident in our studies. We identified several instances in which TFs recognize in Y1H two or more promoters, whereas additional one(s) would show interaction by ChIP–PCR but not in yeast (Table 1). One possibility is that the binding occurs outside of the region included in the bait constructs. Alternatively, it is possible that in maize cells the TF is tethered to the promoter through another TF, providing a positive ChIP result, but because the interaction with DNA is not direct, this PDI would not be identified in the Y1H assay. Indeed, we have previously shown such a mechanism to be at play in the control of maize anthocyanin biosynthesis. The R2R3-MYB factor C1 recruits the bHLH factor R to the A1 gene promoter. Yet on Bz1, it is R that makes direct contact with DNA (Kong et al., 2012). Consistent with this, we identified R in the screen for TFs controlling Bz1, but not A1. Instances in which we identified a Y1H interaction that could not be recapitulated by ChIP could reflect a false positive, or an interaction that occurs in a tissue or condition different from those tested by ChIP. Indeed, we believe that similar strengths and weaknesses of both methods are in part responsible for the modest overlap between the interactions identified by Y1H and the few ChIP-seq experiments so far conducted in maize. We hope that the resources and tools generated herein will encourage others to screen additional promoters and perform ChIP-seq with more TFs to increase the coverage of the maize GRG. 

# METHODS

# Maize Genotypes and Growth Conditions

Two-week-old B73 seedlings used for genomic DNA isolation were grown in soil in the greenhouse at $2 7 ^ { \circ } \mathsf { C } / 2 1 ^ { \circ } \mathsf { C }$ day and night temperatures respectively, with a 16-h day/8-h night photoperiod and $60 \%$ relative humidity. Leaves from 2-week-old $\mathsf { B } 7 3 \times$ Mo17 F1 hybrid etiolated seedlings grown in a growth chamber at $\boldsymbol { 2 5 ^ { \circ } \mathrm { C } }$ and $70 \%$ relative humidity under continuous dark conditions were used as a source of protoplasts for ChIP and transactivation analyses. 

# Generation of Y1H Promoter Clones

Upstream regulatory DNA fragments used as bait in the Y1H screenings were selected from the literature, from MaizeGDB (http://www. maizegdb.org/) or from experimentally established TSS determined by CAGE (Mejia-Guerra et al., 2015). B73 genomic DNA was isolated by a cetyltrimethyl ammonium bromide-based method (Hulbert and Bennetzen, 1991) and used as template. Regions comprising $\sim 5 0 0 -$ to 2000-bp long sequences located upstream of the TSSs were amplified using Phusion High-Fidelity DNA Polymerase (Life Technologies, Grand Island, NY) and primers were designed using the web-based software Primer 3 (Rozen and Skaletsky, 2000) (Supplemental Table 5). The amplicons were recombined into pDONR P4-P1R (Life Technologies) and subsequently subcloned into the Y1H destination vectors pMW#2 and pMW#3 containing HIS3 and LacZ, respectively (Deplancke et al., 2006a) using LR Clonase (Life Technologies), and confirmed by sequencing using primers listed in Supplemental Table 5. 

# Generation of Yeast Strains and Y1H Screenings

The resulting promoter clones were integrated into the genome of yeast strain YM4271 (MATa, ura3-52, his3-200, lys2-801, ade2-101, ade5, trp1-901, leu2-3, 112, tyr1-501, gal4D, gal80D, ade5::hisG) (Clontech, Mountain View, CA) (Liu et al., 1993; Estojak et al., 1995) and selected by growth in dropout medium lacking histidine and uracil (SD-His-Ura). Integration was confirmed by colony PCR with primer pairs P1 and P2 (Supplemental Table 5). Each yeast strain was tested for autoactivation by growth in SD-His-Ura medium containing increasing concentrations (5, 10, 20, 40, 60, 80, 100, and $1 2 0 ~ \mathsf { m M } )$ of 3-amino-1,2,4-triazole (3-AT; Sigma Life Sciences, St. Louis, MO), as previously described (Deplancke et al., 2006b). Y1H screens were performed using 54 different promoter bait strains corresponding to genes encoding enzymes involved in the phenolic biosynthetic pathway, as described previously (Yang et al., 2016) using the maize transcription factor (TFome) library we generated (Burdo et al., 2014). The coding DNA sequences of 1901 TFs were cloned downstream of the GAL4 activation domain in the pAD-GAL4-GW-C1 vector (Machemer et al., 2011) by LR Clonase (Life Technologies). All of the bacterial strains containing the 1901 AD-TF-encoding plasmids were equally pooled to make the AD-TF library. The copy number (number of plasmid molecules per nanogram of library DNA) of 18 random selected TFs ‘‘per ng’’ were quantified by using real-time PCR (see Supplemental Table 5 for primers). A standard curve was made to determine the Ct values for specific plasmid quantities. The weight (ng) was then calculated from Ct values and converted to molar by using molecular weight of each plasmid. The AD-TF library was used to transform yeast strains harboring the promoter:: selectable marker integrated constructs. Positive interactions were identified by selection of colonies on SD-His-Ura-Leu medium with different concentrations of 3-AT, and compared with the growth of a strain harboring the pAD-GAL4-GW-C1 empty vector (referred to as EV) as control. Validations of positive interactions were performed by retransforming each AD-TF plasmid individually into the naive strain, and selecting colonies by growth in SD-His-Ura-Leu + 3-AT medium. 

# Y2H Assay to Validate TF–TF Interactions

Y1H assays identified TF pairs that work cooperatively were investigated with physical interactions using Y2H assay. First, TFs were cloned into both pAD-GAL4-GW-C1 vector (AD-TF) as prey and pBD-GAL4-GW-C1 vector (BD-TF) as bait. AD and BD were used as controls to examine self-activation. The corresponding AD-TF and BD-TF pairs were transformed into the pJ69.4a yeast strain harboring the HIS3 and ADE2 selectable markers downstream of GAL4-binding sites. Transformed yeast strains were first plated on the SD-Leu-Trp plates and incubated at $_ { 3 0 ^ { \circ } \mathrm { C } }$ for 3 days. Putative positive colonies (at least three) were then streaked on the SD-Leu-Trp, SD-Leu-Trp-His, and SD-Leu-Trp-His-Ade plates and incubated at $_ { 3 0 ^ { \circ } \mathrm { C } }$ for 3 days to determine physical interaction between corresponding TF pairs compared with self-activation of TFs. 

# Generation of Promoter::Luciferase Reporter Clones and Transactivation Analyses in Maize Protoplasts

For generation of the luciferase reporter constructs, the promoter fragments used for Y1H screening were cloned into the pENTR/SD/D-TOPO vector (Life Technologies). The resulting plasmids were used to insert the promoter sequence into the destination vector pLUC2, in which a Gateway cassette was cloned upstream of the luciferase reporter gene (Kim and Somers, 2010) using LR Clonase (Life Technologies). For generation of the effector constructs, the coding sequence of each TF was cloned into the pENTR/SD/D-TOPO vector (Life Technologies) (Burdo et al., 2014), and then inserted downstream of a 35S promoter in the Gateway overexpression vector P2GW7 (Karimi et al., 2002) using LR Clonase (Life Technologies). Maize leaf protoplasts were prepared and co-transfected as described by Burdo et al. (2014), using $1 5 ~ \mu \ g$ each of the reporter and effector constructs together with $1 \ \mu \mathfrak { g }$ of the reference construct containing the Renilla luciferase gene driven by the $p 3 5 S$ promoter. Protoplasts were incubated for 18–22 h in the dark at 

$\boldsymbol { 2 5 ^ { \circ } \mathrm { C } }$ before lysing and evaluating the luciferase activity in a 96-well plate using the dual-luciferase reporter assay kit (Promega) according to the manufacturer’s instructions on a Centro LB 960 Microplate Luminometer (Berthold Technologies, Germany). The peak emission of firefly luciferase bioluminescence color is 560 nm with the range of 550–620 nm. The luciferase (firefly) activity was calculated by normalizing against the Renilla luciferase activity. A p35S::Renilla construct (Elomaa et al., 1998) was included in each transformation as a normalization control and the data were normalized as described by Kong et al. (2012). The fold activation was calculated as the ratio between the treatment with TF and without TF. The experiments were carried out with three biological replicates from three independent preparations of protoplast. 

# ChIP and ChIP–qPCR Experiments

Ten PDIs were randomly selected from the Y1H results for ChIP. Five PDIs were randomly picked from the PDIs contributed by TFs binding more than one promoter. One additional PDI was then picked from each selected TFs. A matrix of PDIs was generated between five TFs and nine promoters. Directed Y1H assays were then performed on some unknown PDIs to define the false-negative rate. 

Maize TFs were cloned into vector 1511 (p35S::GFP-GW) vector using LR Clonase (Life Technologies) to create N-terminal GFP fusion under the control of the $p 3 5 S$ promoter. Forty micrograms of p35S::GFP-TF were transfected into protoplasts and incubated for 18–22 h in the dark at $\boldsymbol { 2 5 ^ { \circ } \mathrm { C } }$ . GFP expression was evaluated by fluorescence microscopy (Nikon Eclipse E600, Melville, NY) and used to estimate electroporation efficiency. ChIP was performed as previously described (Kong et al., 2012). The fluorescence furnished by p35S::GFP was used to calculate the transformation efficiency, which was usually $3 0 \% { - } 5 0 \%$ . Eight individual reactions were pooled together to yield one biological replicate. ChIPs were performed on three biological replicates from three independent protoplast preparations. Primer design was carried out using Primer 3 (Rozen and Skaletsky, 2000) on the B73 genome (B73 RefGen v3) sequence to amplify 80–120 bp (Supplemental Table 5). qPCR was performed using $1 ~ \mu \mu \up$ of input or ChIPed DNA on a Bio-Rad CFX96 Real-Time PCR Detection System using the Bio-Rad iQ SYBR Green Supermix. Maize TY1-copia type retrotransposon (GenBank #AF398212) and Actin1 (GRMZM2G126010) were used as a negative control, as previously described (Morohashi et al., 2012). 

# Determination of GRG Scale-Free Properties

Node degree distribution was determined by enumeration of either outgoing (out-degree) or incoming (in-degree) edges in the grid model. The resulting data were fitted on the power law distribution and the parameter of the power law, the exponent a, estimated. Analyses were performed in the R statistical and programming environment (https://www. r-project.org/). 

# Overlap of TFs with Known Phenolic QTLs

To determine whether TFs identified by Y1H were overrepresented among the identified phenolic pathway mQTLs, we compared all the TFs associated with at least one mQTL (as determined by Wen et al., 2014, 2016) present in the AD-TF collection but not identified by Y1H (12 TFs) with the number of TFs identified in the Y1H screens (18 TFs). The enrichment analysis was carried out by building a null distribution by resampling (1000 bootstraps of sample 564) TFs present in the AD-TF collection, but not identified by Y1H (mean distribution, 5.2; SD, 2.2). We then compared the number of TFs identified by Y1H with the null distribution generated previously using a Z score. The significance of the $Z$ score obtained (5.3) was calculated by means of a one-tailed hypothesis test with a confidence level of $9 5 \%$ $( x = 0 . 0 5 )$ . 

# Resource Distribution

Maize TF clones in the pENTRY vector described in this study are available from the ABRC through http://grassius.org/tfomecollection.html. All 

of the plasmids and yeast strains for the bait promoter constructs are available from the ABRC under Stock Numbers CD3-1983 to CD3-2151. 

# SUPPLEMENTAL INFORMATION

Supplemental Information is available at Molecular Plant Online. 

# FUNDING

This research was supported by Grant NSF IOS-1125620 to J.G., A.I.D., and E.G., and by state and federal funds appropriated to The Ohio State University, Ohio Agricultural Research and Development Center. 

# AUTHORS CONTRIBUTIONS

J.G., A.I.D., and E.G. designed the experiments. F.Y., W.L., N.J., H.Y., K.M., D.E.M.-M, L.D.P.-S, R.A.V., and J.V. performed the experiments. M.K.M.-G., E.M., W.Z.O., and F.G.-C. established bioinformatics pipelines and performed the computational analyses. F.Y. and E.G. prepared the manuscript with assistance from all other authors. 

# ACKNOWLEDGMENTS

The yeast strain YM4271 and vectors PMW#2 and PMW#3 were kindly provided by Dr. Siobhan Brady (UC Davis, Davis, CA). The p2GW7 plasmid was kindly provided by Dr. Richard Dixon (University of North Texas, Denton, TX). The pLUC2 plasmid was kindly provided by Dr. Hong Gil Nam (Daegu Gyeongbuk Institute of Science and Technology, Korea). The 1511 vector was kindly provided by Dr. Jyan-Chyun Jang (The Ohio State University, Columbus, OH). No conflict of interest declared. 

Received: July 28, 2016 

Revised: September 20, 2016 

Accepted: October 31, 2016 

Published: November 18, 2016 

# REFERENCES



Abe, M., Kobayashi, Y., Yamamoto, S., Daimon, Y., Yamaguchi, A., Ikeda, Y., Ichinoki, H., Notaguchi, M., Goto, K., and Araki, T. (2005). FD, a bZIP protein mediating signals from the floral pathway integrator FT at the shoot apex. Science 309:1052–1056. 





Agarwal, T., Grotewold, E., Doseff, A.I., and Gray, J. (2016). MYB31/ MYB42 syntelogs exhibit divergent regulation of phenylpropanoid genes in maize, sorghum and rice. Sci. Rep. 6:28502. 





Alonso, R., Onate-Sanchez, L., Weltmeier, F., Ehlert, A., Diaz, I., Dietrich, K., Vicente-Carbajosa, J., and Droge-Laser, W. (2009). A pivotal role of the basic leucine zipper transcription factor bZIP53 in the regulation of Arabidopsis seed maturation gene expression based on heterodimerization and protein complex formation. Plant Cell 21:1747–1761. 





Alves, M.S., Dadalto, S.P., Goncalves, A.B., De Souza, G.B., Barros, V.A., and Fietto, L.G. (2013). Plant bZIP transcription factors responsive to pathogens: a review. Int. J. Mol. Sci. 14:7815–7828. 





Ba, L.J., Shan, W., Xiao, Y.Y., Chen, J.Y., Lu, W.J., and Kuang, J.F. (2014). A ripening-induced transcription factor MaBSD1 interacts with promoters of MaEXP1/2 from banana fruit. Plant Cell Rep. 33:1913–1920. 





Barabasi, A.L., and Oltvai, Z.N. (2004). Network biology: understanding the cell’s functional organization. Nat. Rev. Genet. 5:101–113. 





Boerjan, W., Ralph, J., and Baucher, M. (2003). Lignin biosynthesis. Annu. Rev. Plant Biol. 54:519–546. 





Bogamuwa, S.P., and Jang, J.C. (2014). Tandem CCCH zinc finger proteins in plant growth, development and stress response. Plant Cell Physiol. 55:1367–1375. 





Bolduc, N., Yilmaz, A., Mejia-Guerra, M.K., Morohashi, K., O’Connor, D., Grotewold, E., and Hake, S. (2012). Unraveling the KNOTTED1 regulatory network in maize meristems. Genes Dev. 26:1685–1690. 





Borghi, L., Bureau, M., and Simon, R. (2007). Arabidopsis JAGGED LATERAL ORGANS is expressed in boundaries and coordinates KNOX and PIN activity. Plant Cell 19:1795–1808. 





Brady, S.M., Zhang, L., Megraw, M., Martinez, N.J., Jiang, E., Yi, C.S., Liu, W., Zeng, A., Taylor-Teeples, M., Kim, D., et al. (2011). A steleenriched gene regulatory network in the Arabidopsis root. Mol. Syst. Biol. 7:459. 





Brkljacic, J., and Grotewold, E. (2017). Combinatorial control of plant gene expression. Biochim. Biophys. Acta 1860:31–40. http://dx.doi. org/10.1016/j.bbagrm.2016.07.005. 





Burdo, B., Gray, J., Goetting-Minesky, M.P., Wittler, B., Hunt, M., Li, T., Velliquette, D., Thomas, J., Gentzel, I., dos Santos Brito, M., et al. (2014). The Maize TFome—development of a transcription factor open reading frame collection for functional genomics. Plant J. 80:356–366. 





Bureau, M., Rast, M.I., Illmer, J., and Simon, R. (2010). JAGGED LATERAL ORGAN (JLO) controls auxin dependent patterning during development of the Arabidopsis embryo and root. Plant Mol. Biol. 74:479–491. 





Casas, M.I., Falcone-Ferryra, M.L., Jiang, N., Mejia-Guerra, M.K., Rodriguez, E.J., Wilson, T., Engelmeier, J., Casati, P., and Grotewold, E. (2016). Identification and characterization of maize salmon silks genes involved in insecticidal maysin biosynthesis. Plant Cell 28:1297–1309. 





Chanderbali, A.S., He, F., Soltis, P.S., and Soltis, D.E. (2015). Out of the water: origin and diversification of the LBD gene family. Mol. Biol. Evol. 32:1996–2000. 





Chandler, S. (2003). Commercialization of genetically modified ornamental plants. J. Plant Biotech. 5:69–77. 





Chardin, C., Girin, T., Roudier, F., Meyer, C., and Krapp, A. (2014). The plant RWP-RK transcription factors: key regulators of nitrogen responses and of gametophyte development. J. Exp. Bot. 65:5577– 5587. 





Cheynier, V., Comte, G., Davies, K.M., Lattanzio, V., and Martens, S. (2013). Plant phenolics: recent advances on their biosynthesis, genetics, and ecophysiology. Plant Physiol. Biochem. 72:1–20. 





Choi, H., Hong, J., Ha, J., Kang, J., and Kim, S.Y. (2000). ABFs, a family of ABA-responsive element binding factors. J. Biol. Chem. 275:1723– 1730. 





Chuck, G., Whipple, C., Jackson, D., and Hake, S. (2010). The maize SBP-box transcription factor encoded by tasselsheath4 regulates bract development and the establishment of meristem boundaries. Development 137:1243–1250. 





Cvitanich, C., Pallisgaard, N., Nielsen, K.A., Hansen, A.C., Larsen, K., Pihakaski-Maunsbach, K., Marcker, K.A., and Jensen, E.O. (2000). CPP1, a DNA-binding protein involved in the expression of a soybean leghemoglobin c3 gene. Proc. Natl. Acad. Sci. USA 97:8163–8168. 





de Oliveira, D.M., Finger-Teixeira, A., Rodrigues Mota, T., Salvador, V.H., Moreira-Vilar, F.C., Correa Molinari, H.B., Craig Mitchell, R.A., Marchiosi, R., Ferrarese-Filho, O., and Dantas Dos Santos, W. (2015). Ferulic acid: a key component in grass lignocellulose recalcitrance to hydrolysis. Plant Biotechnol. J. 13:1224–1232. 





Deplancke, B., Mukhopadhyay, A., Ao, W., Elewa, A.M., Grove, C.A., Martinez, N.J., Sequerra, R., Doucette-Stamm, L., Reece-Hoyes, J.S., Hope, I.A., et al. (2006a). A gene-centered C. elegans protein-DNA interaction network. Cell 125:1193–1205. 





Deplancke, B., Vermeirssen, V., Arda, H.E., Martinez, N.J., and Walhout, A.J. (2006b). Gateway-compatible yeast one-hybrid screens. CSH Protoc. 2006 http://dx.doi.org/10.1101/pdb.prot4590. 





Dias, A.P., and Grotewold, E. (2003). Manipulating the accumulation of phenolics in maize cultured cells using transcription factors. Biochem. Eng. J. 14:207–216. 





Dias, A.P., Braun, E.L., McMullen, M.D., and Grotewold, E. (2003). Recently duplicated maize R2R3 Myb genes provide evidence for distinct mechanisms of evolutionary divergence after duplication. Plant Physiol. 131:610–620. 





Elomaa, P., Mehto, M., Kotilainen, M., Helariutta, Y., Nevalainen, L., and Teeri, T.H. (1998). A bHLH transcription factor mediates organ, region and flower type specific signals on dihydroflavonol-4- reductase (dfr) gene expression in the inflorescence of Gerbera hybrida (Asteraceae). Plant J. 16:93–99. 





Estojak, J., Brent, R., and Golemis, E.A. (1995). Correlation of two-hybrid affinity data with in vitro measurements. Mol. Cell. Biol. 15:5820–5829. 





Eveland, A.L., Goldshmidt, A., Pautler, M., Morohashi, K., Liseron-Monfils, C., Lewis, M.W., Kumari, S., Hiraga, S., Yang, F., Unger-Wallace, E., et al. (2014). Regulatory modules controlling maize inflorescence architecture. Genome Res. 24:431–443. 





Falcone Ferreyra, M.L., Rius, S.P., and Casati, P. (2012). Flavonoids: biosynthesis, biological functions, and biotechnological applications. Front. Plant Sci. 3:222. 





Fornale´ , S., Shi, X., Chai, C., Encina, A., Irar, S., Capellades, M., Fuguet, E., Torres, J.-L., Rovira, P., Puigdome` nech, P., et al. (2010). ZmMYB31 directly represses maize lignin genes and redirects the phenylpropanoid metabolic flux. Plant J. 64:731–739. 





Fujita, Y., Fujita, M., Satoh, R., Maruyama, K., Parvez, M.M., Seki, M., Hiratsu, K., Ohme-Takagi, M., Shinozaki, K., and Yamaguchi-Shinozaki, K. (2005). AREB1 is a transcription activator of novel ABRE-dependent ABA signaling that enhances drought stress tolerance in Arabidopsis. Plant Cell 17:3470–3488. 





Gaudinier, A., Zhang, L., Reece-Hoyes, J.S., Taylor-Teeples, M., Pu, L., Liu, Z., Breton, G., Pruneda-Paz, J.L., Kim, D., Kay, S.A., et al. (2011). Enhanced Y1H assays for Arabidopsis. Nat. Methods 8:1053– 1055. 





Gray, J., Bevan, M., Brutnell, T., Buell, R., Cone, K., Hake, S., Jackson, D., Kellogg, E.A., Lawrence, C., McCouch, S., et al. (2009). A recommendation for naming transcription factor proteins in the grasses. Plant Physiol. 149:4–6. 





Gray, J., Caparros-Ruiz, D., and Grotewold, E. (2012). Grass phenylpropanoids: regulate before using!. Plant Sci. 184:112–120. 





Gray, J., Burdo, B., Goetting-Minesky, M., Wittler, B., Hunt, M., Li, T., Velliquette, D., Thomas, J., Agarwal, T., Key, K., et al. (2015). Protocol for the generation of a transcription factor open reading frame collection (TFome). Bio Protoc. 5:e1547. 





Grotewold, E. (2006). The genetics and biochemistry of floral pigments. Annu. Rev. Plant Biol. 57:761–780. 





Grotewold, E. (2008). Transcription factors for predictive plant metabolic engineering: are we there yet? Curr. Opin. Biotechnol. 19:138–144. 





Grotewold, E., Chamberlin, M., Snook, M., Siame, B., Butler, L., Swenson, J., Maddock, S., Clair, G.S., and Bowen, B. (1998). Engineering secondary metabolism in maize cells by ectopic expression of transcription factors. Plant Cell 10:721–740. 





Guo, Y.H., Yu, Y.P., Wang, D., Wu, C.A., Yang, G.D., Huang, J.G., and Zheng, C.C. (2009). GhZFP1, a novel CCCH-type zinc finger protein from cotton, enhances salt stress tolerance and fungal disease resistance in transgenic tobacco by interacting with GZIRD21A and GZIPR5. New Phytol. 183:62–75. 





Gupta, S., Malviya, N., Kushwaha, H., Nasim, J., Bisht, N.C., Singh, V.K., and Yadav, D. (2015). Insights into structural and functional diversity of Dof (DNA binding with one finger) transcription factor. Planta 241:549–562. 





Handakumbura, P.P., and Hazen, S.P. (2012). Transcriptional regulation of grass secondary cell wall biosynthesis: playing catch-up with Arabidopsis thaliana. Front. Plant Sci. 3:74. 





Hauser, B.A., He, J.Q., Park, S.O., and Gasser, C.S. (2000). TSO1 is a novel protein that modulates cytokinesis and cell expansion in Arabidopsis. Development 127:2219–2226. 





He, X., Ma, H., Zhao, X., Nie, S., Li, Y., Zhang, Z., Shen, Y., Chen, Q., Lu, Y., Lan, H., et al. (2016). Comparative RNA-Seq analysis reveals that regulatory network of maize root development controls the expression of genes in response to N stress. PLoS One 11:e0151697. 





Heine, G.F., Malik, V., Dias, A.P., and Grotewold, E. (2007). Expression and molecular characterization of ZmMYB-IF35 and related R2R3- MYB transcription factors. Mol. Biotech. 37:155–164. 





Hernandez, J., Heine, G., Irani, N.G., Feller, A., Kim, M.-G., Matulnik, T., Chandler, V.L., and Grotewold, E. (2004). Different mechanisms participate in the R-dependent activity of the R2R3 MYB transcription factor C1. J. Biol. Chem. 279:48205–48213. 





Heyndrickx, K.S., Van de Velde, J., Wang, C., Weigel, D., and Vandepoele, K. (2014). A functional and evolutionary perspective on transcription factor binding in Arabidopsis thaliana. Plant Cell 26:3894–3910. 





Huang, P., Ju, H.W., Min, J.H., Zhang, X., Chung, J.S., Cheong, H.S., and Kim, C.S. (2012). Molecular and physiological characterization of the Arabidopsis thaliana Oxidation-related Zinc Finger 2, a plasma membrane protein involved in ABA and salt stress response through the ABI2-mediated signaling pathway. Plant Cell Physiol. 53:193–203. 





Hulbert, S.H., and Bennetzen, J.L. (1991). Recombination at the Rp1 locus of maize. Mol. Genet. Genomics 226:377–382. 





James, P., Halladay, J., and Craig, E.A. (1996). Genomic libraries and a host strain designed for highly efficient two-hybrid selection in yeast. Genetics 144:1425–1436. 





Jindra, M., Gaziova, I., Uhlirova, M., Okabe, M., Hiromi, Y., and Hirose, S. (2004). Coactivator MBF1 preserves the redox-dependent AP-1 activity during oxidative stress in Drosophila. EMBO J. 23:3538–3547. 





Jolma, A., Yin, Y., Nitta, K.R., Dave, K., Popov, A., Taipale, M., Enge, M., Kivioja, T., Morgunova, E., and Taipale, J. (2015). DNAdependent formation of transcription factor pairs alters their binding specificity. Nature 527:384–388. 





Karimi, M., Inze, D., and Depicker, A. (2002). GATEWAY vectors for Agrobacterium-mediated plant transformation. Trends Plant Sci. 7:193–195. 





Kawaoka, A., Kaothien, P., Yoshida, K., Endo, S., Yamada, K., and Ebinuma, H. (2000). Functional analysis of tobacco LIM protein Ntlim1 involved in lignin biosynthesis. Plant J. 22:289–301. 





Khan, N.A., Yu, P., Ali, M., Cone, J.W., and Hendriks, W.H. (2015). Nutritive value of maize silage in relation to dairy cow performance and milk quality. J. Sci. Food Agric. 95:238–252. 





Kim, J., and Somers, D.E. (2010). Rapid assessment of gene function in the circadian clock using artificial microRNA in Arabidopsis mesophyll protoplasts. Plant Physiol. 154:611–621. 





Kim, D.H., Yamaguchi, S., Lim, S., Oh, E., Park, J., Hanada, A., Kamiya, Y., and Choi, G. (2008). SOMNUS, a CCCH-type zinc finger protein in Arabidopsis, negatively regulates light-dependent seed germination downstream of PIL5. Plant Cell 20:1260–1277. 





Ko, J.H., Kim, W.C., and Han, K.H. (2009). Ectopic expression of MYB46 identifies transcriptional regulatory genes involved in secondary wall biosynthesis in Arabidopsis. Plant J. 60:649–665. 





Kong, Z., Li, M., Yang, W., Xu, W., and Xue, Y. (2006). A novel nuclearlocalized CCCH-type zinc finger protein, OsDOS, is involved in delaying leaf senescence in rice. Plant Physiol. 141:1376–1388. 





Kong, Q., Pattanaik, S., Feller, A., Werkman, J.R., Chai, C., Wang, Y., Grotewold, E., and Yuan, L. (2012). Regulatory switch enforced by basic helix-loop-helix and ACT-domain mediated dimerizations of the 





maize transcription factor R. Proc. Natl. Acad. Sci. USA 109:E2091– E2097. 





Kubo, M., Udagawa, M., Nishikubo, N., Horiguchi, G., Yamaguchi, M., Ito, J., Mimura, T., Fukuda, H., and Demura, T. (2005). Transcription switches for protoxylem and metaxylem vessel formation. Genes Dev. 19:1855–1860. 





Lee, H.W., Kim, N.Y., Lee, D.J., and Kim, J. (2009). LBD18/ASL20 regulates lateral root formation in combination with LBD16/ASL18 downstream of ARF7 and ARF19 in Arabidopsis. Plant Physiol. 151:1377–1389. 





Lee, B.-K.K., Bhinge, A.A., Battenhouse, A., McDaniell, R.M., Liu, Z., Song, L., Ni, Y., Birney, E., Lieb, J.D., Furey, T.S., et al. (2012). Cell-type specific and combinatorial usage of diverse transcription factors revealed by genome-wide binding studies in multiple human cells. Genome Res. 22:9–24. 





Lee, H.W., Kim, M.J., Kim, N.Y., Lee, S.H., and Kim, J. (2013). LBD18 acts as a transcriptional activator that directly binds to the EXPANSIN14 promoter in promoting lateral root emergence of Arabidopsis. Plant J. 73:212–224. 





Li, Z., and Thomas, T.L. (1998). PEI1, an embryo-specific zinc finger protein gene required for heart-stage embryo formation in Arabidopsis. Plant Cell 10:383–398. 





Li, B., Gaudinier, A., Tang, M., Taylor-Teeples, M., Nham, N.T., Ghaffari, C., Benson, D.S., Steinmann, M., Gray, J.A., Brady, S.M., et al. (2014). Promoter-based integration in plant defense regulation. Plant Physiol. 166:1803–1820. 





Li, C., Qiao, Z., Qi, W., Wang, Q., Yuan, Y., Yang, X., Tang, Y., Mei, B., Lv, Y., Zhao, H., et al. (2015). Genome-wide characterization of cisacting DNA targets reveals the transcriptional regulatory framework of opaque2 in maize. Plant Cell 27:532–545. 





Liu, J., Wilson, T.E., Milbrandt, J., and Johnston, M. (1993). Identifying DNA-binding sites and analyzing DNA-binding domains using a yeast selection system. Methods 5:125–137. 





Liu, Z., Running, M.P., and Meyerowitz, E.M. (1997). TSO1 functions in cell division during Arabidopsis flower development. Development 124:665–672. 





Liu, W.J., Reece-Hoyes, J.S., Walhout, A.J., and Eisenmann, D.M. (2014). Multiple transcription factors directly regulate Hox gene lin-39 expression in ventral hypodermal cells of the C. elegans embryo and larva, including the hypodermal fate regulators LIN-26 and ELT-6. BMC Dev. Biol. 14:17. 





Lu, T., Dou, Y., and Zhang, C. (2013). Fuzzy clustering of CPP family in plants with evolution and interaction analyses. BMC Bioinformatics 14:S10. 





Machemer, K., Shaiman, O., Salts, Y., Shabtai, S., Sobolev, I., Belausov, E., Grotewold, E., and Barg, R. (2011). Interplay of MYB factors in differential cell expansion, and consequences for tomato fruit development. Plant J. 68:337–350. 





Majer, C., and Hochholdinger, F. (2011). Defining the boundaries: structure and function of LOB domain proteins. Trends Plant Sci. 16:47–52. 





Maldonado-Bonilla, L.D., Eschen-Lippold, L., Gago-Zachert, S., Tabassum, N., Bauer, N., Scheel, D., and Lee, J. (2014). The Arabidopsis tandem zinc finger 9 protein binds RNA and mediates pathogen-associated molecular pattern-triggered immune responses. Plant Cell Physiol. 55:412–425. 





Mangeon, A., Bell, E.M., Lin, W.C., Jablonska, B., and Springer, P.S. (2011). Misregulation of the LOB domain gene DDA1 suggests possible functions in auxin signalling and photomorphogenesis. J. Exp. Bot. 62:221–233. 





McCarthy, R.L., Zhong, R., and Ye, Z.H. (2009). MYB83 is a direct target of SND1 and acts redundantly with MYB46 in the regulation of 





secondary cell wall biosynthesis in Arabidopsis. Plant Cell Physiol. 50:1950–1964. 





Me´ chin, V., Argillier, O., Menanteau, V., Barrie` re, Y., Mila, I., Pollet, B., and Lapierre, C. (2000). Relationship of cell wall composition to in vitro cell wall digestibility of maize inbred line stems. J. Sci. Food Agric. 80:574–580. 





Mejia-Guerra, M.K., Pomeranz, M., Morohashi, K., and Grotewold, E. (2012). From plant gene regulatory grids to network dynamics. Biochim. Biophys. Acta 1819:454–465. 





Mejia-Guerra, M., Li, W., Galeano, N.F., Vidal, M., Gray, J., Doseff, A.I., and Grotewold, E. (2015). Core promoter plasticity between maize tissues and genotypes contrasts with predominance of sharp transcription initiation sites. Plant Cell 27:3309–3320. 





Mitsuda, N., and Ohme-Takagi, M. (2008). NAC transcription factors NST1 and NST3 regulate pod shattering in a partially redundant manner by promoting secondary wall formation after the establishment of tissue identity. Plant J. 56:768–778. 





Mitsuda, N., and Ohme-Takagi, M. (2009). Functional analysis of transcription factors in Arabidopsis. Plant Cell Physiol. 50:1232–1248. 





Mitsuda, N., Seki, M., Shinozaki, K., and Ohme-Takagi, M. (2005). The NAC transcription factors NST1 and NST2 of Arabidopsis regulate secondary wall thickenings and are required for anther dehiscence. Plant Cell 17:2993–3006. 





Mitsuda, N., Iwase, A., Yamamoto, H., Yoshida, M., Seki, M., Shinozaki, K., and Ohme-Takagi, M. (2007). NAC transcription factors, NST1 and NST3, are key regulators of the formation of secondary walls in woody tissues of Arabidopsis. Plant Cell 19:270–280. 





Morohashi, K., and Grotewold, E. (2009). A systems approach reveals regulatory circuitry for Arabidopsis trichome initiation by the GL3 and GL1 selectors. PLoS Genet. 5:e1000396. 





Morohashi, K., Casas, M.I., Ferreyra, L.F., Mejia-Guerra, M.K., Pourcel, L., Yilmaz, A., Feller, A., Carvalho, B., Emiliani, J., Rodriguez, E., et al. (2012). A genome-wide regulatory framework identifies maize pericarp color1 controlled genes. Plant Cell 24:2745– 2764. 





Nakano, Y., Yamaguchi, M., Endo, H., Rejab, N.A., and Ohtani, M. (2015). NAC-MYB-based transcriptional regulation of secondary cell wall biosynthesis in land plants. Front. Plant Sci. 6:288. 





Niu, W., Lu, Z.J., Zhong, M., Sarov, M., Murray, J.I., Brdlik, C.M., Janette, J., Chen, C., Alves, P., Preston, E., et al. (2011). Diverse transcription factor binding features revealed by genome-wide ChIPseq in C. elegans. Genome Res. 21:245–254. 





Noguero, M., Atif, R.M., Ochatt, S., and Thompson, R.D. (2013). The role of the DNA-binding One Zinc Finger (DOF) transcription factor family in plants. Plant Sci. 209:32–45. 





Pautler, M., Eveland, A.L., LaRue, T., Yang, F., Weeks, R., Lunde, C., Je, B.I., Meeley, R., Komatsu, M., Vollbrecht, E., et al. (2015). FASCIATED EAR4 encodes a bZIP transcription factor that regulates shoot meristem size in maize. Plant Cell 27:104–120. 





Peng, X., Zhao, Y., Cao, J., Zhang, W., Jiang, H., Li, X., Ma, Q., Zhu, S., and Cheng, B. (2012). CCCH-type zinc finger family in maize: genomewide identification, classification and expression profiling under abscisic acid and drought treatments. PLoS One 7:e40120. 





Petroni, K., and Tonelli, C. (2011). Recent advances on the regulation of anthocyanin synthesis in reproductive organs. Plant Sci. 181:219–229. 





Reece-Hoyes, J.S., and Marian Walhout, A.J. (2012). Yeast one-hybrid assays: a historical and technical perspective. Methods 57:441–447. 





Reece-Hoyes, J.S., Diallo, A., Lajoie, B., Kent, A., Shrestha, S., Kadreppa, S., Pesyna, C., Dekker, J., Myers, C.L., and Walhout, A.J. (2011). Enhanced yeast one-hybrid assays for high-throughput 





gene-centered regulatory network mapping. Nat. Methods 8:1059– 1064. 





Rozen, S., and Skaletsky, H. (2000). Primer3 on the WWW for general users and for biologist programmers. Methods Mol. Biol. 132:365–386. 





Rubin, G., Tohge, T., Matsuda, F., Saito, K., and Scheible, W.R. (2009). Members of the LBD family of transcription factors repress anthocyanin synthesis and affect additional nitrogen responses in Arabidopsis. Plant Cell 21:3567–3584. 





Skirycz, A., Jozefczuk, S., Stobiecki, M., Muth, D., Zanor, M.I., Witt, I., and Mueller-Roeber, B. (2007). Transcription factor AtDOF4;2 affects phenylpropanoid metabolism in Arabidopsis thaliana. New Phytol. 175:425–438. 





Smykowski, A., Zimmermann, P., and Zentgraf, U. (2010). G-Box binding factor1 reduces CATALASE2 expression and regulates the onset of leaf senescence in Arabidopsis. Plant Physiol. 153:1321–1331. 





Sonbol, F.M., Fornale, S., Capellades, M., Encina, A., Tourino, S., Torres, J.L., Rovira, P., Ruel, K., Puigdomenech, P., Rigau, J., et al. (2009). The maize ZmMYB42 represses the phenylpropanoid pathway and affects the cell wall structure, composition and degradability in Arabidopsis thaliana. Plant Mol. Biol. 70:283–296. 





Soyano, T., Thitamadee, S., Machida, Y., and Chua, N.H. (2008). ASYMMETRIC LEAVES2-LIKE19/LATERAL ORGAN BOUNDARIES DOMAIN30 and ASL20/LBD18 regulate tracheary element differentiation in Arabidopsis. Plant Cell 20:3359–3373. 





Suzuki, N., Sejima, H., Tam, R., Schlauch, K., and Mittler, R. (2011). Identification of the MBF1 heat-response regulon of Arabidopsis thaliana. Plant J. 66:844–851. 





Takemaru, K., Harashima, S., Ueda, H., and Hirose, S. (1998). Yeast coactivator MBF1 mediates GCN4-dependent transcriptional activation. Mol. Cell. Biol. 18:4971–4976. 





Taylor-Teeples, M., Lin, L., de Lucas, M., Turco, G., Toal, T.W., Gaudinier, A., Young, N.F., Trabucco, G.M., Veling, M.T., Lamothe, R., et al. (2015). An Arabidopsis gene regulatory network for secondary cell wall synthesis. Nature 517:571–575. 





Thatcher, L.F., Kazan, K., and Manners, J.M. (2012). Lateral organ boundaries domain transcription factors: new roles in plant defense. Plant Signal. Behav. 7:1702–1704. 





Trivedi, P., Malina, R., and Barrett, S.R.H. (2015). Environmental and economic tradeoffs of using corn stover for liquid fuels and power production. Energy Environ. Sci. 8:1428–1437. 





Tsuda, K., Tsuji, T., Hirose, S., and Yamazaki, K. (2004). Three Arabidopsis MBF1 homologs with distinct expression profiles play roles as transcriptional co-activators. Plant Cell Physiol. 45:225–231. 





Vanholme, R., Morreel, K., Darrah, C., Oyarce, P., Grabber, J.H., Ralph, J., and Boerjan, W. (2012). Metabolic engineering of novel lignin in biomass crops. New Phytol. 196:978–1000. 





Ve´ lez-Bermu´ dez, I.C., Salazar-Henao, J.E., Fornale, S., Lopez-Vidriero, I., Franco-Zorrilla, J.M., Grotewold, E., Gray, J., Solano, R., Schmidt, W., Pages, M., et al. (2015). A MYB/ZML complex regulates wound-induced lignin genes in maize. Plant Cell 27:3245– 3259. 





Vicente-Carbajosa, J., Moose, S.P., Parsons, R.L., and Schmidt, R.J. (1997). A maize zinc-finger protein binds the prolamin box in zein gene promoters and interacts with the basic leucine zipper transcriptional activator Opaque2. Proc. Natl. Acad. Sci. USA 94:7685–7690. 





Vogt, T. (2010). Phenylpropanoid biosynthesis. Mol. Plant 3:2–20. 





Walhout, A.J. (2011). What does biologically meaningful mean? A perspective on gene regulatory network validation. Genome Biol. 12:109. 





Wallace, J.G., Larsson, S.J., and Buckler, E.S. (2014). Entering the second century of maize quantitative genetics. Heredity 112:30–38. 





Wang, P., Dudareva, N., Morgan, J.A., and Chapple, C. (2015). Genetic manipulation of lignocellulosic biomass for bioenergy. Curr. Opin. Chem. Biol. 29:32–39. 





Wei, K., Chen, J., Wang, Y., Chen, Y., Chen, S., Lin, Y., Pan, S., Zhong, X., and Xie, D. (2012). Genome-wide analysis of bZIP-encoding genes in maize. DNA Res. 19:463–476. 





Wen, W., Li, D., Li, X., Gao, Y., Li, W., Li, H., Liu, J., Liu, H., Chen, W., Luo, J., et al. (2014). Metabolome-based genome-wide association study of maize kernel leads to novel biochemical insights. Nat. Commun. 5:3438. 





Wen, W., Liu, H., Zhou, Y., Jin, M., Yang, N., Li, D., Luo, J., Xiao, Y., Pan, Q., Tohge, T., et al. (2016). Combining quantitative genetics approaches with regulatory network analysis to dissect the complex metabolism of the maize kernel. Plant Physiol. 170:136–146. 





Whitfield, T.W., Wang, J., Collins, P.J., Partridge, E.C., Aldred, S.F., Trinklein, N.D., Myers, R.M., and Weng, Z. (2012). Functional analysis of transcription factor binding sites in human promoters. Genome Biol. 13:R50. 





Xia, C., Wang, Y.J., Liang, Y., Niu, Q.K., Tan, X.Y., Chu, L.C., Chen, L.Q., Zhang, X.Q., and Ye, D. (2014). The ARID-HMG DNA-binding protein AtHMGB15 is required for pollen tube growth in Arabidopsis thaliana. Plant J. 79:741–756. 





Xu, C., Luo, F., and Hochholdinger, F. (2016). LOB domain proteins: beyond lateral organ boundaries. Trends Plant Sci. 21:159–167. 





Yamaguchi, M., Goue, N., Igarashi, H., Ohtani, M., Nakano, Y., Mortimer, J.C., Nishikubo, N., Kubo, M., Katayama, Y., Kakegawa, K., et al. (2010). VASCULAR-RELATED NAC-DOMAIN6 and VASCULAR-RELATED NAC-DOMAIN7 effectively induce transdifferentiation into xylem vessel elements under control of an induction system. Plant Physiol. 153:906–914. 





Yang, F., Ouma, W.Z., Li, W., Doseff, A.I., and Grotewold, E. (2016). Establishing the architecture of plant gene regulatory networks. Methods Enzymol. 576:251–304. 





Yilmaz, A., Nishiyama, M.Y., Garcia-Fuentes, B., Souza, G.M., Janies, D., Gray, J., and Grotewold, E. (2009). GRASSIUS: a platform for comparative regulatory genomics across the grasses. Plant Physiol. 149:171–180. 





Zhang, L., Zhao, H.K., Wang, Y.M., Yuan, C.P., Zhang, Y.Y., Li, H.Y., Yan, X.F., Li, Q.Y., and Dong, Y.S. (2015). Genome-wide identification and expression analysis of the CPP-like gene family in soybean. Genet. Mol. Res. 14:1260–1268. 





Zhang, J., Zhang, S., Li, H., Du, H., Huang, H., Li, Y., Hu, Y., Liu, H., Liu, Y., Yu, G., et al. (2016). Identification of transcription factors ZmMYB111 and ZmMYB148 involved in phenylpropanoid metabolism. Front. Plant Sci. 7:148. 





Zhao, Q., Wang, H., Yin, Y., Xu, Y., Chen, F., and Dixon, R.A. (2010). Syringyl lignin biosynthesis is directly regulated by a secondary cell wall master switch. Proc. Natl. Acad. Sci. USA 107:14496–14501. 





Zhong, R., and Ye, Z.-H. (2015). Secondary cell walls: biosynthesis, patterned deposition and transcriptional regulation. Plant Cell Physiol. 56:195–214. 





Zhong, R., Demura, T., and Ye, Z.H. (2006). SND1, a NAC domain transcription factor, is a key regulator of secondary wall synthesis in fibers of Arabidopsis. Plant Cell 18:3158–3170. 





Zhong, R., Richardson, E.A., and Ye, Z.H. (2007a). The MYB46 transcription factor is a direct target of SND1 and regulates secondary wall biosynthesis in Arabidopsis. Plant Cell 19:2776–2792. 





Zhong, R., Richardson, E.A., and Ye, Z.H. (2007b). Two NAC domain transcription factors, SND1 and NST1, function redundantly in regulation of secondary wall synthesis in fibers of Arabidopsis. Planta 225:1603–1611. 





Zhong, R., Lee, C., Zhou, J., McCarthy, R.L., and Ye, Z.H. (2008). A battery of transcription factors involved in the regulation of secondary cell wall biosynthesis in Arabidopsis. Plant Cell 20:2763– 2782. 





Zhong, R., Lee, C., McCarthy, R.L., Reeves, C.K., Jones, E.G., and Ye, Z.-H. (2011). Transcriptional activation of secondary wall biosynthesis by rice and maize NAC and MYB transcription factors. Plant Cell Physiol. 52:1856–1871. 





Zhou, J., Lee, C., Zhong, R., and Ye, Z.H. (2009). MYB58 and MYB63 are transcriptional activators of the lignin biosynthetic pathway during secondary cell wall formation in Arabidopsis. Plant Cell 21:248–266. 





Zhou, J., Zhong, R., and Ye, Z.H. (2014). Arabidopsis NAC domain proteins, VND1 to VND5, are transcriptional regulators of secondary wall biosynthesis in vessels. PLoS One 9:e105726. 

