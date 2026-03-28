# Insights into the missing apiosylation step inflavonoid apiosides biosynthesis ofLeguminosae plants

Received: 5 April 2023

Accepted: 9 October 2023

Published online: 20 October 2023

Check for updates

Hao-Tian Wang1,4, Zi-Long Wang 1,4, Kuan Chen1 , Ming-Ju Yao1 , Meng Zhang1 ,Rong-Shen Wang1 , Jia-He Zhang1 , Hans Ågren2 , Fu-Dong Li3 , Junhao Li2 ,Xue Qiao 1 & Min Ye 1

Apiose is a natural pentose containing an unusual branched-chain structure.Apiosides are bioactive natural products widely present in the plant kingdom.However, little is known on the key apiosylation reaction in the biosyntheticpathways of apiosides. In this work, we discover an apiosyltransferase GuA-piGT from Glycyrrhiza uralensis. GuApiGT could efficiently catalyze $2 ^ { \prime \prime } – O \cdot$ -apiosylation of flavonoid glycosides, and exhibits strict selectivity towardsUDP-apiose. We further solve the crystal structure of GuApiGT, determine akey sugar-binding motif (RLGSDH) through structural analysis and theoreticalcalculations, and obtain mutants with altered sugar selectivity through proteinengineering. Moreover, we discover 121 candidate apiosyltransferase genesfrom Leguminosae plants, and identify the functions of 4 enzymes. Finally, weintroduce GuApiGT and its upstream genes into Nicotiana benthamiana, andcomplete de novo biosynthesis of a series of flavonoid apiosides. This workreports an efficient phenolic apiosyltransferase, and reveals mechanisms forits sugar donor selectivity.

The naturally occurring D-apiose is a unique branched-chain pentosewith a tertiary alcohol group, and is considered as “one of nature’switty games” 1 . The name “apiose” is derived from apiin (apigenin 7-O-apiosy $( 1  2 )$ )-glucoside), the first apiose-containing natural productisolated from parsley in $1 8 4 3 ^ { 2 }$ . In plants, apiose is synthesized as uri-dine diphosphate-apiose (UDP-Api) from UDP-glucuronic acid (UDP-GlcA) catalyzed by UDP-apiose/UDP-xylose synthase (UAXS)3,4 . It is alsoa key component of complex cell wall polysaccharides, which playimportant roles in plant growth and development5 . The apiose-containing plant pectic polysaccharide RG-II has been a componentof human diet for a long history, and exhibits notable benefits tohuman health6 .

More importantly, apiose is an important building block of var-ious natural products. Around 1200 apiosides have been identified

from plants1 , thus far, including phenolic glycosides (e.g. flavonoids,coumarins, and lignans), triterpenoid saponins, and cyanogenic gly-cosides. Among them, flavonoid apiosides represent the largest group,and are believed to play hormone-like roles in plant growthregulation7 . In the structures of flavonoid apiosides, the apiosyl residueis usually linked to $2 ^ { \prime \prime } – \mathrm { O H }$ of sugar moieties through a $\beta$ -O-glycosidicbond. It may also be linked to 3″-OH or $6 ^ { \prime \prime } – 0 \mathsf { H }$ of sugar moieties or theflavonoid skeleton directly8 . Leguminosae is one of the most fre-quently reported plant families with flavonoid apiosides1 . Glycyrrhizauralensis Fisch. is a worldwide popular medicinal plant of the Legu-minosae family. Its roots and rhizomes are used as the famous Chineseherbal medicine Gan-Cao (licorice)9 . Licorice contains abundant fla-vonoid apiosides (around $1 \%$ of the dry weight) as bioactive com-pounds, particularly liquiritin apioside and isoliquiritin apioside


a


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/6b744aec1776dd0e3783bcf2a303d25c39825a263c8cda2c7f64572deb6e7ae1.jpg)



Glycyrrhiza uralensis


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/0e0d823a12d298194abf538cd20b32bc61cf3be3810d0f6c94324465306df8a8.jpg)



Gan-cao



b


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/6b1ae61d17ab71bddb883d659413f9e3c368c36f5db72bce81f91b9fd92e8698.jpg)



Liquiritin


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/3dadf0a09aaef6be237acd116342ba5b1f704cca709069285d5fbd66c1c4d043.jpg)



1a



Liquiritin apioside


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/7cf3d33a54091538eb5481d3da549c6d64768fc97b181064eb74896917c45395.jpg)



Isoliquiritin


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/7fcb0ef684c852d30f44b77ed9472f622471c752d1fe69fdcdd4cd12cc89481f.jpg)



2a



Isoliquiritin apioside


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/33a42a5afb9e0188e4bd6936f5e6ab50213d1ad27be864058d0b6074ca4c8b9f.jpg)



c


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/6b0d717685ef3663203ade8a79ea0a23f7559a235faae0bc3dd55ec13a5e5794.jpg)



Coumaroyl-CoA


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/024abadc13f23c151a5cc3ab770e3b56a97823cc463605bac642b606d8532aaf.jpg)



Malonyl-CoA


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/ec7fc5cbcff2914405e49c1d86ff423c5ff98682d1abd96d677b41deed73e61b.jpg)



Naringenin chalcone


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/d58536259654d5e32f40f187eae8d1dfa0063964d6bc215cf46a152d48846b18.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/5e611010b2dc6bd0ef951184171ff93d5ac0cfa4b4f62d892c0ac9e5b8a5954c.jpg)



Isoliquiritigenin


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/164eaa77d3778d297e1cebcaf66b48cb072a5beba0a2564bdd5c85758aa0959a.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/5ccc3981d84f5fc288a40c3cc2b60a7c67c67274a128530e035bf1a603d58cd4.jpg)



Liquiritigenin


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/71e76f306fd35e06ddf1361ffaf7f88c4e43541441170fe8198c01bd6d0bbd47.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/9771ce3c680efbf65567096101c100c038d4d3e2f90f1bd1008be0f13a9f4a70.jpg)



1(2)



(iso)Liquiritin


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/84f42f59967de1b13bf81af9d58cad04a0ae5bea4a6497ec9822f38a47542a91.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/b32aef4464c04e4fa5f0321bd2661e3cbaa8381f58af1eb48db5db949f986f07.jpg)



1a(2a)



(iso)Liquiritin apioside



d


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/09b819644e829b23d1f27ac072b93cba7cde6f749d6a1f92481284fc52577274.jpg)



e


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/ba430bf87d68bfd5beaceaad0216db2b346413e4cbe4e57a7e36251be1606e5a.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/41ec820de7fae413115f73dcd4ec524e15664604bb957d8e04cd7ad8d4065a79.jpg)



Fig. 1 | Bioinformatic analysis of candidate apiosyltransferase genes from Gly-cyrrhiza uralensis. a Pictures of Glycyrrhiza uralensis plant and the Chinese herbalmedicine Gan-Cao. b LC/MS analysis of the roots, cortexes, and leaves of G. ura-lensis, showing extracted ion chromatograms (XICs) of 1, 2, 1a and 2a. c The pro-posed biosynthetic pathway of 1a and 2a. CHS, chalcone synthase; CHR, chalcone



reductase; CHI, chalcone isomerase. d Co-expression analysis of G. uralensis tran-scriptomes using GuCHS and GuCHR as bait genes. The circle of dots representsgenes co-expressed with GuCHS and GuCHR. e Expression levels of candidate genesin the transcriptomes of different plant parts of G. uralensis. Two replicates weretested for each part $( n = 2 )$ .


(Fig. 1a)10. Among them, liquiritin apioside (liquiritigenin 4′-O-apio-syl(1→2)-glucoside) shows potent antitussive activities11.

Currently, flavonoid apiosides are mainly obtained throughextraction and purification from plants. The procedure is laboriousand time consuming. The unique structure of apiose has attractedorganic chemists to develop new methods to synthesize apiosides.However, these methods usually take multiple steps, and needexpensive metal catalysts12. In plant biosynthesis, the formation ofglycosidic bond is usually catalyzed by uridine diphosphate-dependent glycosyltransferases (UGTs)13. The UGT-mediated glycosy-lation reactions take only one step, and show high catalytic efficiency

and selectivity. Thus far, a big family of plant UGTs have beenreported14, and most of them accept popular sugar donors such asUDP-glucose (UDP-Glc), UDP-xylose (UDP-Xyl), UDP-galactose (UDP-Gal), UDP-rhamnose (UDP-Rha), UDP-arabinose (UDP-Ara), and UDP-glucuronic acid (UDP-GlcA)14,15. It is noteworthy that no UGTs couldaccept UDP-Api as sugar donor except for the recently reportedUGT73CY2 which could accept a triterpenoid saponin substrate16.

In this work, we report an efficient phenolic apiosyltransferaseGuApiGT from G. uralensis, and dissect mechanisms for its sugar donorselectivity towards UDP-Api through crystal structure analysis, theo-retical calculations, and mutagenesis. A key motif (RLGSDH) of

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/8ecf0db4369822dbfd1bcb58c59da1a143207fc60d9357dcd4d462c8fcd6fa37.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e7ad6a8e7fd22a2301f8da48a2b8d234ee8ab50d6c7bee7bd011cb5d7cd945aa.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/eeb23a47707dc033b7e937f349ebdbfc9879fd8d2c4a5a9808c2c879b5072c62.jpg)



Fig. 2 | Functional characterization of GuApiGT. a Catalytic function of GuApiGTusing 1 and 2 as sugar acceptors. The acceptors were incubated with GuApiGT andan UDP-Api supply system (UDP-GlcA, UAXS, NAD+ ) in pH 8.0 $( 5 0 \mathrm { m M } \mathrm { N a H } _ { 2 } \mathrm { P O } _ { 4 } -$



${ \sf N a } _ { 2 } { \sf H P O } _ { 4 }$ buffer) at $3 7 ^ { \circ } \mathrm { C }$ for 3 h. b (-)-ESI-MS and ${ \mathsf { M } } { \mathsf { S } } ^ { 2 }$ spectra of 1a. For compoundsidentification, see Fig. 1.


GuApiGT led to the discovery of a group of apiosyltransferases fromLeguminosae plants. Furthermore, we realized the de novo biosynth-esis of a series of flavonoid apiosides in Nicotiana benthamiana.

# Results and discussion

# Bioinformatic analysis

G. uralensis contains (iso)liquiritin apioside as major compounds. Thehigh yield strongly suggests the presence of apiosyltransferases in thisplant. To discover the apiosyltransferase gene, we conducted co-expression analysis17,18. As the contents of (iso)liquiritin apioside (1aand 2a) in the roots were higher than those in the cortex and leaves,transcriptomes of these three parts were analyzed $\scriptstyle ( n = 2$ , Fig. 1b). Allhigh expression genes $\left( \mathsf { F P K M } \ge 2 0 \right)$ in the roots were used as candi-dates. GuCHS and GuCHR were used as the ‘bait’, because they are keygenes involved in the biosynthesis of (iso)liquiritigenin (1′ and 2′),which are precursors of (iso)liquiritin apioside (Fig. 1c).

Through co-expression analysis, a total of 289 genes wereobtained $( \boldsymbol { \mathsf { r } } \geq 0 . 8 ,$ Spearman correlation coefficient) (Fig. 1d). Pfam, NR,and Swissprot databases annotated four candidate UGT genes. Asidefrom two previously reported triterpenoid glycosyltransferases(GuRhaGT and UGT73P12)19,20, the other two unknown genes showedvery similar expression patterns with GuCHS and GuCHR (Fig. 1e). In thephylogenetic tree, MSTRG.23171.4 was clustered with flavonoid $2 ^ { \prime \prime } – O \cdot$ -

glycosyltransferases including $Z \mathrm { j } 0 \mathbf { G } \mathbf { T } 3 8 ^ { 2 1 }$ and $\mathsf { T c O G T } 4 ^ { 2 2 }$ , and wasconsidered as the candidate apiosyltransferase gene (Supplemen-tary Fig. 1).

