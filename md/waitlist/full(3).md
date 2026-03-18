# Root microbiota drive direct integration of phosphate stress and immunity

Gabriel C astrillo1,2 *, Paulo José Pereira Lima Teixeira1,2 *, Sur H errera Paredes1,2,3*, Theresa F. Law1,2 , Laura de Lorenzo4†, Meghan E. Feltcher1,2 , Omri M. Finkel1,2 , Natalie W. Breakfield1,2 †, Piotr Mieczkowski5,6,7 , Corbin D. Jones1,3,5,6,7,8, Javier Paz-Ares4 & Jeffery L. Dangl1,2,3,7,8,9

Plants live in biogeochemically diverse soils with diverse microbiota. Plant organs associate intimately with a subset of these microbes, and the structure of the microbial community can be altered by soil nutrient content. Plant-associated microbes can compete with the plant and with each other for nutrients, but may also carry traits that increase the productivity of the plant. It is unknown how the plant immune system coordinates microbial recognition with nutritional cues during microbiome assembly. Here we establish that a genetic network controlling the phosphate stress response influences the structure of the root microbiome community, even under non-stress phosphate conditions. We define a molecular mechanism regulating coordination between nutrition and defence in the presence of a synthetic bacterial community. We further demonstrate that the master transcriptional regulators of phosphate stress response in Arabidopsis thaliana also directly repress defence, consistent with plant prioritization of nutritional stress over defence. Our work will further efforts to define and deploy useful microbes to enhance plant performance.

Plant organs create distinct physical and chemical environments that are colonized by specific microbial taxa1 . These can be modulated by the plant immune system2 and by soil nutrient composition3 . Phosphorus is present in the biosphere at high concentrations, but plants can only absorb orthophosphate (Pi), a form also essential for microbial proliferation4,5 and scarce in soil6 . Thus, plants possess adaptive phosphate starvation responses (PSRs) to manage low Pi availability that typically occurs in the presence of plant-associated microbes. Common strategies for increasing Pi uptake capacity include rapid extension of lateral roots foraging into topsoil where Pi accumulates7 and establishment of beneficial relationships with some soil microorganisms8,9 . For example, the capacity of a specific mutualistic fungus to colonize A. thaliana, hereafter Arabidopsis, roots is modulated by plant phosphate status, implying coordination between the PSR and the immune system8,10. Descriptions of pathogen exploitation of the coordination between the PSR and immune system are emerging11,12.

We demonstrate that Arabidopsis mutants with altered PSRs assemble atypical microbiomes, either in phosphate-replete ‘wild’ soil, or during in vitro colonization with a synthetic bacterial community (SynCom). This SynCom competes for phosphate with the plant and induces PSR in limiting phosphate. PSR in these conditions requires the master transcriptional regulator PHR1 and its weakly redundant paralogue, PHL1. The severely reduced PSR observed in phr1;phl1 mutants is accompanied by transcriptional changes in plant defence, leading to enhanced immune function. Negative regulation of immune system components by PHR1 is direct, as measured by target gene promoter occupancy, and functional, as validated by pathology phenotypes. Thus, PHR1 directly activates microbiome-enhanced response to phosphate limitation while repressing microbially driven plant immune system outputs.

# The root microbiome in plants with altered PSR

We linked PSR to the root microbiome by contrasting the root bacterial community of wild-type Arabidopsis Col-0 with three types of PSR mutants (Fig. 1a, b, Supplementary Text 1, Extended Data Fig. 1, Supplementary Table 1). PSR, historically defined in axenic seedlings and measured by Pi concentration in the plant shoot, is variable across these mutants. In replete Pi and axenic conditions, phr1 plants accumulate less free Pi than wild type13; pht1;1, pht1;1;pht1;4 and phf1 plants accumulate very low Pi levels and express constitutive PSR14,15; and pho2, nla and spx1;spx2 express diverse magnitudes of Pi hyperaccumulation16–18. We grew plants in a previously characterized wild soil19 that is not overtly phosphate deficient (Extended Data Fig. 2). Generally, the Pi concentration of PSR mutants grown in this wild soil recapitulated those defined in axenic conditions, except that phf1 and nla displayed the opposite phenotype to that observed in axenic agar, and phr1 accumulated the same Pi concentration as Col-0 (Fig. 1b). These results suggest that complex chemical conditions, soil microbes, or a combination of these can alter Pi metabolism in these mutants.

Bacterial root endophytic community profiles were consistent with previous studies2,19. Constrained ordination revealed significant differences between bacterial communities across the Pi accumulation gradient represented by these PSR mutants $5 . 3 \%$ constrained variance, canonical analysis of principal coordinates) (Fig. 1c). Additionally, canonical analysis of principal coordinates confirmed that phr1 and spx1;spx2 plants carried different communities, as evidenced by their separation on the first three ordination axes, and that phf1 was the most affected of the Pi-transport mutants (Fig. 1c). Specific bacterial taxa had differential abundances inside the roots of mutant plants compared to wild-type. Notably, we found that the enrichment and depletion profiles were better explained by PSR mutant signalling type, rather than the

![](images/f31fa6fe80d3c8dc9eecab4bc30cf8a71e568901c95d2f9f16fc5d213375d9c8.jpg)  
a

![](images/3948a83cd52b082b4489e91140f6fb48d7ca45f523b3ee3dd439d8200672494e.jpg)

![](images/9af42e9d49037a70e498c9449e75551add74be5141c5d4954de4b8c8f5cdc315.jpg)  
c

![](images/aa15a20035f6cadc2d8b90e3ae8e6d825f92614d4efc0ff16ef40417f2a29e87.jpg)

![](images/f7687ec9ae0514bd9824099e4d51842c39b8c36feb7a7a006d0a60c9464df9cf.jpg)  
d   
Figure 1 | PSR mutants assemble an altered root microbiota. a, Diagram of PSR regulation in Arabidopsis. Red and blue stripes indicate whether these mutants hyper- or hypo-accumulate Pi, respectively, in axenic, Pi-replete conditions. The master PSR regulator PHR1 is a Myb-CC family transcription factor13 bound under phosphate-replete conditions by the negative regulators SPX1 and SPX2 in the nucleus18. During PSR, PHR1 is released from SPX and regulates genes whose products include highaffinity phosphate transporters (PHT1;1 and PHT1;4)13. Transporter accumulation at the plasma membrane is controlled by PHF115, while PHO2 and NLA mediate PHT1 degradation16,17. b, Pi content normalized by the shoot fresh weight in mg in plant genotypes grown in Mason Farm wild soil19 in growth chambers (16-h dark/8-h light regime, $2 1 ^ { \circ } \mathrm { C }$ day/ $1 8 ^ { \circ } \mathrm { C }$ night for 7 weeks). Statistical significance was determined by ANOVA, controlling for experiment (indicated by point shape); genotype grouping is based on a post hoc Tukey test, and is indicated by letters at the top; genotypes with the same letter are indistinguishable at $9 5 \%$ confidence. Biological replicate numbers are: Col-0 ${ \mathit { n } } = 1 2$ ), pht1;1 $\ R = 1 3$ ), pht1;1;pht1;4 $[ n = 1 4 ]$ ), phf1 $( n = 9 )$ ), nla $( n = 1 3$ ), pho2 ${ \bf \zeta } _ { n } = 1 1$ ), phr1 $( n = 1 4 )$ ) and spx1;spx2 ${ \mathit { n } } = 1 1$ ) distributed across two independent experiments. c, Constrained ordination of root microbiome composition showing the effect of plant genotype: phr1 separates on the first two axes, spx1;spx2 on the third axis and phf1 on the fourth axis. Ellipses show the parametric smallest area around the mean that contains $5 0 \%$ of the probability mass for each genotype. Biological replicate numbers are: Col-0 $( n = 1 7 )$ ), pht1;1 $n = 1 8 ,$ ), pht1;1;pht1;4 $( n = 1 7 )$ ), phf1 $( n = 1 3$ ), nla $( n = 1 6 )$ ), pho2 $( n = 1 6 )$ ), phr1 $( n = 1 8 )$ ) and spx1;spx2 $\mathrm { { \bar { \it { n } } = 1 4 } }$ ) distributed across two independent experiments. d, Table of $P$ values from Monte Carlo pairwise comparisons between mutants at the OTU level. A significant $P$ value (cyan) indicates that two genotypes are more similar than expected by chance.

capacity of the mutant for Pi accumulation: all of the Pi-transportrelated mutants had a similar effect on the root microbiome, and the antagonistic PSR regulators phr1 and spx1;spx2 each exhibited unique patterns (Fig. 1a, d, Extended Data Fig. 1f, g). Importantly, we observed this pattern at a low taxonomic level $9 7 \%$ identity operational taxonomic unit (OTU) (Fig. 1d), but not at a higher taxonomic level (family, Extended Data Fig. 1g). This suggests that closely related groups of bacteria have differential colonization patterns on the same host genotypes. Our results indicate that PSR components influence root microbiome composition in plants grown in a phosphate-replete wild soil, leading to alteration of the abundance of specific microbes across diverse levels of Pi accumulation representing diverse magnitudes of PSR.

# PSR in a microcosm reconstitution

Our observations in a wild soil suggested complex interplay between PSR and the presence of a microbial community. Thus, we deployed a defined but complex bacterial SynCom of 35 taxonomically diverse, genome-sequenced bacteria isolated from the roots of Brassicaceae (27 of which are from Arabidopsis) and two wild soils. This SynCom approximates the phylum level distribution observed in wild-type root endophytic compartments (Extended Data Fig. 3, Supplementary Tables 1, 2). We inoculated seedlings of Col-0, phf1 and the double mutant phr1;phl1 (a redundant paralogue of phr1 (ref. 13)) grown

on agar plates with low or high Pi concentrations (Supplementary Text 2). Twelve days later, we noted that the SynCom had a negative effect on shoot Pi accumulation of Col-0 plants grown on low Pi, but not on plants grown on replete phosphate (Fig. 2a). As expected, both PSR mutants accumulated less Pi than Col-0; the SynCom did not rescue this defect. Thus, in this microcosm, plant-associated microbes drive a context-dependent competition with the plant for Pi.

We sought to establish whether PSR was activated by the SynCom. We generated a literature-based core set of 193 PSR transcriptional markers and explored their expression in transcriptomic experiments (Extended Data Fig. 4a, b, Supplementary Table 3). In axenic low Pi conditions, only the constitutive Pi-stressed mutant phf1 exhibited induction of these PSR markers. By contrast, Col-0 plants expressed only a marginal induction of PSR markers compared to those plants grown at high Pi (Fig. 2b). This is explained by the purposeful absence of sucrose, a key component for the PSR induction in vitro20 (Supplementary Text 2, Extended Data Fig. 5) that cannot be used in combination with bacterial SynCom colonization protocols. Notably, the SynCom greatly enhanced the canonical transcriptional response to Pi starvation in Col-0 (Fig. 2b); this was dependent on PHR1 and PHL1 (Fig. 2b, Extended Data Fig. 4b). Various controls validated these conclusions (Supplementary Text 2, Extended Data Figs 4–6). Importantly, shoots of plants pre-colonized with SynCom on 0 or $5 0 \mu \mathrm { M }$ Pi, but

![](images/d8b1b54244880655607bcec95d12b29c30281e64fbda46a5b27069710d551a66.jpg)

![](images/69573643a195d03be8349aedeb730c011f306d3eaf831ebef24293567254b09f.jpg)

![](images/2d301a33d4967f3489543293d07c3963efd5a19617d7f7cf9ecc06b3228db132.jpg)

![](images/f8d0527f5c2adcacdb08c218c5f6b9a81b3ed34f0a03240693113c16a96b660a.jpg)

![](images/54f42c679fcefd254e86b2b381d3f15ea6f3fd9d43ac1fdf7056067b5ca4424b.jpg)

![](images/cf6737ef1556d79f196048a2a819097c575046d991a8f5ac2c5547453b82053b.jpg)

![](images/b19a69778226e51ae25dc5bc247aec02ab1a1c6aba6832977340f6e113890012.jpg)  
Figure 2 | A bacterial SynCom differentially colonizes PSR mutants. a, Pi concentration in shoots of plants grown on different Pi regimens with or without the SynCom. Biological replicate numbers are: Col-0 ( ${ \dot { n } } = 1 6$ $6 2 5 \mu \mathrm { M }$ Pi), 24 ( $6 2 5 \mu \mathrm { M }$ $\mathrm { P i } +$ SynCom), 12 $5 0 \mu \mathrm { M }$ Pi), 24 $( 5 0 \mu \mathrm { M }$ $\mathrm { P i } + \mathrm { S y n C o m } )$ ), phf1 $n = 1 6$ , 18, 12, 24) and phr1;phl1 $n = 1 6$ , 18, 12, 24) from three independent experiments. Statistical significance was determined via ANOVA while controlling for experiment, and the letters indicate the results of a post hoc Tukey test. Groups of samples that share at least one letter are statistically indistinguishable. b, Expression levels of 193 core PSR genes. The $z$ -scores of RPKM expression values are shown. Boxes at bottom indicate presence/absence of SynCom and Pi at the concentration indicated. This labelling is maintained throughout. Data are the average of 4 biological replicates. c, Functional activation of PSR by the SynCom. Plants were grown on different Pi levels with or without the SynCom and subsequently transferred to full Pi (1 mM). The Pi concentration in shoots was measured at the time of transfer and at 1, 2, 3 days thereafter. Relative Pi increase represents the normalized difference in Pi content at day n with respect to the Pi content on the day of transfer to 1 mM Pi. Absolute Pi concentration values are available in Supplementary Table 4. For all Pi concentrations and SynCom treatments,

