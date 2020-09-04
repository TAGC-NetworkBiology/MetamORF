# -*- coding: utf-8 -*-


# ===============================================================================
# Genetic code
# ===============================================================================

STOP_CODON = '*'

'''
    Description of the available genetic codes is available at: 
    https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
    
    Standard genetic code (corresponding to the table 2 of the 
                           Biopython Bio.Seq.translate method)

    TTT F Phe      TCT S Ser      TAT Y Tyr      TGT C Cys  
    TTC F Phe      TCC S Ser      TAC Y Tyr      TGC C Cys  
    TTA L Leu      TCA S Ser      TAA * Ter      TGA * Ter  
    TTG L Leu i    TCG S Ser      TAG * Ter      TGG W Trp  
    
    CTT L Leu      CCT P Pro      CAT H His      CGT R Arg  
    CTC L Leu      CCC P Pro      CAC H His      CGC R Arg  
    CTA L Leu      CCA P Pro      CAA Q Gln      CGA R Arg  
    CTG L Leu i    CCG P Pro      CAG Q Gln      CGG R Arg  
    
    ATT I Ile      ACT T Thr      AAT N Asn      AGT S Ser  
    ATC I Ile      ACC T Thr      AAC N Asn      AGC S Ser  
    ATA I Ile      ACA T Thr      AAA K Lys      AGA R Arg  
    ATG M Met i    ACG T Thr      AAG K Lys      AGG R Arg  
    
    GTT V Val      GCT A Ala      GAT D Asp      GGT G Gly  
    GTC V Val      GCC A Ala      GAC D Asp      GGC G Gly  
    GTA V Val      GCA A Ala      GAA E Glu      GGA G Gly  
    GTG V Val      GCG A Ala      GAG E Glu      GGG G Gly  
'''


# Custom genetic code
GENETIC_CODE_DNA_SINGLE_LETTER = { 
                                    'ATA':'I',      'ATC':'I',       'ATT':'I',        'ATG':'M', 
                                    'ACA':'T',      'ACC':'T',       'ACG':'T',        'ACT':'T', 
                                    'AAC':'N',      'AAT':'N',       'AAA':'K',        'AAG':'K', 
                                    'AGC':'S',      'AGT':'S',       'AGA':'R',        'AGG':'R',                  
                                    'CTA':'L',      'CTC':'L',       'CTG':'L',        'CTT':'L', 
                                    'CCA':'P',      'CCC':'P',       'CCG':'P',        'CCT':'P', 
                                    'CAC':'H',      'CAT':'H',       'CAA':'Q',        'CAG':'Q', 
                                    'CGA':'R',      'CGC':'R',       'CGG':'R',        'CGT':'R', 
                                    'GTA':'V',      'GTC':'V',       'GTG':'V',        'GTT':'V', 
                                    'GCA':'A',      'GCC':'A',       'GCG':'A',        'GCT':'A', 
                                    'GAC':'D',      'GAT':'D',       'GAA':'E',        'GAG':'E', 
                                    'GGA':'G',      'GGC':'G',       'GGG':'G',        'GGT':'G', 
                                    'TCA':'S',      'TCC':'S',       'TCG':'S',        'TCT':'S', 
                                    'TTC':'F',      'TTT':'F',       'TTA':'L',        'TTG':'L', 
                                    'TAC':'Y',      'TAT':'Y',       'TAA':STOP_CODON, 'TAG':STOP_CODON, 
                                    'TGC':'C',      'TGT':'C',       'TGA':STOP_CODON, 'TGG':'W'           
                                }

# List of stop codon nucleic sequences
STOP_CODON_SEQUENCES = [ 'TAA', 'TGA', 'TAG' ]