Molecular cloning and functional characterization of GuApiGTBased on the above bioinformatic analysis, we cloned MSTRG.23171.4from the cDNA of G. uralensis by RT-PCR (Supplementary Data 1). Thegene in pET28a(+) vector was then expressed in E. coli BL21(DE3) andpurified by His-tag affinity chromatography (Supplementary Fig. 2).As uridine diphosphate-apiose (UDP-Api) is commercially unavail-able, we introduced the UDP-apiose/UDP-xylose synthase (UAXS)of Arabidopsis thaliana into the enzyme catalysis system (Fig. 2a)3 .This system was used to provide UDP-Api in follow-up experiments.Liquid chromatography coupled with mass spectrometry (LC/MS)analysis and reference standards comparison indicatedMSTRG.23171.4 almost completely converted liquiritin (1) and iso-liquiritin (2) into their ${ 2 ^ { \prime \prime } { \cdot } O }$ -apiosides 1a and 2a, respectively (Fig. 2b).Although UAXS could also produce UDP-Xyl, no products wereobserved when UDP-Xyl was added (Supplementary Fig. 3). Theseresults confirmed MSTRG.23171.4 as an apiosyltransferase, and it wasnamed GuApiGT. To our best knowledge, this is a previously uni-dentified apiosylation pathway for the biosynthesis of phenolicapiosides.

The gene sequence of GuApiGT (GenBank accession numberOQ201607) contains an open reading frame (ORF) of 1365 bp encoding454 amino acids (Supplementary Table 1). It is named as UGT79B74 byUGT Nomenclature Committee. The biochemical characteristics ofrecombinant GuApiGT were investigated using 2 as the acceptor.GuApiGT showed its maximum activity at $\mathsf { p H } 8 . 0$ and $3 7 ^ { \circ } \mathrm { C } .$ . Somedivalent cations could suppress the catalytic activities (SupplementaryFig. 4). Kinetic analysis demonstrated the $K _ { \mathfrak { m } }$ value of $2 . 5 9 \pm 0 . 2 3$$\mathsf { \mu } \mathsf { m o l } \cdot \mathsf { L } ^ { - 1 }$ for 2, at the presence of saturated UDP-Api. The $k _ { \mathrm { c a t } }$ value was$0 . 1 1 \mathsf { s } ^ { - 1 }$ , and the $k _ { \mathrm { { c a t } } } / K _ { \mathrm { { m } } }$ was $0 . 0 4 2 \ s ^ { - 1 } { \cdot } | | \mathrm { m o l ^ { - 1 } { \cdot } L }$ (Supplementary Fig. 5).

To explore the catalytic promiscuity of GuApiGT, 65 substrates (1-65) were tested. LC/MS analysis revealed that GuApiGT showed highsubstrate promiscuity and high catalytic efficiency. It could accept 37glycosides (1-37) of flavonoids, lignans, or coumarins, but not freeflavonoids (52-57, Fig. 3, Supplementary Fig. 6, and SupplementaryTables 2, 3). The products were identified as $o$ -apiosides according tothe diagnostic fragment ions [M-H-132]- and [M-H-132-162]- in the MS/MS spectra (Supplementary Figs. 7–42). For 14 substrates, the con-version rates were $58 0 \%$ .

GuApiGT mainly catalyzed the apiosylation of flavonoid 7- or 4′-O-glycosides. The aglycones could be flavanones (1, 3-6), chalcones (2, 7-8), flavones (9-22), isoflavones (23-27), flavonols (28-31), and dihy-drochalcone (32). For $^ { 7 , 4 ^ { \prime } }$ -di-O-glycosides like 8, 19 and 29, two pro-ducts were observed, indicating apiosylation at either site. GuApiGTcould also catalyze flavonoid 5-O-glycoside (20), but not 3-O-glyco-sides (38-46, Supplementary Fig. 6). It is noteworthy that GuApiGTcould accept flavone 6-C-glycosides (21 and 22) and xanthone C-gly-cosides (33 and 34), but not isoflavone 8-C-glycoside (47) or flavone di-C-glycosides (48-51). It could not recognize other types of glycosidesincluding triterpenoid glycosides (58-65).

To fully identify structures of the products, we purified six $2 ^ { \prime \prime } – O \cdot$ -apiosides (6a, 15a, 24a, 27a, 32a, and 35a) from scaled-up catalyticreactions. All the products are unreported compounds except for$\mathbf { 1 5 a } ^ { 2 3 }$ . Their structures were established by HR-ESI-MS, together with1D and 2D NMR spectroscopic analyses (Supplementary Figs. 43–81).The $^ { 1 3 } \mathsf { C }$ NMR and DEPT spectra showed additional signals at $\delta _ { \mathsf { C } }$ 108.8(C-1′′′, CH), 76.2 (C-2′′′, CH), 79.4 (C-3′′′, C), 74.0 (C-4′′′, $\mathrm { C H } _ { 2 } )$ , and 64.2$( \mathbf { C } { \cdot } 5 ^ { \prime \prime \prime }$ , $\mathrm { C H } _ { 2 } )$ ), which are characteristic for an apiosyl group. In theHMBC spectra, the long-range correlation between $\mathbf { H } { - } \mathbf { 1 } ^ { \prime \prime \prime }$ and $\mathbf { { C } } { \cdot } 2 ^ { \prime \prime }$indicated the apiosyl moiety was attached to $2 ^ { \prime \prime }$ -hydroxy of the glu-cose residue.

The RLGSDH motif is critical for the selectivity towards UDP-ApiInterestingly, GuApiGT showed strict sugar donor selectivity towardsUDP-Api. It could not recognize seven other donors (Fig. 3c). In orderto dissect the mechanisms, we obtained the apo crystal structure ofGuApiGT with a resolution of $2 . 2 \mathring \mathrm { A }$ (Fig. 4a and SupplementaryTable 4). Due to the low amino acid sequence identity with reportedstructures, the structure of GuApiGT was solved by molecular repla-cement with the help of AlphaFold2 simulation (SupplementaryFig. 82)24. The crystal contains two highly similar molecules with a rootmean square deviation (RMSD) of $1 . { \overset { - } { 1 } } { \overset { - } { \mathbf { A } } }$ , and adopts a canonical GT-Bfold consisting of two Rossmann-like $\beta / \alpha / \beta$ domains that face eachother and are separated by a deep cleft. The N-terminal domain (NTD,residues 1-242 and 436-454) and the C-terminal domain (CTD, residues243-435) are responsible primarily for sugar acceptor and sugar donorbinding, respectively25.

It was regretful that we failed to obtain complex structures aftermany attempts including soaking experiments. Fortunately, the loca-tion of UDP in reported UGT complex structures is highly conservative(Fig. 4b and Supplementary Table 5). Based on the structures ofGgCGT/UDP-Glc, GgCGT/UDP-Gal, and UGT89C1/UDP-Rha, wesimulated the UDP-Api binding pocket of GuApiGT (Fig. $4 \mathbf { c } ) ^ { 2 6 , 2 7 }$ . It isnoteworthy that a part of UDP-sugar binding region of GuApiGT isdifferent from that of GgCGT (glucosyltransferase), SbCGTb

(arabinosyltransferase)28, or UGT89C1 (rhamnosyltransferase)27. Thisregion is composed of the $\mathsf { R } ^ { 3 6 8 } \mathsf { L } ^ { 3 6 9 } \mathsf { G } ^ { 3 7 0 } \mathsf { S } ^ { 3 7 1 }$ loop and the start of α helix$( \mathbf { D } ^ { 3 7 2 } \mathsf { H } ^ { 3 7 3 } )$ , which forms a large secondary structure compared withother UGTs (Fig. $4 \mathrm { d } ) ^ { 2 6 - 3 0 }$ . Moreover, the plant secondary product gly-cosyltransferase box (PSPG box) of GuApiGT contains 45 amino acidsdue to the additional S371 residue (Supplementary Fig. 83). In contrast,this highly conserved box for all previously reported plant UGTscontains 44 amino acids14,25.

To analyze the potential interactions of UDP-Api with key resi-dues, we obtained the initial GuApiGT/UDP-Api complex structure bysuperimposing the UDP part of UDP-Api to the reported bindingpocket of other UGTs. Subsequently, the sugar acceptor was dockedinto the active site using the Glide module in Schrodinger Suite (Sup-plementary Fig. 84). Constraints were added to make the acceptor’sglucose moiety oriented to UDP-sugar moiety. To optimize the con-figuration of ligands in GuApiGT, we conducted 100-ns MD simulations(Supplementary Fig. 85)31. Representative snapshots of GuApiGT/UDP-Api/2 complex model indicate that D372, H373, and I136 could formhydrogen bonds with the apiose OH group (Fig. 4e and SupplementaryFig. 86). Moreover, R368 could change its initial state, and the sidechain could flip into the pocket to form π-π/cation-π interactions andhydrogen bonds with H373, and hydrogen bonds with UDP. We pro-pose that the additional S371 residue could increase flexibility of theloop, thus enables R368 to interact with H373 for the binding of UDP-Api. When these amino acids were mutated to alanine, the activity ofGuApiGT was decreased (Supplementary Fig. 87). We further simu-lated the structures of GuApiGT/UDP-Xyl/2 and GuApiGT/UDP-Glc/2(Supplementary Fig. 88). The configuration of Glc in the complexstructure is unreasonable due to a twist conformation between boatand chair, whereas 6-OH could suppress the attack of UDP-sugar C1′′′to 2″-OH of 2 (Supplementary Fig. 89). For the binding of Xyl, the MM/GBSA (molecular mechanics, the generalized Born model and solventaccessibility) binding free energy of GuApiGT/UDP-Xyl/2 is higher thanthat of GuApiGT/UDP-Api/2 (Supplementary Fig. $9 0 ) ^ { 3 2 }$ . These resultswere consistent with our observation that GuApiGT could not acceptUDP-Glc or UDP-Xyl.

For inverting GTs, the distance between the hydroxyl oxygenatom of sugar receptor $( 0 2 ^ { \prime \prime } )$ and $\mathbf { C 1 } ^ { \prime \prime \prime }$ of UDP-sugar, as well as theangle of $\mathbf { O } 2 ^ { \prime \prime }$ , $\mathbf { { C 1 } ^ { \prime \prime \prime } }$ , and the UDP oxygen atom next to $\mathbf { { C 1 } ^ { \prime \prime \prime } }$ (O3), arecritical for the glycosylation reaction13. We performed 500-ns well-tempered metadynamic simulations using the distance (CV1: $0 2 ^ { \prime \prime } { \cdot } \mathbf { C } 1 ^ { \prime \prime \prime } )$ and angle (CV2: O2′′-C1′′′-O3) as the first and second collective vari-ables (CV), respectively33. Optimal conformations should have CV1lower than $4 . 5 \mathring \mathrm { A }$ and CV2 greater than $9 0 ^ { \circ }$ . As shown in Fig. 4f, onlyUDP-Api, but not UDP-Glc or UDP-Xyl, exhibited reasonable localminima of free energy surfaces (FES).

We further conducted QM/MM calculations using the ONIOMmethod implemented in Gaussian 16 (rev C.01) to derive the transitionstates34. CV1/CV2 values in the optimized transition state (TS) structureis $2 . 1 \mathring { \mathbf { A } } / 1 5 2 . 1 ^ { \circ }$ (Fig. 4g, Supplementary Data 2-4). The activation barrierand related product energy for the transfer of apiose is 14.5 and-1.3 kcal/mol, respectively (Fig. 4h). During the process to form theglycosidic bond between $\mathbf { O } 2 ^ { \prime \prime }$ of 2 and $\mathbf { { C 1 } ^ { \prime \prime \prime } }$ of UDP-Api, H18 couldpartially deprotonate 2, with the assistance of D115. Once the reactionis completed, D115 is protonated in the product complex. On the otherhand, when we remove the atomic charge of outer MM region resi-dues, R368 and E272 could notably impact the activation barrier, withΔΔE of 12.06 and 21.67 kcal/mol, respectively (Supplementary Table 6and Supplementary Fig. 91).