not on $6 2 5 \mu \mathrm { M }$ Pi, expressed 20- to 40-fold increases in normalized Pi concentration when transferred to full Pi (1 mM) conditions; non-precolonized plants did not exhibit this response (Fig. 2c, Supplementary Table 4). This demonstrates functional PSR activation by the SynCom. We thus propose that the transcriptional response to low Pi induced by our SynCom reflects an integral microbial element of normal PSR in complex biotic environments.

We evaluated agar- and root-associated microbiomes of plants grown with the SynCom (Supplementary Text 3, Fig. 2d, e, Extended Data Fig. 7e, f, Supplementary Table 5). In line with results from plants grown in wild soil, we found that PSR mutants failed to assemble a wild-type SynCom microbiome (Fig. 2f). Some strains were differentially abundant across PSR mutants phf1 and phr1;phl1 (Fig. 2e, f, Extended Data Fig. 7c), Pi concentration (Fig. 2g, Extended Data Fig. 7d), or sample fraction (Extended Data Fig. 7b, e, f). These results established a microcosm reconstitution system to study plant PSR under chronic competition with plant-associated microbes and allowed us to confirm that the tested PSR mutants influence composition of the root microbiome.

$n = 6$ at day 0, and $n = 9$ at all other time points, distributed across two independent experiments. d, PCoA of SynCom experiments showing that Agar and Root samples are different from starting inoculum. Biological replicate numbers are: Inoculum $( n = 4 )$ , Agar $( n = 1 2 )$ ) and Root $\left( n = 3 5 \right.$ ) across two independent experiments. e, Heat map showing per cent abundances of SynCom isolates (columns) in all samples (rows). Strain name colours correspond to phylum (bottom left). Within each block, samples are sorted by experiment. For each combination of genotype and Pi level, there are $n = 6$ biological replicates evenly distributed across two independent experiments, except for Inoculum for which there are $n = 4$ technical replicates evenly distributed across two independent experiments. f, g, Constrained ordination showing the effect of plant genotype (f) and media Pi concentration effect on the root communities (g). The proportion of total variance explained (constrained) by each variable is indicated on top of each plot; for g, remaining unconstrained ordination was subjected to multi-dimensional scaling (MDS); the first MDS axis (MDS1) is shown. For f and g, biological replicate numbers are: Col-0 $( n = 1 2 )$ ), phf1 ${ \mathit { n } } = 1 1 { \mathit { n } }$ ), phr1;phl1 $( n = 1 2$ ), $5 0 \mu \mathrm { M }$ Pi $( n = 2 4 )$ ) and $6 2 5 \mu \mathrm { M }$ Pi $\cdot n = 2 3 )$ ) distributed across two independent experiments.

Coordination between PSR and immune system output We noted that phr1;phl1 and phf1 differentially activated transcriptional PSR in the presence of our SynCom (Fig. 2b). Therefore, we investigated the transcriptomes of plants growing with the SynCom to understand how these microbes activate PHR1-dependent PSR. We identified differentially expressed genes (DEGs) that responded to either low Pi, presence of the SynCom, or the combination of both (hereafter PSR-SynCom DEGs) (Supplementary Text 4, Extended Data Fig. 8a, b, Supplementary Table 6). Hierarchical clustering (Fig. 3a, Supplementary Table 7) revealed gene sets (c1, c2, c7 and c10) that were more strongly activated in Col-0 than in phr1 or phr1;phl1. These clusters contained most of the core PSR markers regulated by PHR1 (Fig. 3b). They were also enriched in PHR1 direct targets identified in an independent ChIP–seq experiment (Fig. 3c, Supplementary Table 8), PHR1 promoter binding motifs (Extended Data Fig. 4c), and genes involved in biological processes related to PSR (Fig. 3d, Supplementary Table 9). PHR1 unexpectedly contributed to transcriptional regulation of plant immunity. Five of the twelve clusters (Fig. 3a, c3, c6, c7, c8 and c11) were enriched in genes related to plant immune system

![](images/f4009b91d67a472ee41045956539cfe2bde0babb8699d0fdf523736a01cb73ab.jpg)

![](images/5ee3689afc0dc562e94c2cc74873e13f54bac70632c8a79d501bf83deb334467.jpg)

![](images/daab471d464ee3e46e3ab9defa4fc588e0b42a585911a97d79bd36429be1c085.jpg)

![](images/1f5524b63188098ee1cc6dbd39574fe240b813ec8a32a5e991817ef925b5baae.jpg)

![](images/7ad07717f500e9bbe5ee5073ddfe922327858a966d6bbc057225a010b067221a.jpg)  
Figure 3 | PHR1 mediates interaction of the PSR and plant immune system outputs. a, Hierarchical clustering of 3,257 genes that were differentially expressed in the RNA-seq experiment. Columns on the right indicate genes that are core PSR markers (‘core’ lane) or had a PHR1 binding peak (‘PHR1 ChIP’ lane). b, Proportion of PSR marker genes per cluster. c, Proportion of PHR1 direct targets genes per cluster. The red line in b and c denotes the proportion of genes in the whole Arabidopsis genome that contain the analysed feature. Asterisk denotes significant enrichment or depletion $\lceil P \leq 0 . 0 5$ ; hypergeometric test). d, Summary of the Gene Ontology enrichment analysis for each of the twelve clusters. The enrichment significance is shown as $- \mathrm { l o g } _ { 2 } [ \mathrm { F D R } ]$ ]. White means no   
enrichment. The complete results are in Supplementary Table 9. e, The set of genes bound by PHR1 (At4g28610) in ChIP–seq experiments is enriched in genes that are upregulated by BTH/SA and/or MeJA. Red nodes are core PSR marker genes. Exp., expected; obs., observed. f, Example of genes bound by PHR1 and differentially expressed in our experiment. PSR marker genes (top) and JA response (middle) are more expressed in wild-type plants, whereas SA-responsive genes (bottom) exhibit higher transcript levels in phr1 and phr1 phl1. The heat maps show the average measurement of ten biological replicates for Col-0 and phr1 and six for phr1;phl1. The colour key (blue to red) related to a, and f, represents gene expression (RPKM) as $z$ -scores.

output; four of these were over-represented for jasmonic acid (JA) and/or salicylic acid (SA) pathway markers (Fig. 3d, c3, c7, c8, and c11; Supplementary Table 9) and three of these four were enriched for PHR1 direct targets (Fig. 3c). SA and JA are plant hormone regulators of immunity and at least SA modulates Arabidopsis root microbiome composition2 .

To explore PHR1 function in the regulation of plant immunity further, we generated transcriptomic time-course data for treatmentmatched Col-0 seedlings following application of methyl jasmonate (MeJA) or the SA analogue benzothiadiazole (BTH; Supplementary Table 10). We found a considerable over-representation of SA- and JA-activated genes among the PSR-SynCom DEGs (468 versus 251 expected for SA, and 165 versus 80 expected for JA; $P { < } 0 . 0 0 0 1$ , hypergeometric test) (Extended Data Fig. 8c–h, Supplementary Table 7). A large proportion of SA-responsive genes were more strongly expressed in phr1 and phr1;phl1 than in Col-0; these were strongly enriched for classical SA-dependent defence genes (Extended Data Fig. 8d, e). A second group of SA-responsive genes with lower expression in phr1 and phr1;phl1 than in Col-0 lacked classical SA-dependent defence genes and were weakly enriched for genes that probably contribute to PSR (Extended Data Fig. 8d). By contrast, most JA-responsive genes exhibited lower expression in phr1 and phr1;phl1 (Extended Data Fig. 8g, h), including a subset of 18 of 46 genes known or predicted to mediate biosynthesis of defence-related glucosinolates21 (Extended Data Fig. 8i). This agrees with the recent observation that phr1 exhibited decreased glucosinolate levels during Pi starvation22. Analyses of

SA- and JA-upregulated genes revealed enrichment of direct PHR1 targets (Fig. 3e), consistent with the converse observation that some PHR1-regulated clusters enriched in direct targets were also enriched in defence genes (Fig. 3c, d). Many of the SA- and JA-responsive genes were PSR-SynCom DEGs (Fig. 3f, Extended Data Fig. 8c–h, Supplementary Table 7). Thus, PHR1 directly regulates an unexpected proportion of the plant immune system during PSR triggered by our SynCom.

# PHR1 integrates plant immune system output and PSR

We tested whether PHR1 also controls the expression of plant defence genes under conditions typically used to study PSR (axenic growth, sucrose present). We performed RNA sequencing (RNA-seq) in response to low Pi in these conditions and identified 1,482 DEGs in Col-0 and 1,161 DEGs in phr1;phl1 (Fig. 4a, b, Extended Data Fig. 9, Supplementary Table 11). A significant number of the BTH/ SA-activated genes were also upregulated in phr1;phl1, but not in Col-0 in response to low Pi (Fig. 4a, b, Supplementary Table 12). A large number of these overlapped with the defence genes induced in phr1;phl1 by our SymCom (Fig. 4c, red ellipse, 113 out of $3 3 7 = 3 3 \%$ ; clusters c3 and c8 from Fig. 3a). At least 14 out of 113 are direct PHR1 targets (Supplementary Table 12).

To underscore the role of PHR1 in the regulation of response to microbes, we analysed the transcriptional profile of Col-0 and phr1;phl1 plants exposed to the flagellin peptide $\mathrm { { \dot { f } l g 2 2 ^ { 2 3 } } }$ . We subjected the plants to chronic exposure to flg22 to mimic the condition of

![](images/8792ada183a94172576f3aa6d1c6adcc4e71bc2d98ec6cf78368fdfd86352d45.jpg)  
a

![](images/8b4dae76fbaa3c369cb3b6ab6c58e90a32ce292bd5b122b5c3f70f6ac9d6b7c7.jpg)  
c

![](images/3c99129aa635743f622518447cce8dba3c26767944554d08822ae24780bf3b43.jpg)

![](images/f573b157cab8471dc8be2e13057f7f0c56cf12966f4aa1e8ba482ac46dbd5977.jpg)

![](images/1c7313ca72eadc3aadf33b574b3cb3c52b4cbd56a2e73664d5f557ce49ec4888.jpg)

![](images/de83dd05df09dd70120f1bc35d5c08597e4f71fcf18f79b55e91fe71dab0e3e1.jpg)

![](images/4b94d609ea9517b64efd39e714bc54138f21927b590741a044e97a2a087e610d.jpg)

![](images/85537381b4bc61a063b060424ff0d0856682278172d39f5e19d4cf0185234760.jpg)  
e

![](images/92285fd73fcfe28d859709334972a26fc8b5e5f9a6d6e590a8a518eb71cdef4a.jpg)  
f   
Figure 4 | Loss of PHR1 activity results in enhanced activation of plant immunity. a, Venn diagram (left) showing the overlap between genes upregulated and downregulated in Col-0 and phr1;phl1 in response to phosphate starvation. Gene ontology enrichment (right) analyses indicate that defence-related genes are upregulated exclusively in phr1;phl1 (see Supplementary Table 14). Colour key (white to red) represents the gene ontology enrichment significance shown as $- \mathrm { l o g } _ { 2 } [ \mathrm { F D R } ]$ . b, Fold-change of genes differentially expressed in Col-0, phr1;phl1 or in both genotypes in response to phosphate starvation. Columns on the right indicate whether each gene is also upregulated by MeJA or BTH/SA. c, Venn diagram showing the overlap among genes upregulated in Col-0 and phr1;phl1 during a typical PSR (from a) and the defence genes upregulated in phr1;phl1 in response to the SynCom (from Fig. 3a; clusters c3 and c8). The red ellipse indicates defence genes that were upregulated in phr1;phl1 during classical PSR and during PSR triggered by the SynCom; yellow ellipse indicates upregulated genes under the same conditions. P values refer to enrichment results using hypergeometric tests. d, phr1;phl1 exhibits enhanced transcriptional activation of PTI   
marker genes differentially expressed following chronic exposure to flg22 (Extended Data Fig. 9). Averaged from six biological replicates. e, phr1 exhibits enhanced disease resistance to the biotrophic oomycete pathogen Hyaloperonospora arabidopsidis isolate Noco2. Colour gradient displays the number of asexual sporangiophores (Sp) per cotyledon from resistant (green) to susceptible (red); the mean number of sporangiophores per cotyledon is noted above each bar. The experiment was performed at least five times with similar results. f, phr1 mutants exhibit enhanced disease resistance to the hemibiotrophic bacterial pathogen Pseudomonas syringae DC3000. The coi1-16 $\scriptstyle \left. { n = 9 } \right.$ (day zero), 13 (day three)) and sid2-1 $n = 1 6$ , 20) mutants were controls for resistance and susceptibility, respectively. Col-0 ( ${ \mathrm { ? } n = 1 6 }$ , 20), phr1 $n = 1 7 , 2 0$ ), phr1;phl1 ${ \dot { n } } = 1 6$ , 20) and control plants were inoculated under phosphate replete conditions in non-axenic potting soil (Extended Data Fig. 2). The data are derived from three independent experiments. Statistical comparisons among genotypes were one-way ANOVA tests followed by a post hoc Tukey analysis; genotypes with the same letter above the graph are statistically indistinguishable at $9 5 \%$ confidence.

plants in contact with a microbiome. We found that phr1;phl1 plants displayed higher expression of flg22-responsive genes23 than Col-0, independent of phosphate status (Supplementary Text 5, Fig. 4d, Extended Data Fig. 9a, b, Supplementary Tables 11, 13). This indicates that PHR1 negatively regulates the immune response triggered by flg22.