# Protein engineering of GuApiGT to change its sugar donorselectivity

To verify the role of RLGSDH motif on sugar donor selectivity ofGuApiGT, we conducted site-directed mutagenesis. First, we deletedthe additional S371, and the catalytic activity was decreased (Fig. 5a).

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/7985882a81bf91007752d602b77501695b1fa520616e7615e9245b1dd92823e8.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/bce7e1938dc442c89831e00f0f28a5e6756288acf5c80c8425336b787ddb53bf.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/bab14bcedbb96789c737fce722485390077a0ac2947bcdeb0e762c509132df98.jpg)



Fig. 3 | Substrate promiscuity of GuApiGT. a Conversion rates of apiosylatedproducts of different types of substrates catalyzed by GuApiGT. b Structures ofsubstrates 1-37 and part of the products. The regular triangles represent productspurified and identified by NMR; The inverted triangles represent compoundsidentified by comparing with reference standards; The asterisks represent



endogenous compounds of G. uralensis. c Structures of sugar donors and theconversion rates. 1 was used as sugar acceptor. Data are presented as meanvalue $\pm \mathsf { S D }$ $\scriptstyle \overbar { n } = 3$ biologically independent samples) (3a and c). The source dataunderlying Fig. (3a and c) are provided in a Source Data file.


Then we replaced H373 with glutamine, which is usually the last resi-due of PSPG box of UDP-Glc-preferring UGTs, as glutamine could formhydrogen bonds with 2-OH and 3-OH of glucose. The H373Q mutantalso showed decreased activity. Interestingly, the S371/H373Q mutantcould accept UDP-Xyl as sugar donor (Fig. 5a, b and SupplementaryFigs. 92, 93). Similarly, we deleted R368, L369, and G370, respectively.

All the double mutants could accept UDP-Xyl, and L369/H373Q was themost active one, with a conversion rate of almost $100 \%$ .

The structures of glucose and xylose differ in the $\mathrm { C H } _ { 2 } \mathrm { O H }$ sub-stituent at C-5. In our previous report, T145 in GgCGT is a key aminoacid to form hydrogen bond with 6-OH of UDP-Glc26. T145 is mapped toIle136 in GuApiGT (Supplementary Fig. 94). Thus, we continued to


a


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e0ef9a64e8dc6159a31bc6d277bed41efe4423ad654b6f3841ef5d0975de9d35.jpg)



PDB ID: 8HZZ (2.2 Å)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/059a9f345219cb7fbf3d07bfb55c3a73660c9ba33d2c44f271ac44cbf4d3bf06.jpg)



Representative sugar donor



c


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/58399085d3823af7b109f428b45b67db5145115ebe74775dd7661ff6439a8e91.jpg)



Sugar donor binding pocket


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/c77fc874ed5a0ce40278a0b5e006e0f7ddf19033427b43e7651d8971585913a7.jpg)



d


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/7dc557d5e4e1fb0f92a90426cfee10e9c3ec17d193ecc9cfec81395d433b7841.jpg)



e


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/86e07a31d890fc81fe38530127369429f7bb961f911f8e6ab8c9593d9cca10bd.jpg)



f


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/4e9d8ee02b7455250392609f1858577d58b5f6e9d2261b266c6218ac7956c84f.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/2138d72d67ac99ccbd4e9be1882cadd28fbb9f4b3744b57737f4997c8fa65e01.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e7772028e7ddda56496041e774f5ef7d5ef368586d453bd81df293012cabc70c.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/7e957d9ffb58995961e697d5a64c80d676a5c1b6b0b7f86f17411f7d0085ed66.jpg)



h


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/203dd71049f3b7e762dd7b716c03e83ee1a4234530195a6131022995b913c11d.jpg)


construct a series of triple mutants. I136T/G370/H373Q showed thehighest catalytic activity to accept UDP-Glc (Fig. 5a, b and Supple-mentary Fig. 95). The co-incubation of UDP-Xyl and UDP-Glc furtherconfirmed the significance of T136 on the preference towards UDP-Glc(Supplementary Fig. 96).

The L369/H373Q and I136T/G370/H373Q mutants could catalyzea series of substrates using UDP-Xyl and UDP-Glc as sugar donor,

respectively (Fig. 5c and Supplementary Figs. 97–122). Products 32band 3c were purified from scaled-up reactions and their structureswere identified by NMR analysis as ${ 2 ^ { \prime \prime } { \cdot } O }$ -xyloside of trilobatin and $2 ^ { \prime \prime } – O \cdot$ -glucoside of naringenin, respectively (Supplementary Figs. 123–132).

We further employed hydrogen-deuterium exchange mass spec-trometry (HDX-MS) to elucidate the protein conformation of GuA-piGT, and L369/H373Q and I136T/L369/H373Q mutants in the solution

Fig. 4 | Structural basis for the UDP-apiose selectivity of GuApiGT. a The crystalstructure of GuApiGT. b Superimposition of 26 plant crystal structures (the sugardonors are highlighted). c The sugar donor binding pocket of GuApiGT. d The sugarbinding region in crystal structures of representative ApiGT, GlcGT (GgCGT, PDBID: 6L5P), AraGT (SbCGTb, PDB ID: 6LFZ), and RhaGT (UGT89C1, PDB ID: 6IJA). TheRLGSDH motif in GuApiGT is highlighted as yellow sticks. e A representative con-figuration of GuApiGT/UDP-Api/2 extracted from MD simulations. The hydrogen-bond interactions and π-π/cation-π interactions are shown as yellow and purpledashes, respectively. The key amino acids interacted with ligands are highlightedusing sticks. The unique R368 is depicted as orange sticks, the others as blue. Theother amino acids in key motif are depicted using lines. f Metadynamic simulations

of GuApiGT with different sugar donors (Api, Xyl, and Glc). CV1, the distance of O2′′-C1′′′ (Å); CV2, the angle of $0 2 ^ { \prime \prime } { \cdot } { \bf { C } } 1 ^ { \prime \prime \prime } { \cdot } { \bf { O } } 3$ (°). g QM/MM optimized geometry of thetransition state (TS) at the theory of B3LYP/6-311++G(2d,2p):AMBER with theelectronic embedding scheme and thermal zero-point energy calculated from thetheory of B3LYP/6-31G(d):AMBER. The QM region atoms, hydrogen bonds, and keyangle and distances are highlighted in green sticks, yellow dashes, and magentadashes, respectively. The MM region atoms are depicted using lines. h An energyprofile for the apiosylation of GuApiGT. RC, reactant complex; TS, transition state;PC, product complex. The source data underlying Fig. (4f) are provided in a SourceData file.

state35,36. The peptide coverage was $9 0 . 1 \%$ (Supplementary Figs. 133,134). Compared with the wild type, peptide L363-D372 of the mutantsshowed decreased deuterium uptake, indicating the $\mathsf { R } ^ { 3 6 8 } \mathsf { L } ^ { 3 6 9 } \mathsf { G } ^ { 3 7 0 } \mathsf { S } ^ { 3 7 1 }$loop became compact and rigid after mutagenesis, and thus may beable to interact with xylose or glucose (Fig. 5d, e and SupplementaryFigs. 135, 136). The L135-E156 peptide of I136T/L369/H373Q mutantexhibited noticeable increase of deuterium uptake, verifying the sig-nificance of T136 in recognizing UDP-Glc (Supplementary Fig.137). Forthe PSPG box, the R316-M334 and I335-F344 peptides only showedminor changes, while I345-Q362 and L363-D372 changed significantlyupon mutagenesis. This result indicated the R316-F344 and I345-H373parts were responsible for the binding with UDP and the sugar moiety,respectively.

The recognition of UDP-Xyl and UDP-Glc was also supported bythermal shift assay37. Compared to the WT, the melting temperature$( T _ { \mathfrak { m } } )$ of the mutants increased by $1 . 2 { \cdot } 5 . 4 ^ { \circ } \mathrm { C }$ and $0 . 9 { \cdot } 2 . 7 ^ { \circ } \mathrm { C } ,$ , respectively,when co-incubated with UDP-Xyl or UDP-Glc (Fig. 5f). These resultsproved that UDP-Xyl and UDP-Glc could bind with the mutant proteinand increase stability. We simulated the structure models of L369/H373Q mutant/UDP-Xyl/2 and I136T/L369/H373Q mutant/UDP-Glc/2complexes (Supplementary Fig. 138a). The binding free energies andlocal minima from metadynamic simulations were consistent with theexperimental results (Supplementary Fig. 138b, c). Moreover, thevolume of sugar binding pocket decreased upon mutagenesis (Sup-plementary Fig. 138d).

# Protein engineering of Sb3GT1 to gain apiosylation activity

To further prove the critical role of the RLGSDH motif in UDP-Apiselectivity, we conducted site-directed mutagenesis of Sb3GT1.Sb3GT1 is an efficient plant flavonoid 3-O-glycosyltransferase whichcould accept at least five sugar donors except for UDP-Api38. It shares$1 9 . 8 \%$ amino acid sequence identity with GuApiGT (SupplementaryFig. 139). We solved the complex crystal structure of Sb3GT1/UDP at$1 . 9 \mathring { \mathsf { A } }$ resolution (Fig. 6a and Supplementary Table 7), and the RMSDcompared with GuApiGT is $2 . { \dot { 6 4 } } { \dot { \mathbf { A } } }$ . The RLGSDH (368-373) motif inGuApiGT is mapped to FFGDQ (372-376) of Sb3GT1.

Based on structural analysis, we inserted a serine residue into themotif and constructed the 375S/Q377H mutant of Sb3GT1, as well asthe F372R/Q376H and F372R/375S/Q377H mutants. All the threemutants could catalyze kaempferol (66) into its 3-O-apioside, accord-ing to the characteristic $[ \mathsf { Y } ^ { 0 } \cdot \mathsf { H } ] ^ { - }$ ion at $m / z 2 8 4$ in LC/MS analysis (Fig. 6band Supplementary Fig. $1 4 0 ) ^ { 3 8 }$ . We further solved the crystal structureof Sb3GT1 375S/Q377H mutant in complex with UDP-Glc at 1.43 Åresolution (Fig. 6c and Supplementary Table 7). The motif structure ofthe mutant was larger than that of WT, which may be critical for thesugar donor selectivity towards UDP-Api. Interestingly, GuApiGT couldnot accept free flavonoids or 3-O-glycosides, which could be inter-preted by molecular docking and MM/GBSA binding free energy cal-culations (Supplementary Fig. 141).

# The RLGSDH motif is general for leguminosae plants

To discover more apiosyltransferases, we analyzed the online planttranscriptome databases39. A total of 121 candidate genes were

discovered from 39 plant species, using the unique 45-amino acidPSPG box as a filter (Supplementary Table 8). Interestingly, all thespecies belong to Leguminosae family. These genes were closelyclustered with GuApiGT in the phylogenetic tree, except for threegenes clustered with ZjOGT38 and TcOGT4 (Fig. 7a).

Majority of these ApiGT genes contain the RLGSDH motif in thePSPG box (Fig. 7b). Among the 39 plants, P. thomsonii, S. suberectus, G.glabra, and G. inflata had been reported to contain flavonoidapiosides14,40,41. Thus, we cloned PtApiGT, SsApiGT, GgApiGT, andGiApiGT from the plants, and identified them as apiosyltransferases byenzyme catalysis reactions (Fig. 7c and Supplementary Fig. 142). Theiramino acid sequences were highly conservative, with identity of$9 0 . 0 7 \%$ (Supplementary Fig. 143). Very recently, Reed et al. reportedUGT73CY2 as a triterpenoid apiosyltransferase, which has a PSPG boxof 44 amino acids16. After submission of the present work, Yamashitaet al. reported UGT94AX1 from Apium graveolens (Apiaceae family),which also contains a 44-amino acid PSPG box42. Their amino acidsequence identity with GuApiGT was $2 1 \%$ and $23 \%$ , respectively. Thus,the unique 45-amino acid PSPG box and the RLGSDH motif may begeneral for apiosyltransferases from Leguminosae plants.

# De novo biosynthesis of flavonoid apiosides in tobacco

Liquiritin apioside (1a) and isoliquiritin apioside (2a) are importantbioactive compounds in the Chinese herbal medicine Gan-Cao(licorice)10. Thus far, they could only be prepared by purificationfrom licorice, which needs to grow for at least 3-4 years. The discoveryof GuApiGT paved the way for their de novo biosynthesis. While E. coliand yeast are widely used as chassis for de novo biosynthesis of naturalproducts, the yields for flavonoids are usually low43,44. Thus far, themost productive engineering system for flavonoid glycosides had ayield of $1 0 0 \mathrm { m g / L }$ . Nicotiana benthamiana (tobacco) is a rapid growingand high biomass plant45,46, and may be a suitable host for the pro-duction of flavonoids. The de novo tobacco biosynthesis of severalimportant natural products has been achieved, including taxadiene-5α-ol, colchicine, and (-)-deoxypodophyllotoxin47–50.

To evaluate the suitability of N. benthamiana as a potential plat-form for the production of apiosides (Fig. 8a), Agrobacterium-medi-ated transient expression of GuApiGT was performed using pEAQ-HT-DEST1 with a 35 S promoter51. UAXS was co-infiltrated into tobacco withGuApiGT to supplement the UDP-apiose donor. Isoliquiritin (2) andUDP-GlcA were infiltrated into the leaves after GuApiGT and UAXSexpression for 3 days. Leaf discs from the infiltrated parts were sam-pled 4 days post-infiltration. The samples were extracted and analyzedby LC/MS. Product 2a could be detected at noticeable amounts(Supplementary Fig. 144). To optimize the agrobacterium strain,pEAQ-HT-DEST1-GuApiGT was transferred to five Agrobacteriumstrains, including AGL1, GV3101, C85C1, LBA4404, and GV2260. Amongthe strains, GV2260 showed the highest conversion and was selectedas the most suitable strain for the expression of GuApiGT (Fig. 8b).

For the de novo biosynthesis of (iso)liquiritin apiosides, wedesigned 3 modules, including the flavonoid aglycone module (mod-ule 1), UDP-donor module (module 2), and glycosyltransferase module(module 3). For module 1, AtPAL, AtC4H, At4CL, AtCHS and GuCHR

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/8adeaf0080dac75a17c37c98469b0b4bc34e8ce081adbbba3445de9d867300db.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/c1101c097ecc588bf32e52a5d797dff3d0ef857c75803fca5f63ff4fba50c487.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/2cfecdb0f7cdc49740a7a9ee992b05e615ef8262e5272fd8868d0d6f3be17430.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/a0a06e1471edae14590458c21217c54ec0ee54d8bb766b0c7e330d2b36fb42b0.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e3a876104c8bd0befc45b243d213c1569aa5ecc35483bc7e641787e9b08df4b6.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/f65ffe24b89d955c0050be1124222fd3f513936a1c7e267ebf9b77f5f103eb37.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/224902aba39749825dbc7c8ab24c5b77ccc2f0cfe0ecef9190d2530a6ac15348.jpg)



Fig. 5 | Alteration of sugar donor selectivity of GuApiGT mutants. a The gly-cosylation conversion rates of the wild type (WT) and mutants, using 2 as sugaracceptor, and UDP-Api, UDP-Xyl, or UDP-Glc as sugar donor. b HPLC chromato-grams of enzyme catalytic products. c Substrate promiscuity of GuApiGT mutantsL369/H373Q and I136T/G370/H373Q. For substrate structures, see Fig. 3. d Deu-terium uptake differences of L369/H373Q-WT and I136T/L369/H373Q-WT for allpeptides in the HDX-MS experiments, calculated as the sum of all time points. The



enzyme secondary structure and the PSPG box is shown on the top. e Deuteriumuptake plots of peptides 135-156 and 363-372 at different time points. f Proteinthermal shift assay measuring the changes in melting temperature $( \Delta T _ { \mathrm { m } } )$ of WT andmutants. Top, co-incubated with UDP-Xyl; bottom, co-incubated with UDP-Glc.Data are presented as mean values $\pm \mathsf { S D }$ $\scriptstyle ( n = 3$ biologically independent samples)(5a, c and f). The source data underlying Fig. (5a, c–f) are provided in a SourceData file.


were used to synthesize isoliquiritigenin (2′). Pgm, GalU, CalS8 andUAXS were used for module 2 to produce UDP-Glc and UDP-Api. Formodule 3, GuApiGT and the previously reported GuGT14 were used asglycosyltransferases52. However, 7a was generated as a major bypro-duct when GuGT14 was used. It was due to the poor regio-selectivity ofGuGT14 and endogenous glycosyltransferases from tobacco (Fig. 8cand Supplementary Fig. 145). Then we discovered GuGT53 from G.uralensis, which showed a similar expression pattern as GuCHS,GuCHR, and GuApiGT (Fig. 1d, e). GuGT53 (UGT88E28, GenBankaccession number OQ266890) could regio-selectively and efficientlycatalyze 4′/4-O-glycosylation of liquiritigenin (1′) and ${ \pmb 2 ^ { \prime } }$ into liquiritin

(1) and isoliquiritin (2), respectively (Supplementary Fig. 146). Theyield of isoliquiritin apioside was improved when GuGT14 was replacedby GuGT53. When module 1 or 2 was absent, no 2a could be generated.It was generated after UDP-GlcA or 2′ was injected into the tobaccoleaves (Fig. 8c). Moreover, we cloned GuCHI from G. uralensis toreplace AtCHI, as 1a could not be detected when AtCHI was used inmodule 1 (Supplementary Fig. 147). The $\mathrm { O D } _ { 6 0 0 }$ of Agrobacterium wasalso optimized, and $\mathrm { O D } _ { 6 0 0 } 0 . 2$ for each gene was found to be the mostefficient concentration for 1a (Fig. 8d).

Finally, the contents of 1a and 2a in tobacco leaves were 5.46 and$4 . 7 3 \mathrm { m g / g }$ (dry weight, DW), respectively, with the above optimized

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/cb63df4de9606f4850cc4afe8ec0f86c80764b88335467352cc9cce4abb68561.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/415efa8b6f5dfa7e7c30305a5a4d9c49e26c03696ca66759d66f9dde6b29a564.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e0e5530453df01e238ac83e495041462764783718c038dfdc8c064d8f74d7705.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/e60b487880385422e104b5a2d4e5fb615d50fd1d98589f8a1de54a5ec1324379.jpg)



Fig. 6 | Apiosylation activity of Sb3GT1 mutants. a The crystal structure ofSb3GT1 (PDB ID: 8IOE) and the FFGDQ (372-376) motif. The image on the right is anenlargement of the dashed rectangle, where the red part represents CTD and thegrey part represents NTD. The amino acids in key motif of Sb3GT1 are highlightedusing sticks. b Functional characterization of Sb3GT1 and its mutants. Control 1, theacceptor was incubated with Sb3GT1 and an UDP-Api supply system (UDP-GlcA,



UAXS, NAD+ ). Control 2, the acceptor was incubated with Sb3GT1 and UDP-Xyl.Proposed structures for 66a, kaempferol 3-O-apioside; 66b, kaempferol 3-O-xylo-side. c The crystal structure of Sb3GT1 375S/Q377H mutant (PDB ID: 8IOD) andsuperimposition of its key motif to that in wild type. The amino acids in key motif of375S/Q377H mutant are depicted using lines.


conditions (Fig. 8e, f). By using different gene combinations formodule 1, we realized the de novo biosynthesis of eight more flavonoidapiosides. The basic skeleton could be flavanone, chalcone, or flavone,and the yields ranged from $0 . 1 9 { \cdot } 6 . 2 5 \mathrm { m g / g }$ (DW) (SupplementaryFigs. 148–155).

In conclusion, we identified the missing phenolic apiosyl-transferase GuApiGT from G. uralensis. GuApiGT could efficiently andregio-selectively catalyze ${ 2 ^ { \prime \prime } { \cdot } O }$ -apiosylation of flavonoid glycosides,and showed strict sugar donor selectivity towards UDP-Api. Thisselectivity was highly related with the unique 45-amino acid PSPG boxand the key RLGSDH sugar binding motif. Through theoretical calcu-lations and rational design, we altered the sugar donor selectivity ofGuApiGT and Sb3GT1. The 45-amino acid PSPG box and the RLGSDHmotif may be general for Leguminosae plants, and helped to discover 4other apiosyltransferases. We also achieved de novo biosynthesis of atleast 10 flavonoid apiosides in tobacco, and the yields could be up toaround $6 \mathrm { m g / g }$ . This work realized efficient biosynthesis of flavonoidapiosides, including the important bioactive natural product liquiritinapioside. It also highlights the sugar donor selectivity mechanisms ofGuApiGT, and sets a good example for functional evolution and pro-tein engineering of catalytic enzymes.

# Methods

# Plant materials

The fresh plant of Glycyrrhiza uralensis Fisch. (2-3 years old) was col-lected from Inner Mongolia Autonomous Region of China in August2019 for total RNA extraction and transcriptome sequencing. Theseeds of G. glabra and G. inflata were obtained from Gan-Su (China)and were sown in our laboratory under natural conditions. To extractRNA, 3-week-old seedlings were used. The fresh plant of Puerariathomsonii (1-2 years old) was collected from Anhui Province of China inJune 2022 for total RNA extraction.

# Total RNA isolation and transcriptome sequencing

The total RNA was extracted using the TranZolTM kit (Transgen Biotech,China) following the manufacturer’s instructions, and was used to

synthesize the first-stranded complementary DNA (cDNA) usingTransScript one-step genomic DNA (gDNA) removal and cDNA synth-esis SuperMix (Transgen Biotech, China). The transcriptome data ofdifferent parts of G. uralensis were acquired using Illumina sequencingplatform by Majorbio Bioinformatics Technology Co., Ltd (Shang-hai, China).

# Bioinformatics