On the basis of our transcriptome data, we hypothesized that phr1;phl1 would express an altered response to pathogen infection. The phr1 and phr1;phl1 mutants exhibited enhanced disease resistance against both the oomycete pathogen Hyaloperonospora arabidopsidis isolate Noco2, and the bacterial pathogen Pseudomonas syringae DC3000 (Fig. 4e, f). Collectively, these results confirm the role of PHR1 as a direct integrator of PSR and the plant immune system.

# Conclusions

Plant responses to phosphate stress are inextricably linked to life in microbe-rich soil. We demonstrate that genes controlling PSR contribute to assembly of a normal root microbiome. Our SynCom enhanced the activity of PHR1, the master regulator of the PSR, in plants grown under limited phosphate. This led to our discovery that PHR1 is a direct regulator of a functionally relevant set of plant immune

system genes. Despite being required for the activation of JA-responsive genes during $\mathrm { P S } \bar { \mathrm { R } } ^ { 2 4 }$ , we found that PHR1 is unlikely to be a general regulator of this response (Extended Data Fig. 9c–e, Supplementary Table 12). Rather, PHR1 may fine-tune JA responses in specific biological contexts.

We demonstrate that PSR and immune system outputs are directly integrated by PHR1 (and, probably, PHL1). We provide a mechanistic explanation for previous disparate observations that PSR and defence regulation are coordinated and implications that PHR1 is the key regulator8,11,12,24. We provide new insight into the intersection of plant nutritional stress response, immune system function, and microbiome assembly and maintenance; systems that must act simultaneously and coordinately in natural and agricultural settings. Our findings will drive investigations aimed at utilizing microbes to enhance efficiency of phosphate use.

Online Content Methods, along with any additional Extended Data display items and Source Data, are available in the online version of the paper; references unique to these sections appear only in the online paper.

received 21 September 2016; accepted 25 January 2017.

Published online 15 March 2017.

1. Bulgarelli, D., Schlaeppi, K., Spaepen, S., Ver Loren van Themaat, E. & Schulze-Lefert, P. Structure and functions of the bacterial microbiota of plants. Annu. Rev. Plant Biol. 64, 807–838 (2013).   
2. Lebeis, S. L. et al. Salicylic acid modulates colonization of the root microbiome by specific bacterial taxa. Science 349, 860–864 (2015).   
3. Hacquard, S. et al. Microbiota and host nutrition across plant and animal kingdoms. Cell Host Microbe 17, 603–616 (2015).   
4. Zhu, Q., Riley, W. J., Tang, J. & Koven, C. D. Multiple soil nutrient competition between plants, microbes, and mineral surfaces: model development, parameterization, and example applications in several tropical forests. Biogeosciences 13, 341–363 (2016).   
5. Richardson, A. E. & Simpson, R. J. Soil microorganisms mediating phosphorus availability update on microbial phosphorus. Plant Physiol. 156, 989–996 (2011).   
6. Raghothama, K. G. Phosphate acquisition. Annu. Rev. Plant Physiol. Plant Mol. Biol. 50, 665–693 (1999).   
7. Lambers, H., Martinoia, E. & Renton, M. Plant adaptations to severely phosphorus-impoverished soils. Curr. Opin. Plant Biol. 25, 23–31 (2015).   
8. Hiruma, K. et al. Root endophyte Colletotrichum tofieldiae confers plant fitness benefits that are phosphate status dependent. Cell 165, 464–474 (2016).   
9. Harrison, M. J. Cellular programs for arbuscular mycorrhizal symbiosis. Curr. Opin. Plant Biol. 15, 691–698 (2012).   
10. Hacquard, S. et al. Survival trade-offs in plant roots during colonization by closely related beneficial and pathogenic fungi. Nat. Commun. 7, 11362 (2016).   
11. Lu, Y. T. et al. Transgenic plants that express the phytoplasma effector SAP11 show altered phosphate starvation and defense responses. Plant Physiol. 164, 1456–1469 (2014).   
12. Zhao, H. et al. Small RNA profiling reveals phosphorus deficiency as a contributing factor in symptom expression for citrus huanglongbing disease. Mol. Plant 6, 301–310 (2013).   
13. Bustos, R. et al. A central regulatory system largely controls transcriptional activation and repression responses to phosphate starvation in Arabidopsis. PLoS Genet. 6, e1001102 (2010).   
14. Shin, H., Shin, H. S., Dewbre, G. R. & Harrison, M. J. Phosphate transport in Arabidopsis: Pht1;1 and Pht1;4 play a major role in phosphate acquisition from both low- and high-phosphate environments. Plant J. 39, 629–642 (2004).   
15. González, E., Solano, R., Rubio, V., Leyva, A. & Paz-Ares, J. PHOSPHATE TRANSPORTER TRAFFIC FACILITATOR1 is a plant-specific SEC12-related protein that enables the endoplasmic reticulum exit of a high-affinity phosphate transporter in Arabidopsis. Plant Cell 17, 3500–3512 (2005).   
16. Huang, T. K. et al. Identification of downstream components of ubiquitinconjugating enzyme PHOSPHATE2 by quantitative membrane proteomics in Arabidopsis roots. Plant Cell 25, 4044–4060 (2013).   
17. Lin, W. Y., Huang, T. K. & Chiou, T. J. Nitrogen limitation adaptation, a target of microRNA827, mediates degradation of plasma membrane-localized phosphate transporters to maintain phosphate homeostasis in Arabidopsis. Plant Cell 25, 4061–4074 (2013).   
18. Puga, M. I. et al. SPX1 is a phosphate-dependent inhibitor of Phosphate Starvation Response 1 in Arabidopsis. Proc. Natl Acad. Sci. USA 111, 14947–14952 (2014).   
19. Lundberg, D. S. et al. Defining the core Arabidopsis thaliana root microbiome. Nature 488, 86–90 (2012).   
20. Karthikeyan, A. S. et al. Phosphate starvation responses are mediated by sugar signaling in Arabidopsis. Planta 225, 907–918 (2007).

21. Schweizer, F. et al. Arabidopsis basic helix-loop-helix transcription factors MYC2, MYC3, and MYC4 regulate glucosinolate biosynthesis, insect performance, and feeding behavior. Plant Cell 25, 3117–3132 (2013).   
22. Pant, B. D. et al. Identification of primary and secondary metabolites with phosphorus status-dependent abundance in Arabidopsis, and of the transcription factor PHR1 as a major regulator of metabolic changes during phosphorus limitation. Plant Cell Environ. 38, 172–187 (2015).   
23. Rallapalli, G. et al. EXPRSS: an Illumina based high-throughput expressionprofiling method to reveal transcriptional dynamics. BMC Genomics 15, 341 (2014).   
24. Khan, G. A., Vogiatzaki, E., Glauser, G. & Poirier, Y. Phosphate deficiency induces the jasmonate pathway and enhances resistance to insect herbivory. Plant Physiol. 171, 632–644 (2016).

Supplementary Information is available in the online version of the paper.

Acknowledgements Support by NSF INSPIRE grant IOS-1343020 and DOE-USDA Feedstock Award DE-SC001043 to J.L.D. S.H.P. was supported by NIH Training Grant T32 GM067553-06 and is a Howard Hughes Medical Institute International Student Research Fellow. P.J.P.L.T. was supported by The Pew Latin American Fellows Program in the Biomedical Sciences. J.L.D. is an Investigator of the Howard Hughes Medical Institute, supported by the HHMI and the Gordon and Betty Moore Foundation (GBMF3030). M.E.F. and O.M.F. are supported by NIH NRSA Fellowships F32-GM112345-02 and F32-GM117758-01, respectively. N.W.B. was supported by NIH NRSA Fellowship F32-GM103156. J.P.-A. is funded by the Spanish Ministry of Economy and Competitiveness (MINECO BIO2014-60453-R and EUI2008- 03748). We thank S. Barth and E. Getzen for technical assistance, the Dangl laboratory microbiome group for useful discussions and S. Grant, D. Lundberg, F. El Kasmi, P. Schulze-Lefert and his colleagues for critical comments on the manuscript. Supplement contains additional data. Raw sequence data are available at the EBI Sequence Read Archive accession PRJEB15671 for microbiome 16S profiling, and at the Gene Expression Omnibus accessions GSE87339 for transcriptomic experiments. J.L.D. is a co-founder of, and shareholder in, and S.H.P. collaborates with, AgBiome LLC, a corporation whose goal is to use plant-associated microbes to improve plant productivity.

Author Contributions G.C., P.J.P.L.T., S.H.P. and J.L.D. designed the project, G.C., S.H.P., T.F.L. and M.E.F. set up the experiments, collected samples and organized construction of 16S sequencing libraries. G.C. and T.F.L. performed control experiments related with PSR induced by the SynCom. G.C., N.W.B., M.E.F. and T.F.L. set up the experiments, collected samples and isolated RNA. P.J.P.L.T. organized, performed construction of RNA-seq libraries and analysed RNA-seq data. S.H.P. analysed 16S sequencing data. S.H.P. and P.J.P.L.T. oversaw data deposition. G.C., T.F.L. and P.J.P.L.T. performed pathology experiments. G.C., P.J.P.L.T., S.H.P., T.F.L., O.M.F. and J.L.D. analysed data and created figures. L.d.L. performed the ChIP–seq experiment. C.D.J. and P.M. advised on sequencing process and statistical methods. G.C., P.J.P.L.T., S.H.P. and J.L.D. wrote the manuscript with input from O.M.F., C.D.J. and J.P.-A.

Author Information Reprints and permissions information is available at www.nature.com/reprints. The authors declare no competing financial interests. Readers are welcome to comment on the online version of the paper. Correspondence and requests for materials should be addressed to J.L.D. (dangl@email.unc.edu).

Reviewer Information Nature thanks P. Finnegan and the other anonymous reviewer(s) for their contribution to the peer review of this work.

# Metho ds

Data reporting. For the wild soil and synthetic community profiling studies, we utilized our previously published results (refs 2, 19) that showed that 7 and 5 samples for wild soil and synthetic community experiments were sufficient (see ‘Statistical analysis’).

For wild soil experiments, we performed spatial randomization based on true random numbers. Periodical re-shuffling in the growth chambers was also performed (see ‘Census study experimental procedures’). For DNA extraction, we randomly assigned samples to plates and wells within plates using a physical method. The location of samples determined this way was maintained through the library preparation and sequencing steps (see ‘Census study experimental procedures’). The investigators were not blinded to allocation during experiments and outcome assessment.

Census study experimental procedures. For experiments in wild soil, we collected the top-soil (approximately $2 0 \mathrm { c m }$ ) from a site free of pesticide and fertilizer at Mason Farm (North Carolina, USA; $+ 3 5 ^ { \circ } 5 3 ^ { \prime } 3 0 . 4 0 ^ { \prime \prime }$ , $- 7 9 ^ { \circ } 1 ^ { \prime } 5 . 3 7 ^ { \prime \prime } ) ^ { 1 9 }$ . Soil was dried, crushed and sifted to remove debris. To improve drainage, soil was mixed 2:1 volume with autoclaved sand. Square pots $2 \times 2$ inch square) were filled with the soil mixture and used to grow plants. Soil micronutrient analysis is published in ref. 19.

All Arabidopsis thaliana mutants used in this study were in the Columbia (Col-0) background (Supplementary Table 16). All seeds were surface-sterilized with $7 0 \%$ bleach, $0 . 2 \%$ Tween-20 for 8 min, and rinsed $3 \times$ with sterile distilled water to eliminate any seed-borne microbes on the seed surface. Seeds were stratified at $4 ^ { \circ } \mathrm { C }$ in the dark for 2 days.

To determine the role of phosphate starvation response in controlling microbiome composition, we analysed five mutants related to the Pi-transport system (pht1;1, pht1;1;pht1;4, phf1, nla and pho2) and two mutants directly involved in the transcriptional regulation of the Pi-starvation response (phr1 and spx1;spx2). All these genes are expressed in roots13–18.

Seeds were germinated in sterile square pots filled with MF soil prepared as described above. We also used pots without plants as ‘bulk soil’ controls. All pots, including controls, were watered from the top with non-sterile distilled water to avoid chlorine and other tap water additives two times a week. Plants were grown in growth chambers with a 16-h dark/8-h light regime at $2 1 ^ { \circ } \mathrm { C }$ day $1 8 ^ { \circ } \mathrm { C }$ night for 7 weeks. In all experiments, pots with plants of different genotypes were randomly placed in trays according to true random numbers derived from atmospheric noise; we obtained those numbers from http://www.random.org. We positioned trays in the growth chamber without paying attention to the pots they contained, and we periodically reshuffled them without paying attention to the pot labels.

Plants and bulk soil controls were harvested and their endophytic compartment microbial communities isolated as described19. DNA extraction was performed using 96-well-format MoBio PowerSoil Kit (MOBIO Laboratories) following the manufacturer’s instruction. Sample position in the DNA extraction plates was randomized using a physical method, and this randomized distribution was maintained through library preparation and sequencing.

The method of Ames25 was used to determine the phosphate concentration in the shoots of seedlings grown on different Pi regimens and treatments. Main root length elongation was measured using ImageJ software26 and for shoot area and number of lateral roots WinRhizo software27 was used.

Processing of 16S sequencing data. For wild soil experiment 16S sequencing, we processed libraries according to Caporaso et al.28. Three sets of index primers were used to amplify the V4 (515F–806R) region of the 16S rRNA gene of each sample. In each case, the reverse primer had a unique molecular barcode for each sample28. PCR reactions with ${ \sim } 2 0 \mathrm { n g }$ template were performed with 5 Prime Hot Master Mix in triplicate using plates 2, 4 and 5 from the 16S rRNA Amplification Protocol28. PCR blockers mPNA and $\mathrm { \ p P N A } ^ { 2 9 }$ were used to reduce contamination by plant host plastid and mitochondrial 16S amplicon. The PCR program used was: temperature cycling, $9 5 ^ { \circ } \mathrm { C }$ for 3 min; 35 cycles of $9 5 ^ { \circ } \mathrm { C }$ for $4 5 s$ ; $7 8 ^ { \circ } \mathrm { C }$ (PNA) for 30 s; $5 0 ^ { \circ } \mathrm { C }$ for 60 s; $7 2 ^ { \circ } \mathrm { C }$ for 90 s, $4 ^ { \circ } \mathrm { C }$ until use.