Co-expression analysis was conducted using R studio. Genes highlyexpressed in the roots (fragments per kilobase of transcript per millionmapped reads $( \mathsf { F P K M } ) \ge 2 0$ in two biological replicates) were selectedfor co-expression analysis. GuCHS and GuCHR were used as ‘bait’. Theco-expressed genes were further filtered by Pfam (https://www.ebi.ac.uk/interpro), NR (non-redundant protein sequences, https://www.ncbi.nlm.nih.gov/), and UniProtKB/Swiss-Prot databases (https://www.uniprot.org/) annotation and Spearman’s correlation coefficient$( \boldsymbol { \mathsf { r } } \geq \mathbf { 0 . 8 } )$ . The analysis was performed using G. uralensis RNA-seq tran-scriptome data from different tissues. The co-expression network wasvisualized by Cytoscape.

Homologous plant ApiGT genes were searched using onlinetranscriptome data via China National GeneBank (https://db.cngb.org/blast/) which contains 1,000 plants project, transcriptome shotgunassembly proteins, non-redundant protein sequences, and UniProtKB/Swiss-Prot databases. GuApiGT was used as the query sequence.BLASTP was used for BLAST search with default parameters. Molecularphylogenetic analysis was conducted using MEGA6 software with themaximum likelihood method. The bootstrap consensus tree inferredfrom 1,000 replicates was taken to represent the evolutionary historyof the taxa analyzed.

# Molecular cloning, site-directed mutagenesis, and expressionof GTs

The full-length GT genes were amplified from cDNA using TransStart®FastPfu DNA Polymerase (Transgen, China) and were cloned into pET-$2 8 \mathsf { a } ( + )$ vector (Invitrogen, USA) by the Quick-change method. Mutantswere constructed using a Fast Mutagenesis System kit (Transgen

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/c628c8f1ab1e3705d933adea959761e6b4dc3d907da5c2c819c5a0a162e5bb38.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/0376ffe842af5e2cb1a9c483f755688fc8b0709842a6c0195f6cfc8fc20ac5d3.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/c01fc73a0623763c79067c7d81ea21cd57550428ef7ded2a13f420ecd7f67b9f.jpg)



Fig. 7 | Discovery of apiosyltransferases from Leguminosae plants.



a Phylogenetic analysis of 121 potential apiosyltransferase genes discovered from39 plants and 18 reported flavonoid UGTs. b Sequence alignment of PSPG box ofthe 121 apiosyltransferases. The red dashed box shows the unique RLGSDH motif.



The image was created using WebLogo (https://weblogo.berkeley.edu). The tablelisted conserved amino acids of 9 UGTs, including the 5 characterized ApiGTs. c Thefunctions of PtApiGT (Pueraria thomsonii), SsApiGT (Spatholobus suberectus),GgApiGT (Glycyrrhiza glabra), and GiApiGT (Glycyrrhiza inflata).


Biotech, China) according to the manufacturer’s instructions. Theprimers are given in Supplementary Data 1. The full length of SsApiGTwas synthesized by Tsingke Biological Technology Incorporation(Beijing, China). The recombinant plasmid pET- $2 8 \mathsf { a } ( + )$ -GTs wereintroduced into E. coli BL21(DE3) (Transgen Biotech, China) for het-erologous expression. Single colonies were incubated in LB media$( 5 0 \mu \mathrm { g } / \mathrm { m L }$ kan+ ) on a rotary shaker at $3 7 ^ { \circ } \mathrm { C } .$ When the $\mathrm { \Gamma _ { 0 D _ { 6 0 0 } } }$ value wasaround 0.6, protein expression was induced with $0 . 1 \mathsf { m M }$ IPTG for $2 0 \mathsf { h }$at $1 8 ^ { \circ } \mathrm { C }$ . The cell pellets were collected by centrifugation $( 6 4 0 8 \times g$ for10 min at $4 ^ { \circ } \mathrm { C } )$ . Then the cells were resuspended in $1 5 \mathrm { m l }$ of lysis buffer(10 mM imidazole, $2 0 \mathrm { m M }$ Tris, 200 mM NaCl, $2 \%$ glycerol (v/v), pH 7.4)and ruptured by sonication on ice for 15 min. The cell debris wasremoved by centrifugation at $1 4 { , } 4 2 0 \times g$ for $4 5 \mathrm { { m i n } }$ at $4 ^ { \circ } \mathrm { C } ,$ . Therecombinant proteins were purified using a nickel-affinity column. Theelution buffer included two types: one containing $3 0 \mathrm { m M }$ imidazole,

$2 0 \mathsf { m M }$ Tris, 200 mM NaCl and $2 \%$ glycerol $\left( \upsilon / v \right)$ to elute impurities,and the other containing $3 0 0 \mathrm { m M }$ imidazole, 20 mM Tris, $2 0 0 \mathrm { m M }$NaCl and $2 \%$ glycerol $\left( \upsilon / v \right)$ to elute the target protein. All the bufferswere adjusted to pH 7.4 by HCl. The impurities were eluted with $5 0 \mathrm { m l }$elution buffer containing $3 0 \mathrm { m M }$ imidazole. Then, GuApiGT recombi-nant protein was eluted by $2 0 \mathrm { m l }$ elution buffer containing $3 0 0 \mathrm { m M }$imidazole. The protein purity was analyzed by SDS-PAGE (Supple-mentary Fig. 2). The purified protein was concentrated and desalted bya $3 0 \mathbf { k D } \mathbf { a }$ ultrafiltration tube (Merck Millipore) with a storage buffer$2 0 \mathsf { m } \mathsf { M }$ Tris, 200 mM NaCl, $20 \%$ (v/v) glycerol, pH 7.4). The processesfor the other GTs were the same as that of GuApiGT.

# Enzyme activity assay

The reactions were carried out in $1 0 0 { \cdot } { \mu } 1$ systems containing $5 0 \mathsf { m M }$$\mathsf { N a H } _ { 2 } \mathsf { P O } _ { 4 } \mathsf { - N a } _ { 2 } \mathsf { H P O } _ { 4 }$ (pH 8.0), $0 . 1 \mathsf { m M }$ sugar acceptor, 6 mM NAD+ ,

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/54bea0437c45c24ddcdb8d531de5c4218d7dd615bce6ac286deb4963d4a58b47.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/198a8bff9022d311124e336c32c984c99e5958420d44cc9136fa4a17ac9fc94f.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/0a60c47260ffc36de1a70b4f70e04abff88ed6d4b30033c8e7aed1518631309b.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/78bd77659c5dc4d8218693ba2e50f54acc555a941d51aa9170ef262cba21ac44.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/8632e6cf99ece7c422068f267d4e727f5bcbe20620e3f90d8e07ddccb1253d8e.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/1b0ee045220d83db02d6c5ed1807b49c622ff377b490e19b9767b085aa27a672.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/67f22e9c1bfa0a3c526d720bebf88c62febef312e1cd9092b14449622a9c7096.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/54e0687d5ba5a871d98dc6e2503077f3ef38c1847f83bc59f5d226e778a3f86a.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/71f38541157fcb38b753c01ebf76bc46b2e4f1ab7731094fdac3029b751877b3.jpg)


![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/10e0d981cbb16cea8ab7523fa9104db01600c2e2a944440bb60e07573df257ef.jpg)


$1 . 5 \mathsf { m M }$ UDP-GlcA, $5 0 \mu \ g$ of UAXS, and $5 \mu \ g$ of purified GuApiGT ormutants at $3 7 ^ { \circ } \mathrm { C }$ for $^ { 3 \mathfrak { h } }$ . For other sugar donors, the reactions werecarried out in $1 0 0 { \cdot } { \mu } { \updownarrow }$ systems containing $5 0 \mathrm { \ m M \ N a H _ { 2 } P O _ { 4 } { \cdot } N a _ { 2 } H P O _ { 4 } }$(pH 8.0), 0.1 mM sugar acceptor, $0 . 5 \mathsf { m M }$ UDP-Xyl or $0 . 5 \mathsf { m M }$ UDP-Glc,and $4 0 \mu \mathbf { g }$ of purified mutants at $3 7 ^ { \circ } \mathrm { C }$ for $^ { 3 \mathfrak { h } }$ . For Sb3GT1 and itsmutants, the reactions were carried out in $1 0 0 { \cdot } { \mu } 1$ systems containing50 mM Tris-HCl (pH 9.0), 0.05 mM sugar acceptor, 6 mM NAD+ , 1.5 mM

![image](https://cdn-mineru.openxlab.org.cn/result/2026-03-18/0a767079-515b-4175-9a5f-283cba5cb881/b4c1bc58aeac73c3a26bee951daf9e021c9a80db45e69538c88cd0ae5767fe17.jpg)


UDP-GlcA, $5 0 \mu \ g$ of UAXS, and $1 0 0 \mu \ g$ of purified Sb3GT1 or mutants at$4 5 \mathrm { ^ \circ C }$ for 3 h. The reactions were terminated by adding $2 0 0 \mu \mathrm { L }$ pre-cooled methanol and then centrifuged at $2 1 , 1 3 0 \times g$ for 20 min. Thesupernatants were filtered through a $0 . 2 2 \cdot \mu \mathrm { m }$ membrane and thenanalyzed by LC/MS. The samples were separated on an Agilent ZorbaxSB-C18 column $( 4 . 6 \times 2 5 0 \mathrm { m m } ,$ $5 \mu \mathrm { m } )$ ) at a flow rate of 1 mL/min at roomtemperature. The mobile phase was a gradient elution of solvents A

Fig. 8 | De novo biosynthesis of (iso)liquiritin apioside and analogues intobacco. a The engineered biosynthetic pathway of 1a and 2a in Nicotiana ben-thamiana. b–d Optimization of Agrobacterium strains, bioparts, and optical densityof bacterial cultures for the biosynthesis of 1a and 2a, respectively. Three days afterinfiltration, isoliquiritin and UDP-GlcA were supplemented for lines 1-3; UDP-GlcAand isoliquiritigenin were supplemented for lines 4 and 5, respectively. e HPLCchromatograms of engineered tobacco extracts. Extract 1 and Extract 2 representsamples to produce 1a and 2a, respectively. Standard 1 and Standard 2 were

reference standards of liquiritin apioside and isoliquiritin apioside, respectively.f, g De novo biosynthesis of 1a, 2a, and 8 other flavonoid apiosides. The structuresof 1a, 2a, 12a and 15a were identified by comparing with reference standards; 3a,4a, 7a and 9a were identified by comparing with catalytic products of GuApiGT;and 68a and 69a were characterized by analyzing mass spectral data. Data arepresented as mean values $\pm \mathsf { S D }$ $( n = 3$ biologically independent samples) (8b, c, d, f).The source data underlying Fig. (8b, c, d and f) are provided in a Source Data file.

(water containing $0 . 1 \%$ formic acid) and B (acetonitrile, ACN), and thegradient programs were listed in Supplementary Table 3. The con-version rates in percentage were calculated from peak areas of gly-cosylated products and sugar acceptors in HPLC/UV chromatograms(Agilent 1260, USA). MS analysis was performed on a Q-Exactive hybridquadrupole-Orbitrap mass spectrometer equipped with a heated ESIsource (Thermo Fisher Scientific, USA). The MS parameters were asfollows: sheath gas pressure 45 arb, aux gas pressure 10 arb, dischargevoltage $4 . 5 \mathsf { k V }$ , capillary temperature $3 5 0 ^ { \circ } \mathrm { C }$ . MS1 resolution was set as70,000 FWHM, AGC target $\mathtt { 1 ^ { * } E 6 }$ , maximum injection time 50 ms, andscan range $m / z$ 100-1000. MS2 resolution was set as 17,500 FWHM,AGC target 1*E5, maximum injection time 100 ms, NCE 35. The massspectra were recorded in the negative ion mode for all the substratesexcept for 19 and 29.

# Biochemical properties of GuApiGT

To determine the optimal reaction time, 9 time points between 5 and600 min were tested. To optimize the pH value, different reactionbuffers with pH from 3.0-6.0 (citric acid-sodium citrate buffer), 6.0-8.0$\left( \mathsf { N a } _ { 2 } \mathsf { H P O } _ { 4 } . \mathsf { N a H } _ { 2 } \mathsf { P O } _ { 4 } \right.$ buffer), 7.0-8.5 (Tris-HCl buffer), and 9.0-10.8$( \mathsf { N a } _ { 2 } \mathsf { C O } _ { 3 }  – \mathsf { N a H C O } _ { 3 }$ buffer) were tested. To optimize the reaction tem-perature, the reactions were incubated at different temperatures (4,18, 25, 30, 37, 45, $6 0 ^ { \circ } \mathrm { C } )$ . To determine the effects of divalent metalions on enzyme activities, EDTA, BaCl2, CaCl2, $\mathsf { F e C l } _ { 2 }$ , $\mathbf { M g C l } _ { 2 }$ , $\mathbf { Z } \mathsf { n C l } _ { 2 }$ and$\mathrm { C u C l } _ { 2 }$ were added individually at a final concentration of 5 mM (Sup-plementary Fig. 4). All enzymatic reactions $( 1 0 0 \mu \mathrm { L }$ reaction mixturesincluding $\mathbf { 0 . 1 m M }$ isoliquiritin, $6 \mathsf { m M N A D } ^ { + }$ , 1.5 mM UDP-GlcA, $5 0 \mu \ g$ ofUAXS, and 2 μg of purified GuApiGT) were conducted in three parallelexperiments $\left( n = 3 \right)$ . The reactions were terminated with pre-cooledmethanol and centrifuged at $2 1 , 1 3 0 \times g$ for 20 min for HPLC analysis asdescribed above.

# Preparation of UDP-apiose

The reaction mixtures contained $1 0 0 \mu \mathrm { L }$ buffer $( 1 0 0 \mathsf { m } \mathsf { M }$ triethylaminephosphate, pH 8.0), 0.1 mM NAD+ , 10 mM UDP-GlcA, and $0 . 4 8 \mathrm { m g }$ ofUAXS. A total of 30 parallel tubes were used. The reactions were per-formed at $2 5 ^ { \circ } \mathrm { C }$ for 4 h and then centrifuged at $2 1 , 1 3 0 \times g$ for 30 min.The products were subsequently purified by reversed-phase HPLC.HPLC was performed on an Inertsustain AQ-C18 column $( 5 \mu \mathrm { m }$ ,$4 . 6 \times 2 5 0 \mathrm { m m }$ ; GL Sciences, Tokyo, Japan) at a flow rate of $1 . 0 \mathrm { m L / m i n }$ .The mobile phase was a gradient elution of solvents A $( 1 0 0 \mathrm { m M } N , N \cdot$dimethylcyclohexylamine phosphate buffer, pH 6.5) and B $( 3 0 \% \ ( v / v )$ACN). A gradient elution program was used: 0 min, $100 \%$ A; 13 min,$100 \%$ A; 35 min, $3 3 \%$ A; 39 min, $3 3 \%$ A; 40 min, $100 \%$ A. The elutedfractions were monitored by measuring the UV absorbance at $2 6 2 \mathsf { n m }$(Supplementary Fig. 156). After freeze-drying, UDP-apiose was dis-solved with triethylamine phosphate for use.

# Determination of GuApiGT kinetic parameters

In a final volume of $2 5 \mu \mathrm { L }$ with 50 mM $\mathsf { N a } _ { 2 } \mathsf { H P O } _ { 4 } \mathsf { \cdot N a H } _ { 2 } \mathsf { P O } _ { 4 }$ buffer (pH8.0), $2 \mu \mathrm { g } / \mathrm { m L }$ protein, $4 8 0 \mu \mathrm { m o l / L }$ of saturated UDP-apiose, and dif-ferent concentrations of compound 2 (1, 2.5, 5, 10, 30, 40, 60, 80, 150$\mu \mathrm { m o l } / \mathrm { L } )$ were added. The reactions were quenched with pre-cooledmethanol after incubating at $3 7 ^ { \circ } \mathrm { C }$ for 15 min, and then centrifuged at$2 1 , 1 3 0 \times g$ for 15 min. The supernatants were used for HPLC analysis. All

experiments were performed in triplicate. The conversion rates inpercentage were calculated from HPLC peak areas of glycosylatedproducts and substrates. Michaelis-Menten plot was fitted.

# Scaled-up reactions

To prepare the glycosylated products, the reaction mixtures contained$6 5 0 \mu \mathrm { L }$ buffer (50 mM $\mathsf { N a H } _ { 2 } \mathsf { P O } _ { 4 } { \cdot } \mathsf { N a } _ { 2 } \mathsf { H P O } _ { 4 }$ , pH 8.0), $1 5 \mu \mathrm { L }$ sugar accep-tor $( 5 0 \mathsf { m } \mathsf { M }$ dissolved in dimethyl sulfoxide), $1 0 0 \mu \mathrm { L }$ NAD+ (50 mM),$2 0 \mu \mathrm { L }$ UDP-GlcA $( 5 0 \mathsf { m M } )$ , 1.5 mg of UAXS, and 1.0 mg of GuApiGT. Atotal of 60 parallel tubes were used. The reactions were performed at$3 7 ^ { \circ } \mathrm { C }$ overnight and terminated by adding two-fold volume ofmethanol. The mixtures were then centrifuged at 21, $1 3 0 \times g$ for 30 min.The organic solvent was removed under reduced pressure. The residuewas dissolved in 1.0-1.5 mL of methanol. The products were then pur-ified by reversed-phase semi-preparative HPLC. The structures werecharacterized by HRMS and extensive 1D and 2D NMR analyses. Theprocesses for L369/H373Q and I136T/L369/H373Q mutants weresimilar to that of GuApiGT.

# Crystallization

The full-length cDNA of GuApiGT was cloned into pET- $\cdot 2 8 \mathbf { a } ( + )$ vector.The S-tag of pET28a was removed. A TrxA-tag and $_ { 6 \times }$ His-tag followedby thrombin site were added before the N-terminus of the targetprotein to facilitate purification. The TrxA-His-thrombin-GuApiGTprotein was expressed in E. coli (DE3) strain and purified by Ni affi-nity chromatography (GE Healthcare). After purification, the recom-binant protein was digested by thrombin to remove tag. The samplewas mixed with Ni-NTA affinity beads for the second time to purify theprotein. The flow-through was concentrated and then applied to size-exclusion chromatography on a SuperdexTM 200 increase 10/300 GLprepacked column (GE Healthcare) for further purification. The elutionbuffer was $2 0 \mathrm { m M }$ Tris-HCl (pH 7.5) and 50 mM NaCl. Fractions con-taining GuApiGT were collected and concentrated to $2 0 \mathrm { m g / m L }$ , flash-frozen on liquid nitrogen, and then stored in a ${ \bf - 8 0 ^ { \circ } C }$ freezer. Thepurified protein was incubated with 5 mM UDP or UDP-Glc for 1 h. Thecrystals of GuApiGT were obtained after 14 days at $1 6 ^ { \circ } \mathrm { C }$ in hangingdrops containing $1 \mu \mathrm { L }$ of protein solution and $1 \mu \mathrm { L }$ of reservoir solution(0.2 M lithium sulfate monohydrate, 0.1 M Bis-Tris pH 5.25, $28 \%$ w/vpolyethylene glycol 3,350) (Supplementary Fig. 157). The crystals wereflash-frozen in the reservoir solution supplemented with $2 5 \%$ (v/v)glycerol. The crystals of Sb3GT1 were obtained after 14 days at $1 6 ^ { \circ } \mathrm { C }$ inhanging drops containing $1 \mu \mathrm { L }$ of protein solution and $1 \mu \mathrm { L }$ of reservoirsolution (0.2 M sodium malonate pH 4.0, 20% w/v polyethylene glycol3,350). The crystals of Sb3GT1-375S/Q377H were obtained after 14 daysat $1 6 ^ { \circ } \mathrm { C }$ in hanging drops containing 1 μL of protein solution and 1 μL ofreservoir solution (0.05 M citric acid, 0.05 M Bis-Tris propane pH 5.0,$1 6 \%$ w/v polyethylene glycol 3,350).

# Crystal structure determination

The diffraction data of GuApiGT and Sb3GT1 crystals were collected atbeamlines BL19U1 and BL02U1 Shanghai Synchrotron Radiation Facil-ity (SSRF). The data were processed with XDS. The structures weresolved by molecular replacement with Phaser. Crystallographicrefinement was performed repeatedly using Phenix and COOT. Therefined structures were validated by Phenix and the PDB validation

server (https://validate-rcsb-1.wwpdb.org/). The final refined struc-tures were deposited in the Protein Data Bank. The diffraction data andstructure refinement statistics are given in Supplementary Tables 4and 7.

# Molecular docking

Since all the reported UGT structures are highly conserved for theUDP-sugar binding domain, we simulated the initial GuApiGT/UDP-sugar complex structures by superimposing the UDP parts of UDP-Api,UDP-Glc, and UDP-Xyl to reported structures. The binding modes ofsugar acceptors to the UDP-sugar-bound GuApiGT and its mutantswere derived using the Glide module53,54 of the Schrödinger Suite(version 2021-4). The grid center for the docking of UDP-sugar wasadopted to the geometrical center of His18, Asp372, and Phe195 withthe grid box dimension of $2 5 \mathring \mathbf { A } .$ . The ligands were manually prepared inMaestro interface with the atom types and bond orders correctlyassigned by Ligprep module55. A total of 30 docking poses were gen-erated for each system.

# Molecular dynamics (MD)

The Desmond module56 of Schrödinger Suite (version 2021-4) was usedfor MD simulations of the docked complexes. The OPLS4 force fieldwas selected for both protein and ligand atoms57. An orthorhombicbox was added with a $1 0 . 0 \mathring \mathbf { A }$ buffering area to the protein-ligandcomplex and filled with ~13800 TIP3P-type58 water molecules. Thecounter ions of Na+ and/or Cl− were also added to neutralize the systemand to mimic the physical salt concentration of 0.15 M. The simulatedtemperature and pressure were maintained at 300.0 K and 1.0 atm bythe Nose-Hoover chain thermostat59 and Martyna-Bobias-Kleinbarostat60, respectively. The default minimization and equilibrationprocedures were used before the 100-ns production simulation foreach protein-ligand system. The simulation interaction analysis mod-ule was used to derive statistic data of the ligand-protein interactionsduring the MD simulations.

# Binding free energy calculations

We used the Prime module of Schrödinger Suite (version 2021-4) tocalculate the MM/GBSA32,61 binding free energy with the continuumsolvation model VSGB (variable dielectric surface generalized Born)62.The binding free energy of each system was averaged from 400 snap-shots evenly extracted from the 100-ns trajectory.

# Well-tempered metadynamic simulations

The well-tempered metadynamic simulations63,64 with OPLS4 force fieldwere performed using the desmond module for representative snap-shots from conventional MD (cMD) simulations, which kept the waterbox and counter ions. For the collective valuables, we applied the dis-tance between the $\mathbf { C 1 } ^ { \prime \prime \prime }$ atom of sugar donor and the glycol-site of sugaracceptor $( 0 2 ^ { \prime \prime } )$ and the angle of phosphate oxygen (O3), $\mathbf { C 1 } ^ { \prime \prime \prime }$ , and $0 2 ^ { \prime \prime }$atoms, with the width of $0 . 1 \mathring \mathrm { A }$ and wall of 2.5 to $6 . 5 \mathring \mathrm { A }$ and width of $1 ^ { \circ }$ andwall to $1 8 0 ^ { \circ }$ , respectively. The height of external Gaussian potential,updating interval, and the bias KTemp were assigned to $0 . 2 \mathrm { k c a l / m o l }$ ,1.0 ps, and 3.4 kcal/mol, respectively. With these settings, a 500-ns well-tempered metadynamic simulation was performed for each system.

# QM/MM calculations

We selected a representative snapshot from the MD simulations of WTenzyme with UDP-Api for QM/MM calculations using the ONIOMapproach65 in Gaussian 16 (rev. C.01). The snapshot extracted from MDtrajectories was preprocessed using the tleap program of AMBERpackage (version 18.0) to generate the forcefield topology files(.prmtop)66. The restraint electrostatic potential (RESP) charges wereapplied for the ligands67, 1 and 1a, which were derived from fitting theGaussian calculated electrostatic charge (HF/6-31G*) using the Ante-chamber module of AmberTools18. The MD snapshot was energy

minimized using the sander program with the Amber99SB(protein)/GAFF(ligand) forcefield68,69, followed by exporting to the VMD MolUPplugin (version 1.7.0) for the setup of ONIOM partitions70,71. Watermolecules beyond 4 Å of protein and ions $\left( \mathbf { N _ { A } } ^ { + } \right.$ and Cl− ) were removed.For the QM regions, UDP-Api was truncated at the carbon atom next tothe first phosphorus atom (PDB name: PA), while the sugar acceptorwas truncated to the glycosidic bond. The side-chain atoms of D115,H18, H373, I136, D372 were also selected as QM regions. Linkinghydrogen atoms were automatically added into the boundary betweenQM and MM regions where there is a breaking covalent bond. Thedefault scaling factors for the linked bonds in Gaussian 16 were usedfor the MM energy calculations. All residues and water moleculeswithin $4 \mathring { \mathsf { A } }$ of sugar acceptor/UDP-Api or within 6 Å of the QM regionatoms were unfrozen to move during the optimization. B3LYP/6-31G(d):AMBER and (B3LYP/6-311++G(2d,2p):AMBER)=embedchargewere used for geometry optimizations and final energy calculations,respectively. The transition state geometries were initially located byflexible reactant coordinates scan and fully optimized, which were alsoconfirmed by the unique imaginary vibrational mode connecting thebonding and de-bonding atoms.

# Hydrogen-Deuterium Exchange Mass Spectrometry (HDX-MS)

Deuterium labeling was initiated with a 20-fold dilution in ${ \bf D } _ { 2 } { \bf O }$ buffer$( 1 0 0 \mathsf { m } \mathsf { M }$ phosphate, pD 7.0) of WT, L369/H373Q mutant, or I136T/L369/H373Q mutant (each $\mathrm { 1 m g / m L } )$ ). After 0.083, 0.25, 1, 10, 30, 60and 240 min of labeling, the reaction was quenched with the additionof quenching buffer $( 1 0 0 \mathsf { m } \mathsf { M }$ phosphate, 4 M GdHCl, 0.5 M TCEP, pH2.0). Samples were then injected and online digested using a WatersENZYMATE BEH pepsin column $( 2 . 1 \times 3 0 \mathrm { m m }$ , $5 \mu \mathrm { m } \mathrm { \AA }$ ). The peptideswere trapped and desalted on a VanGuard Pre-Column trap (ACQUITYUPLC BEH C18, $1 . 7 \mu \mathrm { m } $ ), eluted with $1 5 \%$ aqueous acetonitrile at $1 0 0 \mu \mathrm { L } /$min, and then separated on an ACQUITY UPLC BEH C18 column$( 1 . 7 \mu \mathsf { m }$ , $1 . 0 \times 1 0 0 \mathrm { m m } )$ ). All mass spectra were acquired on a WatersXevo G2 mass spectrometer, and processed using DynamX 3.0 soft-ware. Peptides from an unlabeled protein were identified using Pro-teinLynx Global Server (PLGS) searches of a protein database includingWT, L369/H373Q mutant, and I136T/L369/H373Q sequences. Relativedeuterium levels for each peptide were calculated by subtracting themass of the undeuterated control sample from that of the deuterium-labeled sample. Deuterium levels were not corrected for backexchange and were thus reported as relative35.