Reactions were purified using AMPure XP magnetic beads and quantified with Quant IT Picogreen. Amplicons were pooled in equal amounts and then diluted to $5 . 5 \mathrm { p M }$ for sequencing. Samples were sequenced on an Illumina MiSeq machine at UNC, using a 500-cycle V2 chemistry kit. The library was spiked with $2 5 \%$ PhiX control to increase sequence diversity. The raw data for the wild soil experiments is available in the EBI Sequence Read Archive (accession PRJEB15671).

For SynCom experiment 16S library, we amplified the V3-V4 regions of the bacterial 16S rRNA gene using primers 338F $5 ^ { \prime }$ -ACTCCTACGGGAGGCAGCA-3′) and 806R $5 ^ { \prime }$ -GGACTACHVGGGTWTCTAAT-3′). Libraries were created using a modified version of the Lundberg et al.29. In brief, the molecule-tagging step was changed to an exponential amplification to account for low DNA yields with the following reaction: $5 \mu \mathrm { l }$ Kapa Enhancer, $5 \mu \mathrm { l }$ Kapa Buffer A, $1 . 2 5 \mu \mathrm { l } 5 \mu \mathrm { M }$ 338F, 1.25 μl 5 μM 806R, $0 . 3 7 5 \mu \mathrm { l }$ mixed PNAs (1:1 mix of $1 0 0 \mu \mathrm { M }$ pPNA and $1 0 0 \mu \mathrm { M }$

mPNA), $0 . 5 \mu \mathrm { l }$ Kapa dNTPs, $0 . 2 \mu \mathrm { l }$ Kapa Robust Taq, ${ 8 \mu 1 } \mathrm { d H } _ { 2 } \mathrm { O } ,$ $5 \mu \mathrm { l }$ DNA; temperature cycling: $9 5 ^ { \circ } \mathrm { C }$ for 60 s, 24 cycles of $9 5 ^ { \circ } \mathrm { C }$ for 15 s, $7 8 ^ { \circ } \mathrm { C }$ (PNA) for 10 s, $5 0 ^ { \circ } \mathrm { C }$ for 30 s, $7 2 ^ { \circ } \mathrm { C }$ for 30 s, $4 ^ { \circ } \mathrm { C }$ until use. Following PCR cleanup to remove primer dimers, the PCR product was indexed using the same reaction and 9 cycles of the cycling conditions described in ref. 29. Sequencing was performed at UNC on an Illumina MiSeq instrument using a 600-cycle V3 chemistry kit. The raw data for the SynCom experiments is available in the EBI Sequence Read Archive accession PRJEB15671.

Amplicon sequence data processing. For wild soil census analysis, sequences from each experiment were pre-processed following standard method pipelines from refs 2, 19. Briefly, sequence pairs were merged, quality-filtered and de-multiplexed according to their barcodes. The resulting sequences were then clustered into Operational Taxonomic Unit (OTUs) using UPARSE30 implemented with USEARCH7.1090, at $9 7 \%$ identity. Representative OTU sequences (Supplementary Data set 1) were taxonomically annotated with the RDP classifier31 trained on the Greengenes database (4 February 2011; Supplementary Data set 1). We used a custom script (https://github.com/surh/pbi/blob/master/census/1. filter_contaminants.r) to remove organellar OTUs, and OTUs that had no more than a kingdom-level classification, and an OTU count table was generated (Supplementary Table 1, Supplementary Data set 1).

SynCom sequencing data were processed with MT-Toolbox32. Categorizable reads from MT-Toolbox (that is, reads with correct primer and primer sequences that successfully merged with their pair) were quality filtered with Sickle by not allowing any window with Q-score under 20, and trimmed from the $5 ^ { \prime }$ end to a final length of 270 bp. The resulting sequences were matched to a reference set of the strains in the SynCom generated from Sanger sequences, the sequence from a contaminant strain (47Yellow) that grew in the plate from strain 47 (Supplementary Table 2) and Arabidopsis organellar sequences. Sequence mapping was done with USEARCH7.1090 with the option ‘usearch_global’ at a $9 8 \%$ identity threshold. $9 0 \%$ of sequences matched an expected isolate, and those sequence mapping results were used to produce an isolate abundance table. The remaining unmapped sequences were clustered into OTUs with the same settings used for the census experiment, the vast majority of those OTUs belonged to the same families as isolates in the SynCom, and were probably unmapped due to PCR and/or sequencing errors. We combined the isolate and OTU count tables into a single master table. The resulting table was processed and analysed with the code at (https://github.com/surh/pbi/ blob/master/syncom/7.syncomP_16S.r). Matches to Arabidopsis organelles were discarded. PCR blanks were included in the sequencing and the average counts per strain observed on those blanks were subtracted from the rest of the samples following33. Extended Data Figure 7a shows the number of usable reads across samples, and the remaining number after subtracting sterile controls (blanks).

In vitro plant growth conditions. For physiological, transcriptional analysis or pathology experiments, we used phr1, phr1;phl1, phf1, and coi1-16;sid2-1 mutants, which are all in the Col-0 genetic background (Supplementary Table 16). For all physiological and transcriptional analysis in vitro, Arabidopsis seedlings were grown on Johnson medium $\mathrm { ( K N O _ { 3 } }$ $( 0 . 6 \mathrm { g } 1 ^ { - 1 } )$ , $\mathrm { C a } ( \mathrm { N O } _ { 3 } ) _ { 2 } { \cdot } 4 \mathrm { H } _ { 2 } \mathrm { O }$ $( 0 . 9 \mathrm { g } 1 ^ { - 1 } )$ ), $\mathrm { M g S O _ { 4 } { \cdot } 7 H _ { 2 } O }$ $( 0 . 2 \mathrm { g } 1 ^ { - 1 } )$ , KCl $( 3 . 8 \mathrm { m g l ^ { - 1 } } )$ ), $_ \mathrm { H _ { 3 } B O _ { 3 } }$ $( 1 . 5 \mathrm { m g } 1 ^ { - 1 } )$ , $\mathrm { M n S O } _ { 4 } { \cdot } \mathrm { H } _ { 2 } \mathrm { O }$ $( 0 . 8 \mathrm { m g l ^ { - 1 } } )$ ), $\mathrm { Z n S O _ { 4 } { \cdot } 7 H _ { 2 } O }$ $( 0 . 6 \mathrm { m g l ^ { - 1 } } )$ ), $\mathrm { C u S O _ { 4 } }$ · $5 \mathrm { H } _ { 2 } \mathrm { O }$ $( 0 . 1 \mathrm { m g } 1 ^ { - 1 } ,$ ), $_ \mathrm { H _ { 2 } M o O _ { 4 } }$ $( 1 6 . 1 \mu \mathrm { g } 1 ^ { - 1 } )$ ), $\mathrm { F e S O } _ { 4 } { \cdot } 7 \mathrm { H } _ { 2 } \mathrm { O }$ $\mathrm { ( 1 . 1 m g l ^ { - 1 } ) }$ ), Myo-Inositol $( 0 . 1 \mathrm { g } 1 ^ { - 1 } )$ ), MES $( 0 . 5 \mathrm { g l } ^ { - 1 } )$ ), $\mathrm { p H } 5 . 6 \substack { - 5 . 7 ) }$ solidified with $1 \%$ bacto-agar (BD, Difco). Media were supplemented with P $\mathrm { i } \left( \mathrm { K H } _ { 2 } \mathrm { P O } _ { 4 } \right)$ at distinct concentrations depending on the experiment; 1mM Pi was used for complete medium and approximately $5 \mu \mathrm { M }$ Pi (traces of Pi in the agar) was the Pi concentration in the medium not supplemented with Pi. Unless otherwise stated, plants were grown in a growth chamber in a 15-h dark/9-h light regime $2 1 ^ { \circ } \mathrm { C }$ day ${ } ^ { \prime } 1 8 { } ^ { \circ } \mathrm { C }$ night).

For Synthetic Community experiments, plants were germinated on Johnson medium containing $0 . 5 \%$ sucrose, with 1 mM Pi, $5 \mu \mathrm { M }$ Pi or supplemented with $\mathrm { K H } _ { 2 } \mathrm { P O } _ { 3 }$ (phosphite) at 1 mM for 7 days in a vertical position, then transferred to $5 0 \mu \mathrm { M }$ Pi or $6 2 5 \mu \mathrm { M }$ Pi media (without sucrose) alone or with the Synthetic Community at $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l } ^ { - 1 }$ , for another 12 days. For the heat-killed SynCom experiments, plants were grown as above. Heat-killed SynComs were obtained by heating different concentrations of bacteria: $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l } ^ { - 1 }$ , $1 0 ^ { 6 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ and $1 0 ^ { 7 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ at $9 5 ^ { \circ } \mathrm { C }$ for $^ { 2 \mathrm { h } }$ in an oven. The whole content of the heat-killed SynCom solutions were added to the media.

For the functional activation of the PSR by the SynCom, plants were germinated on Johnson medium containing $0 . 5 \%$ sucrose, 1 mM Pi for 7 days in a vertical position, then transferred to 0, 10, 30, 50 and $6 2 5 \mu \mathrm { M }$ Pi alone, or to 0, 50 and $6 2 5 \mu \mathrm { M }$ Pi with the Synthetic Community at $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ , for another 12 days. At this point, we harvested our time zero (three replicas per conditions, each replica was five shoots harvested across all plates used). The remaining plants were transferred again to 1 mM Pi to evaluate the capacity of the plants for Pi accumulation in a time series analysis. We harvested plant shoots every 24 h for 3 days and Pi-concentration was determined. Pi increase was calculated as:

(Pi concentration day $n - \mathrm { P i }$ concentration day 0) / Pi-concentration day 0. Relative increase in Pi concentration is plotted in Fig. 2c. Both relative and absolute Pi concentration values are provided in Supplementary Table 4.

We repeated this experiment twice. For the first experiment, we used 6 plates with 10 plants per condition (48 plates and 480 plants in total). We harvested three replicas per time point with 5 shoots each. In all cases, shoots were harvested across all plates used. For the second experiment, we used 11 plates with 10 plants per condition (88 plates and 880 plants). In this case, we harvested 6 replicas for 1, 2 and 3 days after the re-feeding with Pi, and 3 replicas for time zero. Each replica contains 5 shoots harvested across all the plates used.

For the demonstration that sucrose is required for the induction of PSR in sterile conditions, plants overexpressing the PSR reporter construct IPS1:GUS (ref. 13) were grown in Johnson medium containing 1 mM Pi or $5 \mu \mathrm { M }$ Pi supplemented with different concentrations of sucrose. After 12 days, the expression of the reporter constructs IPS1:GUS, highly induced by low Pi, was followed by GUS staining. Plants were grown in a growth chamber in a 15-h light/9-h dark regime $2 1 ^ { \circ } \mathrm { C }$ day $/ 1 8 ^ { \circ } \mathrm { C }$ night).

For the ChIP–seq experiment, phr1 harbouring the PromPHR1:PHR1-MYC construct18 and Col-0 seedlings were grown on Johnson medium 1 mM Pi, $1 \%$ sucrose for 7 days and then transferred to a media not supplemented with Pi for another 5 days. Plants were grown in a growth chamber in a 15-h light/9-h dark regime ( $2 1 ^ { \circ } \mathrm { C }$ day ${ } ^ { 7 } 1 8 { } ^ { \circ } \mathrm { C }$ night). A total of 2,364 genes were identified as regulated by PHR1. The ChIP–seq data will be fully presented elsewhere (J. Paz-Ares, unpublished data).

For the transcriptional analysis under conditions typically used to study PSR (axenic growth with sucrose present; no microbiota involved), with methyl jasmonate (MeJA) and the 22-amino-acid flagellin peptide (flg22), plants were germinated on Johnson medium ( $1 \%$ sucrose) containing 1 mM Pi for 7 days in a vertical position and then transferred to 1 mM Pi and $5 \mu \mathrm { M }$ Pi media containing $1 \%$ sucrose either alone or supplemented with $1 0 \mu \mathrm { M }$ MeJA (Sigma) or $1 \mu \mathrm { M }$ flg22 (Sigma) for 12 days.

For growth inhibition assays, seedlings were grown on Johnson medium $1 \%$ sucrose) in 1 mM Pi and $5 \mu \mathrm { M }$ Pi conditions for 5 days, transferred to 1 mM Pi and $5 \mu \mathrm { M }$ Pi media supplemented or not with $1 0 \mu \mathrm { M }$ MeJA for 5 days. Main root length was then measured using ImageJ software26.

Bacterial isolation and culture. For Synthetic Community experiments, we selected 35 diverse bacterial strains. 32 of them were isolated from roots of Arabidopsis and other Brassicaceae species grown in two wild soils19. Two strains came from Mason Farm unplanted soil19, and Escherichia coli DH5α was included as a control (Supplementary Table 2). More than half (19 out of 35) of the strains belonged to families enriched in the endophytic compartments of plants grown in Mason Farm soil2,19 (Supplementary Table 2). The strains were chosen from a larger isolate collection in a way that maximizes SynCom diversity while retaining enough differences in their 16S rRNA gene to allow for easy and unambiguous identification.