# De novo biosynthesis of flavonoid apiosides in tabacco

The full-length DNA regions of AtPAL, AtC4H, At4CL, AtCHS, GuCHR,GuCHI, AtCHI, PcFNSI, pgm, GalU, CalS8, UAXS, GuGT14, GuGT53, andGuApiGT were amplified using primers given in Supplementary Data 1.The PCR products were subcloned into pDonr207 vectors using theGateway BP Clonase II Enzyme Mix and then cloned into pEAQ-HT-DEST1 vector using the Gateway LR Clonase II Enzyme Mix accordingto the manufacturer’s instructions. The recombinant pEAQ-HT-DEST1-GuApiGT vector was transformed into Agrobacterium tumefaciensstrain GV2260 by chemical conversion method.

Single colonies were inoculated at ${ 2 8 ^ { \circ } \mathrm { C } }$ with shaking in LB culturemedium $( 5 0 \mu \mathrm { g } / \mathrm { m L }$ kanamycin and $5 0 \mu \mathrm { g } / \mathrm { m L }$ rifampicin) until$\mathrm { O D } _ { 6 0 0 } = 0 . 6$ . After centrifugation, bacteria were re-suspended in MMAbuffer to $\mathrm { O D } _ { 6 0 0 } { = } 0 . 2$ for each strain. Different strains were mixed fortransformation. The infection solution was infiltrated into leaves of 5-6week-old tobacco. After 7 days, the samples were harvested and freeze-dried. The secondary metabolites were extracted by $50 \%$ (v/v)methanol and analyzed by LC/MS.

The contents of 1a and 2a were quantified by regression equa-tions, which were also used for semi-quantification of the other 8 fla-vonoid apiosides. Reference standards 1a and 2a were respectivelydissolved in DMSO to make solutions of $2 \mathrm { m g / m L }$ and $\mathrm { 1 m g / m L }$ , whichwere 1:1 mixed to obtain the mixed stock solution. The stock solution

was serially diluted using $50 \%$ methanol to obtain calibration standardsolutions (diluted by 2, 4, 8, 16, 32, 64, 128 and 256 folds, respectively).The regression equations of 1a and 2a were $y = 1 . 2 1 0 5 \mathrm { e } ^ { 5 } x + 7 . 1 4 1 3 \mathrm { e } ^ { 6 } ( r ^ { 2 } =$ $r ^ { 2 } =$0.999), and $y = 7 . 7 1 3 \mathrm { e } ^ { 4 } x + 3 . 3 8 8 \mathrm { e } ^ { 6 }$ $( r ^ { 2 } = 0 . 9 9 8 )$ , respectively, where $x$represents the concentration $\mathrm { ( n g / m l ) }$ ), $y$ the peak area, and $r$ the cor-relation coefficient.

# Reporting summary

Further information on research design is available in the NaturePortfolio Reporting Summary linked to this article.

# Data availability

Data supporting the findings of this study are available in the article,supplementary materials, or public database. The gene sequence datagenerated in this study have been deposited in the NCBI databaseunder the following accession numbers: GuApiGT (OQ201607), SsA-piGT/PtApiGT/GiApiGT/GgApiGT (OQ230794-OQ230797), GuGT53(OQ266890), and other apiosyltransferase candidate genes fromLeguminosae plants (OR372660-OR372775). The raw reads from theRNA-sequencing profiling analysis of Glycyrrhiza uralensis have beendeposited in the NCBI Sequence Read Archive (SRA) database underthe BioProject accessions PRJNA945816. The crystal structures in thisstudy have been deposited in the RCSB PDB database under the fol-lowing accession numbers: GuApiGT (8HZZ), Sb3GT1 in complex withUDP (8IOE), and Sb3GT1-375S/Q377H in complex with UDP-Glc (8IOD).The primers and Gaussian optimized geometries (RC, TS, and PC) aregiven in Supplementary Data 1–4. Source data are provided withthis paper.

# References



1. Pičmanová, M. & Moller, B. L. Apiose: one of nature’s witty games.Glycobiology 26, 430–442 (2016).





2. Braconnot, H. Sur une nouvelle substance végétale (l’ Apiine). Ann.Chim. Phys. 9, 250–252 (1843).





3. Savino, S. et al. Deciphering the enzymatic mechanism of sugar ringcontraction in UDP-apiose biosynthesis. Nat. Catal. 2,1115–1123 (2019).





4. Choi, S., Mansoorabadi, S. O., Liu, Y. N., Chien, T. C. & Liu, H. W.Analysis of UDP-D-apiose/UDP-D-xylose synthase-catalyzed con-version of UDP-D-apiose phosphonate to UDP-D-xylose phospho-nate: implications for a retroaldol-aldol mechanism. J. Am. Chem.Soc. 134, 13946–13949 (2012).





5. Mohnen, D. Pectin structure and biosynthesis. Curr. Opin. Plant Biol.11, 266–277 (2008).





6. Ndeh, D. et al. Complex pectin metabolism by gut bacteria revealsnovel catalytic functions. Nature 544, 65–70 (2017).





7. Watson, R. R. & Orenstein, N. S. Chemistry and biochemistry ofapiose. Carbohydr. Chem. Biochem. 31, 135–184 (1975).





8. Veitch, N. C. Isoflavonoids of the leguminosae. Nat. Prod. Rep. 24,417–464 (2007).





9. Wang, L. Q., Yang, R., Yuan, B. C., Liu, Y. & Liu, C. S. The antiviral andantimicrobial activities of licorice, a widely-used Chinese herb. ActaPharm. Sin. B 5, 310–315 (2015).





10. Song, W. et al. Biosynthesis-based quantitative analysis of 151 sec-ondary metabolites of licorice to differentiate medicinal Glycyrrhizaspecies and their hybrids. Anal. Chem. 89, 3146–3153 (2017).





11. Kuang, Y., Li, B., Fan, J. R., Qiao, X. & Ye, M. Antitussive andexpectorant activities of licorice and its major compounds. Bioorg.Med. Chem. 26, 278–284 (2018).





12. Kim, M., Kang, S. & Rhee, Y. H. De novo synthesis of furanose sugars:catalytic asymmetric synthesis of apiose and apiose-containingoligosaccharides. Angew. Chem. Int. Ed. 55, 9733–9737 (2016).





13. Liang, D. M. et al. Glycosyltransferases: mechanisms and applica-tions in natural product development. Chem. Soc. Rev. 44,8350 (2015).





14. Kurze, E. et al. Structure-function relationship of terpenoid glyco-syltransferases from plants. Nat. Prod. Rep. 39, 389–409 (2022).





15. Liu, Y. Q. et al. pUGTdb: A comprehensive database of plant UDP-dependent glycosyltransferases. Mol. Plant https://doi.org/10.1016/j.molp.2023.01.003 (2023).





16. Reed, J. et al. Elucidation of the pathway for biosynthesis of saponinadjuvants from the soapbark tree. Science 379, 1252–1264 (2023).





17. Hong, B. K. et al. Biosynthesis of strychnine. Nature 607,617–622 (2022).





18. Nett, R. S., Lau, W. & Sattely, E. S. Discovery and engineering ofcolchicine alkaloid biosynthesis. Nature 584, 148–153 (2020).





19. Wang, Z. L. et al. GuRhaGT, a highly specific saponin $2 "$ -O-rham-nosyltransferase from Glycyrrhiza uralensis. Chem. Commun. 58,5277–5280 (2022).





20. Nomura, Y. et al. Functional specialization of UDP-glycosyltransferase 73P12 in licorice to produce a sweet triterpe-noid saponin, glycyrrhizin. Plant J. 99, 1127–1143 (2019).





21. Zhang, Y. Q. et al. A highly selective $2 "$ -O-glycosyltransferase fromZiziphus jujuba and de novo biosynthesis of isovitexin $2 "$ -O-gluco-side. Chem. Commun. 58, 2472–247 (2022).





22. Liu, S. et al. Characterization of a highly selective 2″-O-galactosyl-transferase from Trollius chinensis and structure-guided engineer-ing for improving UDP-glucose selectivity. Org. Lett. 23,9020–9024 (2021).





23. Zhang, C. et al. Extraction optimization, structural characterizationand potential alleviation of hyperuricemia by flavone glycosidesfrom celery seeds. Food Funct. 13, 9832 (2022).





24. Jumper, J. et al. Highly accurate protein structure prediction withAlphaFold. Nature 596, 583–589 (2021).





25. Zhang, Y. Q., Zhang, M., Wang, Z. L., Qiao, X. & Ye, M. Advances inplant-derived C-glycosides: phytochemistry, bioactivities, and bio-technological production. Biotechnol. Adv. 60, 108030 (2022).





26. Zhang, M. et al. Functional characterization and structural basis ofan efficient di-C-glycosyltransferase from Glycyrrhiza glabra. J. Am.Chem. Soc. 142, 3506–3512 (2020).





27. Zong, G. et al. Crystal structures of rhamnosyltransferase UGT89C1from Arabidopsis thaliana reveal the molecular basis of sugar donorspecificity for UDP-β-L-rhamnose and rhamnosylation mechanism.Plant J. 99, 257–269 (2019).





28. Wang, Z. L. et al. Dissection of the general two-step di-C-glycosy-lation pathway for the biosynthesis of (iso)schaftosides in higherplants. Proc. Natl. Acad. Sci. USA. 117, 30816–30823 (2020).





29. Zhang, J. et al. Catalytic flexibility of rice glycosyltransferaseOsUGT91C1 for the production of palatable steviol glycosides. Nat.Commun. 12, 7030 (2021).





30. Hsu, T. et al. Employing a biochemical protecting group for a sus-tainable indigo dyeing strategy. Nat. Chem. Biol. 14, 256–261 (2018).





31. Klepeis, J. L., Lindorff-Larsen, K., Dror, R. O. & Shaw, D. E. Long-timescale molecular dynamics simulations of protein structure andfunction. Curr. Opin. Chem. Biol. 19, 120–127 (2009).





32. Kollman, P. A. et al. Calculating structures and free energies ofcomplex molecules: combining molecular mechanics and con-tinuum models. Acc. Chem. Res. 33, 889–897 (2000).





33. Bussi, G. & Laio, A. Using metadynamics to explore complex free-energy landscapes. Nat. Rev. Phys. 2, 200–212 (2020).





34. Naidoo, K. J., Bruce-Chwatt, T., Senapathi, T. & Hillebrand, M. Mul-tidimensional free energy and accelerated quantum library meth-ods provide a gateway to glycoenzyme conformational, electronic,and reaction mechanisms. Acc. Chem. Res. 54, 4120–4130 (2021).





35. Zhang, M. et al. Functional characterization and protein engineeringof a triterpene 3-/6-/2′-O-glycosyltransferase reveal a conservedresidue critical for the regiospecificity. Angew. Chem. Int. Ed. 61,e202113587 (2022).





36. Huang, L. W., So, P. K., Chen, Y. W., Leung, Y. C. & Yao, Z. P. Con-formational dynamics of the helix 10 region as an allosteric site in





class A $\beta$ -lactamase inhibitory binding. J. Am. Chem. Soc. 142,13756–13767 (2020).





37. Schober, M. et al. Chiral synthesis of LSD1 inhibitor GSK2879552enabled by directed evolution of an imine reductase. Nat. Catal. 2,909–915 (2019).





38. Wang, Z. L. et al. Highly promiscuous flavonoid 3-O-glycosyl-transferase from Scutellaria baicalensis. Org. Lett. 21,2241–2245 (2019).





39. One thousand plant transcriptomes initiative. One thousand planttranscriptomes and the phylogenomics of green plants. Nature574, 679–685 (2019).





40. Song, W., Li, Y. J., Qiao, X., Qian, Y. & Ye, M. Chemistry of theChinese herbal medicine Puerariae Radix (GeGen): a review. J. Chin.Pharm. Sci. 23, 347–360 (2014).





41. Zhang, S. W. & Xuan, L. J. New phenolic constituents from the stemsof Spatholobus suberectus. Helv. Chim. Acta 89, 1241–1245 (2006).





42. Yamashita, M. et al. The apiosyltransferase celery UGT94AX1 cata-lyzes the biosynthesis of the flavone glycoside apiin. Plant Physiol.https://doi.org/10.1093/plphys/kiad402 (2023).





43. Liu, X. N. et al. Engineering yeast for the production of breviscapineby genomic analysis and synthetic biology approaches. Nat. Com-mun. 9, 448 (2018).





44. Liu, Q. L. et al. De novo biosynthesis of bioactive isoflavonoids byengineered yeast cell factories. Nat. Commun. 12, 6085 (2021).





45. Romanowski, S. & Eustaquio, A. S. Synthetic biology for naturalproduct drug production and engineering. Curr. Opin. Chem. Biol.58, 137–145 (2022).





46. Sirirungruang, S., Markel, K. & Shih, P. M. Plant-based engineeringfor production of high valued natural products. Nat. Prod. Rep. 39,1492 (2022).





47. Nett, R. S. & Sattely, E. S. Total biosynthesis of the tubulin-bindingalkaloid colchicin. J. Am. Chem. Soc. 143, 19454–19465 (2021).





48. Reed, J. et al. A translational synthetic biology platform for rapidaccess to gram-scale quantities of novel drug-like molecules.Metab. Eng. 42, 185–193 (2017).





49. Schultz, B. J., Kim, S. Y., Lau, W. & Sattely, E. S. Total biosynthesis formilligram-scale production of etoposide intermediates in a plantchassis. J. Am. Chem. Soc. 141, 19231–19235 (2019).





50. Li, J. H. et al. Chloroplastic metabolic engineering coupled withisoprenoid pool enhancement for committed taxanes biosynthesisin Nicotiana benthamiana. Nat. Commun. 10, 4850 (2019).





51. Zhao, Q. et al. Two CYP82D enzymes function as flavone hydro-xylases in the biosynthesis of root-specific 4′-deoxyflavones inScutellaria baicalensis. Mol. Plant 11, 135–148 (2018).





52. Chen, K. et al. Diversity of O-glycosyltransferases contributes to thebiosynthesis of flavonoid and triterpenoid glycosides in Glycyrrhizauralensis. ACS Synth. Biol. 8, 1858–1866 (2019).





53. Friesner, R. A. et al. Glide: a new approach for rapid, accuratedocking and scoring. 1. method and assessment of docking accu-racy. J. Med. Chem. 47, 1739–1749 (2004).





54. Halgren, T. A. et al. Glide: a new approach for rapid, accuratedocking and scoring. 2. enrichment factors in database screening.J. Med. Chem. 47, 1750–1759 (2004).





55. LigPrep, Schrödinger, LLC, New York, NY, 2021.





56. Kevin, J. B. et al. Scalable algorithms for molecular dynamicssimulations on commodity clusters, Proceedings of the ACM/IEEEConference on Supercomputing (SC06) (2006).





57. Lu, C. et al. OPLS4: improving force field accuracy on challengingregimes of chemical space. J. Chem. Theory Comput. 17,4291–4300 (2021).





58. Jorgensen, W. L., Chadrasekhar, J., Madura, J. D., Impey, R. W. &Klein, M. L. Comparison of simple potential functions for simulatingliquid water. J. Chem. Phys. 79, 926 (1983).





59. Martyna, G. J., Klein, M. L. & Tuckerman, M. Nosé–Hoover chains:the canonical ensemble via continuous dynamics. J. Chem. Phys.97, 2635 (1992).





60. Martyna, G. J., Tobias, D. J. & Klein, M. L. Constant pressure mole-cular dynamics algorithms. J. Chem. Phys. 101, 4177 (1994).





61. Hou, T. J., Wang, J. M., Li, Y. Y. & Wang, W. Assessing the perfor-mance of the MM/PBSA and MM/GBSA Methods. 1. the accuracy ofbinding free energy calculations based on molecular dynamicssimulations. J. Chem. Inf. Model. 51, 69–82 (2011).





62. Li, J. N. et al. The VSGB 2.0 model: a next generation energy modelfor high resolution protein structure modeling. Proteins 79,2794–2812 (2011).





63. Barducci, A., Bussi, G. & Parrinello, M. Well-tempered metady-namics: a smoothly converging and tunable free-energy method.Phys. Rev. Lett. 100, 020603 (2008).





64. Laio, A. & Parrinello, M. Escaping free-energy minima. Proc. Natl.Acad. Sci. U.S.A. 99, 12562–12566 (2002).





65. Maseras, F. & Morokuma, K. IMOMM: a new integrated ab initio $^ +$molecular mechanics geometry optimization scheme of equili-brium structures and transition states. J. Comput. Chem. 16,1170–1179 (1995).





66. Case, D. A. et al. The amber biomolecular simulation programs. J.Comput. Chem. 26, 1668–1688 (2005).





67. Wang, J. M., Cieplak, P. & Kollman, P. A. How well does a restrainedelectrostatic potential (RESP) model perform in calculating con-formational energies of organic and biological molecules? J.Comput. Chem. 21, 1049–1074 (2000).





68. Cornell, W. D. et al. A second generation force field for the simu-lation of proteins, nucleic acids, and organic molecules. J. Am.Chem. Soc. 117, 5179–5197 (1995).





69. Wang, J. M., Wolf, R. M., Caldwell, J. W., Kollman, P. A. & Case, D. A.Development and testing of a general amber force field. J. Comput.Chem. 25, 1157–1174 (2004).





70. Humphrey, W., Dalke, A. & Schulten, K. VMD: visual moleculardynamics. J. Mol. Graph. Model. 14, 33–38 (1996).





71. Fernandes, H. S., Ramos, M. J. & Cerqueira, N. M. F. S. A. molUP: AVMD plugin to handle QM and ONIOM calculations using theGaussian software. J. Comput. Chem. 39, 1344–1353 (2018).



# Acknowledgements

This work was supported by National Natural Science Foundation ofChina (Grants No. 81891010/81891011, 82330122 and 81725023 to M.Y.;82122073 to X.Q.), China National Postdoctoral Program for InnovationTalents (Grant No. BX20220022 to Z.L.W.), and China Postdoctoral Sci-ence Foundation (Grant No. 2023M730131 to Z.L.W.). We thank Dr. Xiao-Meng Shi and Dr. Hong-Li Jia at State Key Laboratory of Natural andBiomimetic Drugs of Peking University for assistance in HDX-MS andX-ray diffraction experiments. We thank Professor Qing Jin at AnhuiAgricultural University for assistance in plant materials collection. Wethank Prof. George Lomonossoff at John Innes Centre for providing thepEAQ-HT vector. We thank the staff at BL19U1/BL02U1 beamlines at SSRFof the National Facility for Protein Science in Shanghai (NFPS), ShanghaiAdvanced Research Institute, Chinese Academy of Sciences, for pro-viding technical support in X-ray diffraction data collection and analysis.The computations were enabled by resources provided by the SwedishNational Infrastructure for Computing (SNIC) at the National Super-computer Center (Grant No. SNIC2022-3-34) at Linköping University(Sweden).

# Author contributions

M.Y., Z.L.W. and X.Q. designed research and acquired funding. F.D.L.supervised the crystallography experiments. J.H.L. and H.Å. contributedthe theoretical calculation. H.T.W. and Z.L.W. designed and performed

all experiments and analyzed the data. K.C., M.J.Y., M.Z., R.S.W. andJ.H.Z. assisted with experiments; H.T.W., Z.L.W., J.H.L. and M.Y. wrotethe manuscript. All authors have given approval to the final version ofthe manuscript.

# Competing interests

The authors declare no competing interests.

# Additional information

Supplementary information The online version containssupplementary material available athttps://doi.org/10.1038/s41467-023-42393-1.

Correspondence and requests for materials should be addressed toJunhao Li, Xue Qiao or Min Ye.

Peer review information Nature Communications thanks Chin-YuanChang and the other, anonymous, reviewer(s) for their contribution tothe peer review of this work. A peer review file is available.

Reprints and permissions information is available at

http://www.nature.com/reprints

Publisher’s note Springer Nature remains neutral with regard tojurisdictional claims in published maps and institutional affiliations.

Open Access This article is licensed under a Creative CommonsAttribution 4.0 International License, which permits use, sharing,adaptation, distribution and reproduction in any medium or format, aslong as you give appropriate credit to the original author(s) and thesource, provide a link to the Creative Commons license, and indicate ifchanges were made. The images or other third party material in thisarticle are included in the article’s Creative Commons license, unlessindicated otherwise in a credit line to the material. If material is notincluded in the article’s Creative Commons license and your intendeduse is not permitted by statutory regulation or exceeds the permitteduse, you will need to obtain permission directly from the copyrightholder. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/.

$\circledcirc$ The Author(s) 2023