A single colony of bacteria to be tested was inoculated in $4 \mathrm { m l }$ of 2XYT medium $\mathrm { 1 6 g l ^ { - 1 } }$ tryptone, $1 0 \mathrm { g l } ^ { - 1 }$ yeast extract, $5 \mathrm { g } 1 ^ { - 1 }$ NaCL, ${ \sim } 5 . 5 \mathrm { m M }$ Pi) in a test tube. Bacterial cultures were grown while shaking at $2 8 ^ { \circ } \mathrm { C }$ overnight. At this point, the Pi concentration was reduced to by dilution to 5mM Pi average in the supernatants (10 cultures used for the quantification). Cultures were then rinsed with a sterile solution of 10 mM $\mathrm { M g C l } _ { 2 }$ followed by a centrifugation step at ${ 2 , 6 0 0 g }$ for 8 min. This process was repeated twice. The concentration of Pi in the supernatant after the first wash with $\mathrm { M g C l } _ { 2 }$ was $0 . 0 6 \mathrm { m M }$ Pi and after the second wash it was reduced to $0 . 0 0 5 \mathrm { m M }$ Pi. In the suspension of SynCom member cells in $\mathrm { M g C l } _ { 2 }$ , the average concentration of Pi was $0 . 0 8 \mathrm { m M }$ . The $\mathrm { O D } _ { 6 0 0 \mathrm { n m } }$ was measured and assuming that $\mathrm { . O D _ { 6 0 0 \mathrm { n m } } }$ unit is equal to $1 0 ^ { 9 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ we equalized individual bacterium concentration to a final value of $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ of medium. The concentration of Pi in the final SynCom was $0 . 0 9 \mu \mathrm { M }$ Pi. Thus, based on these results, we were not Pi fertilizing the plant by adding the SynCom. Medium was cooled down (to $4 0 { - } 4 4 ^ { \circ } \mathrm { C }$ ) near the solidification point and then the bacteria mix was added to the medium with agitation. We monitored the pH in the media after adding 1, 5, and $1 0 \mathrm { m l }$ of 10mM $\mathrm { M g C l } _ { 2 }$ which represents almost ten times the volume we used to add the SynCom. After adding $\mathrm { M g C l } _ { 2 }$ the pH in the media remained stable. We also analysed the pH after adding the SynCom at $1 0 ^ { 5 }$ , $1 0 ^ { 6 }$ and $1 0 ^ { 7 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ of media and found no pH changes. Therefore, we considered that the MES buffer we used was appropriate for this experiment.

To isolate and quantify bacteria from plant roots in the SynCom experiment, plant roots were harvested, and rinsed three times with sterile distilled water to remove agar particles and weakly associated microbes. Plant material was then freeze-dried. Root pulverization and DNA extraction was conducted as described above.

To isolate and quantify bacteria from agar samples, a freeze and squeeze protocol was used. Syringes with a square of sterilized miracloth at the bottom were

completely packed with agar and kept at $- 2 0 ^ { \circ } \mathrm { C }$ for a week. Samples were thawed at room temperature and syringes were squeezed gently into $5 0 \mathrm { m l ^ { - 1 } }$ tubes. Samples were centrifuged at max speed for $2 0 \mathrm { { m i n } }$ and most of the supernatant discarded. The remaining $1 { - } 2 \mathrm { m l }$ of supernatant, containing the pellet, was moved into clean microfuge tubes. Samples were centrifuged again, supernatant was removed, and pellets were used for DNA extraction. DNA extraction was performed using 96-well format MoBio PowerSoil Kit (MOBIO Laboratories).

Pathology studies. For oomycete pathology studies, Hyaloperonospora arabidopsidis (Hpa) isolate Noco2 was propagated on the susceptible Arabidopsis ecotype Col-0. Spores of Hpa were suspended in deionized sterile water at a concentration of $5 \times 1 0 ^ { 4 }$ spores per ml. The solution containing spores was spray-inoculated onto 10-day-old seedlings of Arabidopsis grown in fertilized potting soil. Inoculated plants were grown a $2 1 ^ { \circ } \mathrm { C }$ under a 15-h dark/9-h light regime. Asexual sporangiophores were counted 5 days after inoculation on at least 100 cotyledons for each genotype.

For bacterial pathology studies, Pseudomonas syringae pv. tomato DC3000 was suspended in 10mM $\mathrm { M g C l } _ { 2 }$ to a final concentration of $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ . 35–40-dayold plants of Arabidopsis grown on soil were hand-infiltrated using a needle-less syringe on the abaxial leaf surface. Leaf discs (10 mm diameter) were collected after 1 h and 3 days after inoculation, and bacterial growth was measured as described34.

Genome-wide gene expression analyses. We performed three different sets of RNA-seq experiments in this study. (1) The first set (Figs 2b, 3, Extended Data Fig. 4b) evaluated the effect of the SynCom on the phosphate starvation response of Arabidopsis seedlings. In addition to wild-type Col-0 (4 replicates), phf1 (4 replicates) and phr1;phl1 (4 replicates) were included in the experiment shown in Fig. 2b, whereas Col-0 (10 replicates), phr1 (10 replicates) and phr1;phl1 (6 replicates) were used in the experiment shown in Fig. 3 and Extended Data Fig. 4b. (2) The second experiment (Extended Data Fig. 6a, b) is an expansion of the first and was designed to evaluate whether different pre-treatments (1 mM Pi, $5 \mu \mathrm { M }$ Pi, 1 mM phosphite (Phi)) influence the phosphate starvation response triggered by the SynCom. We used Col-0 (4 replicates), phf1 (4 replicates) and phr1;phl1 (4 replicates) in this experiment. (3) Finally, the third experiment evaluated the effect of MeJA and flg22 on the phosphate starvation response (Fig. 4, Extended Data Fig. 9) of Arabidopsis seedlings. The genotypes Col-0 (6 replicates) and phr1;phl1 (6 replicates) were used. The experiments listed above were repeated between two and five independent times and each repetition (defined as ‘batch’ in the generalized linear model, see RNA-seq data analysis, below) included two biological replicates per genotype per condition. Supplementary Table 15 contains the metadata information of all RNA-seq experiments. Raw reads and read counts are available at the NCBI Gene Expression Omnibus under accession number GSE87339.

RNA isolation and RNA-seq library construction. Total RNA was extracted from roots of Arabidopsis according to ref. 35. Frozen seedlings were pulverized in liquid nitrogen. Samples were homogenized in $4 0 0 \mu \mathrm { l }$ of Z6-buffer; 8 M guanidinium-HCl, $2 0 \mathrm { m M }$ MES, $2 0 \mathrm { m M }$ EDTA (pH 7.0). Following the addition of $4 0 0 \mu \mathrm { l }$ phenol:chloroform:isoamylalcohol; 25:24:1, samples were vortexed and centrifuged (20,000g, 10 min) for phase separation. The aqueous phase was transferred to a new $1 . 5 \mathrm { m l }$ tube and 0.05 volumes of 1 N acetic acid and 0.7 volumes $9 6 \%$ ethanol were added. The RNA was precipitated at $- 2 0 ^ { \circ } \mathrm { C }$ overnight. Following centrifugation, (20,000g, 10min, $4 ^ { \circ } \mathrm { C } )$ the pellet was washed with $2 0 0 \mu \mathrm { l }$ sodium-acetate (pH 5.2) and $7 0 \%$ ethanol. The RNA was dried, and dissolved in $3 0 \mu \mathrm { l }$ of ultrapure water and stored at $- 8 0 ^ { \circ } \mathrm { C }$ until use.

Illumina-based mRNA-seq libraries were prepared from 1,000 ng RNA. Briefly, mRNA was purified from total RNA using Sera-mag oligo(dT) magnetic beads (GE Healthcare Life Sciences) and then fragmented in the presence of divalent cations $( \mathrm { M g ^ { 2 + } } )$ at $9 4 ^ { \circ } \mathrm { C }$ for 6 min. The resulting fragmented mRNA was used for first-strand cDNA synthesis using random hexamers and reverse transcriptase, followed by second strand cDNA synthesis using DNA polymerase I and RNaseH. Double-stranded cDNA was end-repaired using T4 DNA polymerase, T4 polynucleotide kinase and Klenow polymerase. The DNA fragments were then adenylated using Klenow exo-polymerase to allow the ligation of Illumina Truseq HT adapters (D501–D508 and D701–D712). All enzymes were purchased from Enzymatics. Following library preparation, quality control and quantification were performed using a 2100 Bioanalyzer instrument (Agilent) and the Quant-iT PicoGreen dsDNA Reagent (Invitrogen), respectively. Libraries were sequenced using Illumina HiSeq2500 sequencers to generate 50-bp single-end reads.

RNA-seq data analysis. Initial quality assessment of the Illumina RNA-seq reads was performed using the FASTX-Toolkit. Cutadapt36 was used to identify and discard reads containing the Illumina adaptor sequence. The resulting high-quality reads were then mapped against the TAIR10 Arabidopsis reference genome using Tophat37, with parameters set to allow only one mismatch and discard any read that mapped to multiple positions in the reference. The Python package HTSeq38 was

used to count reads that mapped to each one of the 27,206 nuclear protein-coding genes. Extended Data Fig. 10 shows a summary of the uniquely mapped read counts per library. Raw sequencing data and read counts are available at the NCBI Gene Expression Omnibus accession number GSE87339.

Differential gene expression analyses were performed using the generalized linear model (glm) approach39 implemented in the edgeR package40. This software was specifically developed and optimized to deal with over-dispersed count data, which is produced by RNA-seq. Normalization was performed using the trimmed mean of M-values method (TMM41; function calcNormFactors in edgeR). The glmFit function was used to fit the counts in a negative binomial generalized linear model with a log link function39. For the SynCom experiment (Fig. 3), the model includes the covariates: phosphate content (high or low), bacteria (present or absent) and batch effect. A term for the interaction between phosphate and bacteria was included as represented below:

$\mathrm { E x p r e s s i o n = p h o s p h a t e + b a c t e r i a + ( p h o s p h a t e \times b a c t e r i a ) + b a t c h }$ $=$

The model used to analyse the effect of MeJA and flg22 (Fig. 4) included the following covariates: phosphate content (high or low), MeJA (present or absent), flg22 (present or absent) and batch effect:

$\mathrm { E x p r e s s i o n } = \mathrm { p h o s p h a t e } + \mathrm { M e J a } + \mathrm { f l g } 2 2 + \mathrm { b a t c h }$

In each model, the term ‘batch’ refers to independent repetitions of the experiment (see the ‘Genome-wide gene expression analyses’ section). Data from the different genotypes were fitted independently with the same model variables. The Benjamini–Hochberg method (false discovery rate; FDR)42 was applied to correct the $P$ values after performing multiple comparisons. Genes with FDR below or equal to 0.01 and fold-change variation of at least $1 . 5 \times$ were considered differentially expressed.

Transcriptional activation of the phosphate starvation response was studied using a literature-curated set of phosphate starvation marker genes (Extended Data Fig. 4a, Supplementary Table 3). This core set consists of 193 genes that were upregulated by phosphate starvation stress across four different gene expression experiments13,43–45. The RPKM (reads per kilobase of transcript per million mapped reads) expression values of these 193 genes were $z$ -score transformed and used to generate box and whiskers plots to show the distribution of the expression values of this gene set.

Hierarchical clustering analyses were performed with the ‘heatmap.2’ function in R from the gplots package46, using the sets of differentially expressed genes identified in each experiment. Genes were clustered on the basis of the Euclidean distance and with the complete-linkage method. Genes belonging to each cluster were submitted to Gene Ontology (GO) enrichment analyses on the PlantGSEA platform47 to identify over-represented biological processes.

Defining markers of the MeJA and SA responses. Genes whose transcription is induced by MeJA (672 genes), BTH/SA (2,096 genes) or both hormones (261 genes) were used as markers of the activation of these immune response output sectors in Arabidopsis (Supplementary Table 10)48. These gene sets were defined using two-week old Col-0 seedlings grown on potting soil and sprayed with MeJA $( 5 0 \mu \mathrm { M }$ ; Sigma), BTH $3 0 0 \mu \mathrm { M }$ ; Actigard 50WG) or a mock solution $0 . 0 2 \%$ Silwet, $0 . 1 \%$ ethanol). Samples were harvested 1 h, 5 h and 8 h after the treatment in two independent experiments. Total RNA was extracted with the RNeasy Plant Mini kit (Qiagen) and then used to prepare Illumina mRNA-seq libraries. The bioinformatics pipeline to generate count tables and the criteria used to define differentially expressed genes between conditions (hormone treatment versus mock treatment) was the same as described above. Raw sequencing data are available at the NCBI Gene Expression Omnibus under the accession number GSE90077.

Statistical analyses. Most statistical analyses were performed in the R statistical environment49 and follow methods previously described2 . As described in the following subsections, a number of packages were used, and many were called through AMOR-0.0-14 (ref. 50), which is based on code from ref. 2. All scripts and $\mathrm { k n i t r } ^ { 5 1 }$ output from R scripts are available upon request. Most plots are ggplot2 (ref. 52) objects generated with functions in AMOR50. For all linear modelling analyses (ANOVA, ZINB, GLM), terms for batch and biological replicate were included whenever appropriate. Code for both census and SynCom analysis is available at https://github.com/surh/pbi.

For wild soil and SynCom experiments, the number of samples per genotype and treatment was determined on the basis of our previously published work, which showed that seven and five samples are enough to detect differences in wild soils and SynCom experiments, respectively2,19. For RNA-seq experiments, we used at least four replicates per condition, which is sufficient for parameter estimation with the edgeR software40.

Alpha and beta diversity were calculated on count tables that were rarefied to 1,000 reads. Samples with less than this number of usable reads (that is, high quality

non-organellar reads) were discarded. Alpha diversity (Shannon index, richness) metrics were calculated using the ‘diversity’ function in vegan53, and differences between groups were tested with ANOVA (Extended Data Fig. 1a). Site diversity (Extended Data Fig. 1b) was calculated with the ‘sitediv’ function in AMOR50. Unconstrained ordination was performed with vegan (Bray–Curtis), and principal coordinate analysis (PCoA) was performed with AMOR50 (Extended Data Fig. 1d). Canonical analysis of principal coordinates (CAP) is a form of constrained ordination54 and was performed using the ‘capscale’ function of the vegan package in $\mathrm { R } ^ { 5 3 }$ . CAP was performed on the full counts of the endophytic compartment samples only, using the ‘Cao’ distance. Constraining was done separately on plant genotype while conditioning on sequencing depth and biological replicate. This approach allowed us to focus on the portion of variation that is associated with plant genotype, conditionally, independent of other factors.

For the SynCom experiments, richness was directly calculated in R. Principal coordinate analysis was performed with the ‘PCO’ function of AMOR50 using the ‘Cao’ distance which was calculated with vegan53 on an abundance table rarefied to 1,500 reads per sample. CAP was performed using the ‘capscale’ function of the vegan package53 in R. CAP was performed on the full counts of the root samples only, using the ‘Cao’ distance. Constraining was done separately on fraction, Pi level and plant genotype, while conditioning on sequencing depth and the other covariates.

Differentially abundant bacterial taxa across fraction and genotype in the wild soil experiments were identified using the same approach as in ref. 2. Briefly, we used a zero-inflated negative binomial (ZINB) framework that allowed us to test for the effect of specific variables, while both controlling for the other covariates and accounting for the excess of zero entries in the abundance tables. These zero-entries probably represented under-sampling and not true absences. The same analysis was performed at the family and OTU-level on the measurable OTUs (taxa that have an abundance of at least 25 counts in at least five samples)19. Results are in Extended Data Fig. 1e–h, Supplementary Table 1. Extended Data Fig. 1h shows the distribution of significant genotypic effects on bacterial abundances at both taxonomic levels; in both cases the behaviour is similar, indicating small and even effects of all genotypes.

For the comparison of enrichment profiles between genotypes, we followed the same Monte-Carlo approach described in ref. 2. Briefly we looked at the enrichment/depletion profile of bacterial taxa for each mutant compared to wild-type Col-0, and asked, for each pair of mutants, if they were more similar than expected by chance and assed significance by random permutation. Results are in Fig. 1d, Extended Data Fig. 1g.

To define differentially abundant strains in SynCom experiments, we found that a negative binomial generalized linear model (GLM) approach gave more stable results than the ZINB approach. We used the edgeR package40 to fit a quasinegative-binomial-GLM model with the glmQLFit function, and significance was tested with the glmQLFtest function55. Results of all relevant pairwise comparisons are in Extended Data Fig. 7 and Supplementary Table 5.

For the definition of robust colonizers in synthetic community experiments, we calculated the average relative abundance of E. coli on all root samples and counted, for each strain, how many times it was more abundant than E. coli’s average on the same set of root samples. Then we used a one-sided binomial test to ask if the probability of a given strain to be more abundant than the average E.coli was significantly higher than a coin toss $( 5 0 \% )$ ). Strains that passed the test were labelled as robust-colonizers, the rest of the strains were labelled as sporadic or non-colonizers. The results are indicated in Fig. 2e and Supplementary Table 2. Data and software accessibility. All data generated from this project is publicly available. Raw sequences from soil census and SynCom colonization are available at the EBI Sequence Read Archive under accession PRJEB15671. Count tables, metadata, taxonomic annotations and OTU representative sequences from the Mason Farm census and Syncom experiments are available as Supplementary Data 1 and Supplementary Data 2 respectively. Custom scripts used for statistical analysis and plotting are available at (https://github.com/surh/pbi). Raw sequences from transcriptomic experiments are available at the NCBI Gene Expression Omnibus under the accession number GSE87339. The corresponding metadata information is provided in Supplementary Table 15. All code is available upon request.

25. Ames, B. N. Assay of inorganic phosphate, total phosphate and phosphatases. Methods Enzymol. 8, 115–118 (1966).   
26. Barboriak, D. P., Padua, A. O., York, G. E. & Macfall, J. R. Creation of DICOMaware applications using ImageJ. J. Digit. Imaging 18, 91–99 (2005).   
27. Arsenault, J. L., Pouleur, S., Messier, C. & Guay, R. WinRHIZO, a root-measuring system with a unique overlap correction method. HortScience 30, 906 (1995).   
28. Caporaso, J. G. et al. Ultra-high-throughput microbial community analysis on the Illumina HiSeq and MiSeq platforms. ISME J. 6, 1621–1624 (2012).

29. Lundberg, D. S., Yourstone, S., Mieczkowski, P., Jones, C. D. & Dangl, J. L. Practical innovations for high-throughput amplicon sequencing. Nat. Methods 10, 999–1002 (2013).   
30. Edgar, R. C. UPARSE: highly accurate OTU sequences from microbial amplicon reads. Nat. Methods 10, 996–998 (2013).   
31. Wang, Q., Garrity, G. M., Tiedje, J. M. & Cole, J. R. Naive Bayesian classifier for rapid assignment of rRNA sequences into the new bacterial taxonomy. Appl. Environ. Microbiol. 73, 5261–5267 (2007).   
32. Yourstone, S. M., Lundberg, D. S., Dangl, J. L. & Jones, C. D. MT-Toolbox: improved amplicon sequencing using molecule tags. BMC Bioinformatics 15, 284 (2014).   
33. Nguyen, N. H., Smith, D., Peay, K. & Kennedy, P. Parsing ecological signal from noise in next generation amplicon sequencing. New Phytol. 205, 1389–1393 (2015).   
34. Hubert, D. A., He, Y., McNulty, B. C., Tornero, P & Dangl, J. L. Specific Arabidopsis HSP90.2 alleles recapitulate RAR1 cochaperone function in plant NB-LRR disease resistance protein regulation. Proc. Natl Acad. Sci. USA 106, 9556–9563 (2009).   
35. Logemann, J., Schell, J. & Willmitzer, L. Improved method for the isolation of RNA from plant tissues. Anal. Biochem. 163, 16–20 (1987).   
36. Martin, M. Cutadapt removes adapter sequences from high-throughput sequencing reads. EMBnet. Journal. 17, 10–12 (2011).   
37. Trapnell, C., Pachter, L. & Salzberg, S. L. TopHat: discovering splice junctions with RNA-Seq. Bioinformatics 25, 1105–1111 (2009).   
38. Anders, S., Pyl, P. T. & Huber, W. HTSeq—a Python framework to work with high-throughput sequencing data. Bioinformatics 31, 166–169 (2015).   
39. McCarthy, D. J., Chen, Y. & Smyth, G. K. Differential expression analysis of multifactor RNA-Seq experiments with respect to biological variation. Nucleic Acids Res. 40, 4288–4297 (2012).   
40. Robinson, M. D., McCarthy, D. J. & Smyth, G. K. edgeR: a Bioconductor package for differential expression analysis of digital gene expression data. Bioinformatics 26, 139–140 (2010).   
41. Robinson, M. D. & Oshlack, A. A scaling normalization method for differential expression analysis of RNA-seq data. Genome Biol. 11, R25 (2010).

42. Benjamini, Y. & Hochberg, Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. J. R. Stat. Soc. B 57, 289–300 (1995).   
43. Morcuende, R. et al. Genome-wide reprogramming of metabolism and regulatory networks of Arabidopsis in response to phosphorus. Plant Cell Environ. 30, 85–112 (2007).   
44. Misson, J. et al. A genome-wide transcriptional analysis using Arabidopsis thaliana Affymetrix gene chips determined plant responses to phosphate deprivation. Proc. Natl Acad. Sci. USA 102, 11934–11939 (2005).   
45. Castrillo, G. et al. WRKY6 transcription factor restricts arsenate uptake and transposon activation in Arabidopsis. Plant Cell 25, 2944–2957 (2013).   
46. Gregory, R. et al. gplots: Various R programming tools for plotting data. R package version. 3.0.1 (2016).   
47. Yi, X., Du, Z. & Su, Z. PlantGSEA: a gene set enrichment analysis toolkit for plant community. Nucleic Acids Res. 41, W98–W103 (2013).   
48. Yang, L. et al. Pseudomonas syringae type III effector HopBB1 fine tunes pathogen virulence by degrading host transcriptional repressors. Cell Host Microbe 21, 156–168 (2017).   
49. R Core Team. R: A language and environment for statistical computing. http://www.R-project.org/ (2014).   
50. Sur Herrera Paredes. AMOR 0.0-14. Zenodo. http://dx.doi.org/10.5281/ zenodo.49093 (2016).   
51. Xie, Y. knitr: A feneral-purpose package for dynamic report generation in R. R package version 1.12.3 (2016).   
52. Wickham, H. ggplot2: Elegant graphics for data analysis. (Springer-Verlag, 2009).   
53. Oksanen, J. et al. vegan: Community ecology package. R package version 2.3-5 (2016).   
54. Anderson, M. J. & Willis, T. J. Canonical analysis of principal coordinates: A useful method of constrained ordination for ecology. Ecology 84, 511–525 (2003).   
55. Lun, A. T. L., Chen, Y. & Smyth, G. K. It’s DE-licious: a recipe for differential expression analyses of RNA-seq experiments using quasi-likelihood methods in edgeR. Methods Mol. Biol. 1418, 391–416 (2016).

![](images/c049b46f1d5ae78fe58efc114b2a15b1e5d5166fa51d2988945022a075cfef4e.jpg)  
a

![](images/e8d1dd24c129b4ed79b23f55f6c7952445a461fd29179d99ca2421cbac78861c.jpg)  
b

![](images/89aa189b548c66f79f330f0d7904b7f7554abcf6ecb2845e7154fa529af036d9.jpg)

![](images/23f879542fae955f990f159646a231b06b46d7c57299531c99f0cb9a79f9148e.jpg)  
C

![](images/c14f2adedfd6e3196d4cb6c104e6b60a60e9e0d9c85dc8a14e5f21355fc547b0.jpg)  
d

![](images/48b2b821f1e1bfe65c353d70eca5ec6d9bde47370a5ec3e112d245037887f90b.jpg)  
e

![](images/3ba965598e8e9061ce81db067b410bbccfdf15ee53bba0f0da347fb652881602.jpg)

# Enrichment

# Depletion

![](images/24094c768feee914c05fc8053ed2a6961413ab8a54d5e2edaa0ad33d03fa697e.jpg)

![](images/9e0aa2554193becfd938ba14402b6d4ab65e0a5a52180fd20142f7557d45d4f7.jpg)  
  
Extended Data Figure 1 | See next page for caption.

Extended Data Figure 1 | The Arabidopsis PSR alters highly specific bacterial taxa abundances. a, Alpha diversity of bacterial root microbiome in wild-type Col-0, PSR mutants and bulk soil samples. We used ANOVA methods and no statistical differences were detected between plant genotypes after controlling for experiment. b, Additive beta-diversity curves showing how many OTUs are found in bulk soil samples or root endophytic samples of the same genotype as more samples (pots) are added. The curves show the mean and the $9 5 \%$ confidence interval calculated from 20 permutations. c, Phylum-level distributions of plant root endophytic communities from different plant genotypes and bulk soil samples. d, Principal coordinates analysis based on Bray–Curtis dissimilarity of root and bulk soil bacterial communities showing a large effect of experiment on variation, as expected according to previous studies19. For a–d, the number of biological replicates per genotype and soil are: Col-0 $( n = 1 7 )$ , pht1;1 $( n = 1 8 )$ ), pht1;1;pht1;4 $( n = 1 7 )$ ), phf1 $( n = 1 3$ ), nla $( n = 1 6$ ), pho2 $n = 1 6 ,$ ), phr1 $( n = 1 8 )$ , spx1;spx2 $\ R = 1 4$ ) and soil $( n = 1 7 )$ ). e, Bacterial taxa that are differentially abundant (DA) between PSR mutants and Col-0. Each row represents a bacterial family (left) or OTU (right) that shows a significant abundance difference between Col-0 and at least one mutant. The heat map grey scale shows the mean abundance of the given taxa in the corresponding genotype, and

significant enrichments and depletions with respect to Col-0 are indicated with a red or blue rectangle, respectively. Taxa are organized by phylum shown on the right bar coloured according to f. f, Doughnut plot showing family-level (top) and OTU-level (bottom) differences in endophytic root microbiome compositions between mutants (columns) and Col-0 plants. The number inside each doughnut indicates how many bacterial families are enriched or depleted in each mutant with respect to Col-0, and the colours in the doughnut show the phylum level distribution of those differential abundances. g, Tables of $P$ values from Monte-Carlo pairwise comparisons between mutants. A significant $P$ value (cyan) indicates that two genotypes are more similar than expected by chance. Results of family-level comparison are shown. This plot should be compared with the corresponding OTU-level plot in Fig. 1d. h, Distributions of plant genotypic effects on taxonomic abundances at the family (up) or OTU (down) level. For each genotype, the value of the linear model coefficients for individual OTUs or families is plotted grouped by their sign. Positive values indicate that a given taxon has increased abundance in a mutant with respect to Col-0, whereas a negative value represents the inverse pattern. Only coefficients from significant comparisons are shown. The number of taxa (that is, points) on each box and whisker plot is indicated in the corresponding doughnut plot in f.

![](images/9f69ed3099ef76a2146e0f3270c765debabc70283c864a87574dd684c2a41b63.jpg)  
a   
MF

![](images/3357a0dc0d12724f3547a107b8bd9d5be4efb95bc41301d08b938bc0d6ec4dd5.jpg)  
b   
MF IPS1-GUS (2/12)

![](images/e1d858258b3020252499f966a9eba43d6f2b838d35a1e56f8bcf307b3d165bc6.jpg)  
GH IPS1-GUS (0/12)

![](images/5f60a27e648693b9a76ddfe7d8fb047cd2b928dd35179569bdfba78b2be4ba0f.jpg)  
C   
Extended Data Figure 2 | Plants grown in Mason Farm wild soil or Pi-replete potting soil do not induce PSR and accumulate the same amount of Pi. a, Plants overexpressing the PSR reporter construct IPS1:GUS grown in Mason Farm wild soil (MF) or in Pi-replete potting soil (GH) (250 p.p.m. of 20-20-20 Peters Professional Fertilizer). b, Expression analysis of the reporter constructs IPS1:GUS $n = 1 2$ ) shows lack of induction of PSR for both soils analysed. In this construct, the promoter region of IPS1, highly induced by low Pi, drives the expression   
of GUS. Plants were grown in the conditions described in a. The number of GUS positive plants relative to the total number of plants analysed in each condition is shown in parentheses. c, Pi concentration in shoots $( n = 6 )$ of plants grown in both soils analysed shows no differences. Plants were grown in a growth chamber in a 15-h light/9-h dark regime ( $2 1 ^ { \circ } \mathrm { C }$ day ${ } ^ { / } 1 8 { } ^ { \circ } \mathrm { C }$ night). Images shown here are representative of the 12 plants analysed in each case. Error bars, standard deviation.

![](images/c71d99de4df9d4718cd3fbe2938f33175b4693cbc2f2f5a33f51d84da776683d.jpg)

■Actinobacteria   
Bacteroidetes   
□Proteobacteria  
□others

![](images/2c71131fb98712cb64211da395838e6844750732d6724da7a3f076d80ef2755b.jpg)  
  
Extended Data Figure 3 | Phylogenetic composition of the 35-member SynCom. Left, comparison of taxonomic composition of soil (S), rhizosphere (R) and endophyte (EC) communities from ref. 19, with the taxonomic composition of the isolate collection obtained from the same   
samples and the SynCom selected from within it and used in this work. Right, maximum likelihood phylogenetic tree of the 35-member SynCom based on a concatenated alignment of 31 single-copy core proteins.

![](images/37b75871101c6227797da7e0a9c35209856ab134104dc4a64770e6604e972e8f.jpg)

![](images/6c3f7ec962ae78deb19f19407f05c0ab5b303d1e5f30634f9e227437a2045a98.jpg)

![](images/ba12b5c2713735c6e4ff4a0fd92b606a151e8d58ca2b1640f3602b1625b3788f.jpg)  
Extended Data Figure 4 | Induction of the PSR triggered by the SynCom is mediated by PHR1 activity. a, Venn diagram with the overlap among genes found upregulated during phosphate starvation in four different gene expression experiments13,43–45. The intersection (193 genes) was used as a robust core set of PSR for the analysis of our transcriptional data (Supplementary Table 3). b, Expression profile of the 193 core PSR genes indicating that the SynCom triggers phosphate starvation under low Pi conditions in a manner that depends on PHR1 activity. The RPKM expression values of these genes were $z$ -score transformed and used to generate box and whiskers plots that show the distribution of the   
expression values of this gene set. Col-0, the single mutant phr1 and the double mutant phr1;phl1 were germinated at 1 mM Pi with sucrose and then transferred to low Pi $( 5 0 \mu \mathrm { M } )$ and high Pi ( $6 2 5 \mu \mathrm { M }$ Pi) alone or with the SynCom. The figure shows the average measurement of ten biological replicates for Col-0 and phr1 and six for phr1;phl1. c, Percentage of genes per cluster (from Fig. 3) containing the PHR1 binding site (P1BS, GNATATNC) within 1,000 bp of their promoters. The red line indicates the percentage of Arabidopsis genes in the whole genome that contain the analysed feature. Asterisk denotes significant enrichment or depletion ( $P \leq 0 . 0 5$ ; hypergeometric test).

![](images/db7dcb9c308e72580bab72e62507e24ff5540476fe95292aef6589be837b9db9.jpg)  
a

![](images/756085e36a64ec47a5c935b3c928bcae41351efaac638e56f674a058ad029845.jpg)  
b

![](images/5dbd1c6e713c477a4017a7e756faaf726635e69db04f6ffd4510c871375f7ba1.jpg)

![](images/e89d89d3c5f05771f747c0473dfc985d4aceb066ea913e1843e71deefc3c24b1.jpg)

![](images/dcb1b409e017198abd837f5181b997e39201a541ba01dea81b2d05fa0add93fd.jpg)

![](images/47dfdf2095c35242af6f04ace66d24b843ac75a0185500cd704e8cc737b3c4e1.jpg)

![](images/89587a3075b1d8c1ac24ebb9c621bd884d72bde7b757ea9c12997973efd6d0d5.jpg)

![](images/47e1ba54e4d2f09fca0f95bd28bf41c28dbf79cf465f8c22c177e011170a9dfa.jpg)  
C

![](images/12ae11d468e7dc6d3665959aca0cfbc6da5c66172c1624225406cc5673025ca3.jpg)  
e

![](images/80dbbf44e9735cb61fe234bc5cf7678ee282817341ad395660a61b91c4cf6032.jpg)  
d

![](images/cc41b6e1e27ea32bd35d5ba2d0a5737febe299b456b0be6b0ca57b842534d368.jpg)  
f   
Extended Data Figure 5 | The SynCom induces PSR independently of sucrose in Arabidopsis. a, Expression analysis of a core of 193 PSR marker genes in an RNA-seq experiment using Col-0 plants. The RPKM expression values of these genes were $z$ -score transformed and used to generate box and whiskers plots that show the distribution of the expression values of this gene set. Plants were grown in Johnson medium containing replete (1 mM Pi; $\mathrm { ( + P i ) }$ ) or stress $5 \mu \mathrm { M }$ Pi; (−Pi)) Pi concentrations with $( + \mathsf { S u c } )$ or without (−Suc) $1 \%$ sucrose. b, Expression analysis of the reporter constructs IPS1:GUS $\ R = 2 0$ ). In this construct, the promoter region of IPS1, highly induced by low Pi, drives the expression of GUS. Plants were grown in Johnson medium $+ \mathrm { P i }$ or $- \mathrm { P i }$ at different percentages of sucrose. These results show that sucrose is required for the induction of the PSR in typical sterile conditions. Images shown are representative of the 20 plants analysed in each case. c, Top, plants grown in sterile conditions at different Pi concentrations (left (no bacteria)) or with a SynCom (right $( + \mathrm { { S y n C o m } ) }$ ). Bottom, histochemical analysis of $\beta$ -glucoronidase (GUS) activity in overexpressing IPS1:GUS plants $\mathrm { \Omega } ^ { \prime } n = 2 0 \mathrm { \Omega }$ ) from top panel. Images shown are representative of the 20 plants analysed in each case. d, Pi concentration in plant shoots from c, in all cases $n = 5$ . Analysis of variance indicated a significant effect of the Pi level in the media ( $F { = } 4 4 . 1 2$ , ${ \mathrm { d . f . } } = 1$ , P value $= 9 . 7 2 \times 1 0 ^ { - 8 }$ ), the presence of SynCom $F = 3 2 . 6 1$ , ${ \mathrm { d . f . } } = 1$ , P value $: = 1 . 6 9 \times 1 0 ^ { - 6 } )$ ) and a significant interaction between those two terms $F { = } 4 . 7 4 8$ , d.f. $= 1$ ,   
P value $= 0 . 0 3 6$ ) on Pi accumulation. F, F-value statistic from the ANOVA, d.f. is the degrees of freedom from the same test. e, Top, plants grown in axenic conditions (no bacteria), with a concentration gradient of heatkilled SynCom (2 h at $9 5 ^ { \circ } \mathrm { C } ,$ , (+heat-killed SynCom)) or with SynCom alive. Bottom, histochemical analysis of GUS activity in overexpressing IPS1:GUS plants $( n = 1 5$ ) from top panel. All plants were grown at $5 0 \mu \mathrm { M }$ Pi. Images shown are representative of the 15 plants analysed in each case. f, Quantification of Pi concentration in plant shoots from e, (in all cases $n = 5$ ). The SynCom effect on Pi concentration requires live bacteria. Plants were germinated on Johnson medium containing $0 . 5 \%$ 。 sucrose, with 1 mM Pi for 7 days in a vertical position, then transferred to 0, 10, 30, 50, $6 2 5 \mu \mathrm { M }$ Pi media (without sucrose) alone or with the SynCom at $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ (only for the conditions 0, 50 and $6 2 5 \mu \mathrm { M }$ Pi), for another 12 days. For the heat-killed SynCom experiments, plants were grown as above. Heat-killed SynComs were obtained by heating different concentrations of bacteria $1 0 ^ { 5 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ , $1 0 ^ { 6 }$ c.f.u. $\mathrm { m l } ^ { - 1 }$ and $1 0 ^ { 7 }$ c.f.u. $\mathrm { m l ^ { - 1 } }$ at $9 5 ^ { \circ } \mathrm { C }$ for $^ { 2 \mathrm { h } }$ in an oven. The whole content of the heat-killed SynCom solutions were add to the media. In all cases, addition of the SynCom did not change significantly the final Pi concentration or the pH in the media. Letters indicates grouping based on ANOVA and Tukey post hoc test at $9 5 \%$ confidence, conditions with the same letter are statistically indistinguishable.

![](images/7b81ed38f24ca86edd1aef2ecd1d699a4d2489c1095e8ed475bcf7a8a65cdf61.jpg)  
a

![](images/75743343e042b5fdf89c4a76c0308a610405ac589235ef253952dac82d500757.jpg)  
b   
Transcriptional abundance of Pi starvationmarkers

![](images/52b79e2fcc3f2bf8afc2e04bec8db49a3d0aab0c4f897c820a7e441bbc7d4adb.jpg)  
C

![](images/28e16a1a7e32bac78debabcdb01eed79eb56d217469b3854a12371cdb523579c.jpg)  
d

![](images/1f5efdbc94885b885dff748041b7699dcf14d9bb8b98074e1861cee2a4f83a0a.jpg)  
e

![](images/007d8c0be4ed4c266a401280d23ede3d7ef319ea138a2194ee35ed755b01fede.jpg)  
f

Bacteria***

![](images/3da6c24098530e1387ef775a7ad7d27cf3ea9b1c590b489ca21bdbc9b2bccdb4.jpg)  
Extended Data Figure 6 | Bacteria induce the PSR using the canonical pathway in Arabidopsis. a, Pi concentration in the shoot of Col-0 plants germinated in three different conditions, $5 \mu \mathrm { M }$ Pi $\mathrm { ( - P i ) }$ $( n = 1 4 )$ ), 1 mM Pi (+Pi) ${ \mathrm { ? } n = 1 5 }$ ) and 1 mM $\mathrm { K H } _ { 2 } \mathrm { P O } _ { 3 }$ (Phi) $( n = 1 5$ ) for 7 days. Phi is a non-metabolizable analogue of Pi; its accumulation delays the response to phosphate stress. b, Expression profile analysis of a core of PSR-marker genes in Col-0, phf1 and phr1;phl1. The RPKM expression values of these genes were $z$ -score transformed and used to generate box and whiskers plots that show the distribution of the expression values of this gene set. Plants were germinated in three different conditions, $5 \mu \mathrm { M }$ Pi (−Pi), 1 mM Pi $\mathrm { ( + P i ) }$ and 1 mM $\mathrm { K H } _ { 2 } \mathrm { P O } _ { 3 }$ (Phi) and then transferred to low Pi ( $5 0 \mu \mathrm { M }$ Pi) and high Pi $6 2 5  { \mu \mathrm { M P i } }$ ) alone or with the SynCom for another 12 days. The figure shows the average measurement of four biological replicates. c, Phenotype of plants grown in axenic conditions at $6 2 5 \mu \mathrm { M }$ Pi (top) or at $5 0 \mu \mathrm { M }$ Pi (bottom) (left (no bacteria)) or with a SynCom (right (+SynCom)). Images showed here are representative of the total   
number of plants analysed in each case as noted below. d, Quantification of the main root elongation. e, f, Number of lateral roots per plant (e) and number of lateral roots per cm of main root (f) in plants from c. For d–f, the number of biological replicates are: $6 2 5 \mu \mathrm { M }$ no bacteria $( n = 4 8 )$ ), $6 2 5 \mu \mathrm { M } + \mathrm { S y n C o 1 }$ m $( n = 4 6$ ), $5 0 \mu \mathrm { M }$ no bacteria $\left( n = 7 3 \right)$ ), and $5 0 \mu \mathrm { M }$ SynCom $( n = 5 6 )$ ), distributed across two independent experiments indicated with different shades of colour. Measurements were analysed with ANOVA, controlling for biological replicate. Asterisks denote a significant effect (P value $< 1 \times 1 0 ^ { - \mathrm { { \bar { 1 6 } } } }$ ) of treatment with SynCom for the three phenotypes in d–f. In all cases, neither the interaction between Pi and bacteria, nor Pi concentrations alone had a significant effect and were dropped from the ANOVA model. In all cases, residual quantiles from the ANOVA model were compared with residuals from a normal distribution to confirm that the assumptions made by ANOVA hold (see code on GitHub for details, see Methods).

No Bacteria

SynCom

![](images/5736eb38a376ab05eb1bd916011a19709277d70e33f1ae3eaa857669efbbdf92.jpg)  
a

![](images/e63d35fe93fca8c2f9979569c2d5268c4f6c568892d780faeb10ab5a1fd3f4b8.jpg)

![](images/0516d9d3bd68402b574498c4d36aef70c30387da91ba828e9e76c1756bea0fd7.jpg)  
C

![](images/9f5b809d817d86ce5d31899e06f596359f0f0c29d93e6a92561de02668dceff3.jpg)  
Extended Data Figure 7 | Plant genotype and Pi concentration alter SynCom strain abundances. a, Number of bacterial reads in samples of different types (left) and number of reads after blank normalization (right, see Methods). The number of biological replicates are: inoculum $( n = 8 )$ ), agar + SynCom $( n = 4 1$ ), agar no bacteria $( n = 2 )$ , roo $^ +$ SynCom ${ \mathrm { . } } n = 3 6$ ), root no bacteria $( n = 6 )$ ) and blank $( n = 3 )$ ), across two independent experiments. b, Richness (number of isolates detected) in SynCom samples. No differences were observed between plant genotypes. The number of biological replicates per group is $n = 1 2$ except for inoculum $( n = 4 )$ and phf1 $\ R = 1 1$ ). c, Exemplary SynCom strains that show quantitative abundance differences between genotypes. Genotypes with the same letter are statistically indistinguishable. d, Exemplary SynCom

![](images/73b6cf30cf6642ec5e2c0211c1ce5839463a17e9f104c8c595724b77a0b42edc.jpg)  
d

![](images/def3976e255fe15fa462420b2aa8570f04600b922e01d5ff2e7cfa86a55f6c74.jpg)  
  
f

![](images/6f63aa67b7489791882d91cbc2d8acde3d798e5a36eeba4b0086e2b9e31c19b3.jpg)  
strains that show quantitative abundance differences depending on Pi concentration in the media. Asterisks note statistically significant differences between the two Pi concentrations. e, CAP analysis of agar versus root difference in SynCom communities. These differences explained $9 . 1 \%$ of the variance. The number of biological replicates per fraction is: agar ${ \it n } = 1 2$ ) and root $( n = 3 5$ ), distributed across two independent experiments. f, Exemplary SynCom strain that shows a statistically significant differential abundance between root and agar samples. Statistically significant differences are defined as $\mathrm { F D R } < 0 . 0 5$ . For c, d and f, the number of biological replicates for every combination of genotype and Pi level is always $n = 6$ , evenly distributed across two independent experiments.

a   

<table><tr><td></td><td>Col-0</td><td>phr1</td><td>phr1/phl1</td></tr><tr><td>LowPi</td><td>1(1 up; 0 down)</td><td>0(0 up; 0 down)</td><td>0(0 up; 0 down)</td></tr><tr><td>Bacteria</td><td>519(126 up; 393 down)</td><td>552(297 up; 255 down)</td><td>276(63 up; 213 down)</td></tr><tr><td>LowPi*Bacteria</td><td>2537(1579 up; 958 down)</td><td>471(332 up; 139 down)</td><td>232(158 up; 74 down)</td></tr></table>

![](images/f522ea1d3df1fa84c36bc05736ebcf69de0dd565a34266cb43054a48c683c97c.jpg)  
b

![](images/7dc94c9be53cb930720199e4cb796ebd3d7efd20942088847e2921d2f86749e9.jpg)  
C

![](images/073b55719191f0ffaf256c78ebfbb62f441549dba33265e0e727b6ab43f225af.jpg)  
d   
e

![](images/154ebdcc43611f16f00da8ed729dcd04ccae9427df9ca6ea90a73ea29ed53e6e.jpg)

![](images/11eebc471ce172c463c2449d06de9adc162f32a174536bd7712d9ef561a1b696.jpg)

![](images/53144d9ced8421a0d92af361678e755b12ef5825c8db07d6bbfea572e252ee91.jpg)  
f

![](images/fdda5c157542f79893c3abff2968cd0fdc9e5142655ffe65fd6d03afe308bdd4.jpg)  
  
h

![](images/028749adc47a39761409ba0278e566c892639f44cd9429aff69d27b496de75ec.jpg)

![](images/77ff240229508929890913afbf72f9b8276f4a851a6c81a8292cec1a58d3b2d9.jpg)

![](images/302100f9fd28374019be097395c35eeaa88699f87d37189fece03a02964c1484.jpg)

![](images/d475447b8d2e1b75b45278f52ccdf7c1555cc417ebeb23f1d65a8ca9fba9c8dd.jpg)  
Hormone treatment

![](images/14ec5660d75907691f3b8073d53e9a5cfdb9b9763c994b5b95819a977b6669d5.jpg)

![](images/4184de8682cb722a9f1184a59c9d650ae513561a565b5b78e24b9729ed6bdabd.jpg)  
Extended Data Figure 8 | See next page for caption.

Extended Data Figure 8 | PHR1 controls the balance between the SA and JA regulons during the PSR induced by a 35-member SynCom. a, Total number of differentially expressed genes $( \mathrm { F D R } \leq 0 . 0 1 $ and minimum of $1 . 5 \times$ fold-change) in Col-0, phr1 and phr1;phl1 with respect to low Pi $5 0 \mu \mathrm { M }$ Pi), bacteria presence and the interaction between low Pi and bacteria. In this experiment, plants were grown for 7 days in Johnson medium containing 1 mM Pi, and then transferred for 12 days to low ${ \bf \zeta } 5 0 { \bf \mu } { \bf M \Sigma } { \bf P \ddot { 1 } } , $ ) and high Pi $6 2 5 \mu \mathrm { M }$ Pi) conditions alone or with the SynCom. No sucrose was added to the medium. b, Venn diagram showing the overlap between the PSR marker genes (core Pi) and the genes that were upregulated in Col-0 by each of the three variables analysed. The combination of bacteria and low Pi induced the majority $( 8 5 \% )$ of the marker genes. c, PHR1 negatively regulates the expression of a set of SA-responsive genes during co-cultivation with the SynCom. Venn diagram showing the overlap among PSR-SynCom DEGs, genes upregulated by BTH treatment of Arabidopsis seedlings, and the direct targets of PHR1 identified by ChIP–seq. The red ellipse indicates the 468 BTH/SA-responsive genes that were differentially expressed. A total of 99 of these genes $( 2 1 \% )$ are likely direct targets of PHR1. The yellow ellipse indicates 272 SA-responsive genes that were bound by PHR1 in a ChIP–seq experiment (see Fig. 3e). Approximately one-third of them (99 out of 272) were differentially expressed in the SynCom experiment. d, Hierarchical clustering analysis showed that nearly half of the BTH/ SA-induced genes that were differentially expressed in our experiment are more expressed in phr1 or phr1;phl1 mutants compared to Col-0 (dashed box). The columns on the right indicate those genes that belong to the core PSR marker genes (‘core’ lane) or that contain a PHR1 ChIP–seq peak (‘ChIP–seq’ lane). A subset of the SA marker genes is less expressed in the mutant lines (thin dashed box). This set of genes is also enriched in the core PSR markers and in PHR1 direct targets $P { < } 0 . 0 0 1$ ; hypergeometric test), indicating that PHR1 can function as a positive activator of a subset of SA-responsive genes. Importantly, these genes are not typical components of the plant immune system but rather encode proteins that play a role in the physiological response to low phosphate availability (for example, phosphatases and transporters). e, Examples

of typical SA-responsive genes are shown on the right along with their expression profiles in response to MeJA or BTH/SA treatment compared to Col-0. f, PHR1 activity is required for the activation of JA-responsive genes during co-cultivation with the SynCom. Venn diagram showing the overlap among DEG from this work (PSR-SynCom), genes upregulated by MeJA treatment of Arabidopsis seedlings and the genes bound by PHR1 in a ChIP–seq analysis. Red ellipse indicates 165 JA-responsive genes that were differentially expressed. Thirty-one of these $( 1 9 \% )$ ) were defined as direct targets of PHR1. The yellow ellipse indicates 96 JA-responsive genes that were bound by PHR1 in a ChIP–seq experiment. Approximately onethird of them (31 out of 96) were differentially expressed in the SynCom experiment. g, Hierarchical clustering analysis showed that almost $7 5 \%$ of the JA-induced genes that were differentially expressed in our experiment are less expressed in the phr1 mutants (dashed box). The columns on the right indicate those genes that belong to the core PSR marker genes (‘core’ lane) or that contain a PHR1 ChIP–seq peak (‘ChIP–seq’ lane). h, Examples of well-characterized JA-responsive genes are shown on the right along with their expression profiles in response to BTH and MeJA treatments obtained in an independent experiment. i, Heat map showing the expression profile of the 18 genes that were differentially expressed in our experiment and participate in the biosynthesis of glucosinolates21. In general, these genes showed lower expression in the phr1 mutants indicating that PHR1 activity is required for the activation of a sub-set of JA-responsive genes that mediate glucosinolate biosynthesis. The transcriptional response to BTH/SA and MeJA treatments is shown on the right and was determined in an independent experiment in which Arabidopsis seedlings were sprayed with either hormone. MeJA induces the expression of these glucosinolate biosynthetic genes, whereas BTH represses many of them. The gene IDs and the enzymatic activity of the encoded proteins are shown on the right. Results presented in this figure are based on ten biological replicates for Col-0 and phr1 and six for phr1;phl1. The colour key (blue to red) related to d, e, g, h, i represents gene expression as $z$ -scores and the colour key (green to purple) related to e, h, i represents gene expression as $\log _ { 2 }$ fold changes.

a

<table><tr><td></td><td>Col-0</td><td>phr1/phl1</td></tr><tr><td>LowPi</td><td>1482
(807 up; 675 down)</td><td>1161
(681 up; 480 down)</td></tr><tr><td>flg22</td><td>425
(346 up; 79 down)</td><td>701
(434 up; 267 down)</td></tr><tr><td>MeJA</td><td>2016
(1215 up; 801 down)</td><td>2216
(1358 up; 858 down)</td></tr></table>

![](images/adec53e801162748a680aea74335300d10208d678a30e643b36f42ace83df5f0.jpg)  
b

![](images/c773b9bea4b532e9e33785c7a433b88866e10e7558975435172b5c7a33c6b865.jpg)  
C

![](images/53a28cb76757a607735884e74a1b9c1e2263e2460f27955aa00f6dad652b60b7.jpg)  
d

e   
![](images/14f723bff2829a4e982b93ba86bae17dc20133e46a7f10551400500c92353134.jpg)  
Extended Data Figure 9 | PHR1 activity effects on flg22- and MeJAinduced transcriptional responses. a, Total number of differentially expressed genes $\mathrm { \mathop { F D R } } \leq 0 . 0 1$ and minimum of $1 . 5 \times$ fold-change) in Col-0 and phr1;phl1 with respect to low Pi ( $5 0 \mu \mathrm { M }$ Pi), flg22 treatment $( 1 \mu \mathrm { M } )$ and MeJA $( 1 0 \mu \mathrm { M } )$ . In this experiment, plants were grown for 7 days in Johnson medium containing 1 mM Pi, and then transferred for 12 days to low $( 5 0 \mu \mathrm { M }$ Pi) and high Pi $6 2 5 \mu \mathrm { M }$ Pi) conditions alone, or in combination with each treatment. Sucrose was added to the medium at a final concentration of $1 \%$ . b, Venn diagram showing the overlap among genes that were upregulated by chronic exposure to flg22 in Col-0 and in phr1;phl1 and a literature-based set of genes that were upregulated by acute exposure (between 8 to $1 8 0 \mathrm { { m i n } }$ ) to flg22 (ref. 23). The red ellipse indicates the 251 chronic flg22-responsive genes defined here. c, Venn diagram showing the overlap among genes that were upregulated by chronic exposure to MeJA in Col-0 and in phr1;phl1 in this work and a set   
of genes that were upregulated by MeJA treatment of Arabidopsis seedlings (between 1 h and 8 h). The red ellipse indicates the intersection of JAresponsive genes identified in both experiments. d, Col-0 and phr1;phl1 exhibit similar transcriptional activation of 426 common JA-marker genes (c) independent of phosphate concentration. As a control we used coi1-16, a mutant impaired in the perception of JA. The gene expression results are based on six biological replicates per condition. e, Growth inhibition of primary roots by MeJA. Root length of wild-type Col-0 $n = 1 2 5$ $\mathrm { ( + P i , }$ , −MeJA), 120 (+Pi, $+ \mathrm { M e J A } _ { \rho } ^ { \prime }$ ), 126 (−Pi, −MeJA), 125 (−Pi, $+ \mathrm { M e J A } )$ ), phr1;phl1 ( ${ \mathrm { . } n = 8 5 }$ , 103, 90, 80) and the JA perception mutant coi1-16 $n = 1 2 5$ , 120, 124, 119) was measured after 4 days of growth in the presence or not of MeJA with or without 1 mM Pi. Letters indicate grouping based on multiple comparisons from a Tukey post hoc test at $9 5 \%$ confidence. In agreement with the RNA-seq results, no difference in root length inhibition was observed between Col-0 and phr1;phl1.

![](images/6b513db47cf01d1262c2fac15b351940322f6aedfc89a505cfe80a724a42c89d.jpg)

![](images/c321273bb0b6532ee860591889aa6872fdc1bf8145000dd9527e346276a2ae86.jpg)

![](images/8e87c1eb04719b2ccbb5eed3a5b586128177e86edb7dee1fb2cb0cbee0121fcd.jpg)  
Extended Data Figure 10 | Number of mapped reads for each RNA-seq library used in this study. The figure shows the maximum, minimum, average and median number of reads mapping per gene for all RNA-seq libraries generated. The total number of reads mapping to genes is also shown for each library. With the exception of the minimum number of mapped reads, which is zero for all libraries, all values are shown in a log scale.