# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 15:13:33 2018

@author: u0102617
"""

import codecs
from collections import OrderedDict
import re


conllfile = codecs.open("C:/Users/u0102617/Box Sync/debugfiles/nrc_handelsblad_20001230.conll",'r').readlines()
conllfile2 = codecs.open("C:/Users/u0102617/Box Sync/debugfiles/nrc_handelsblad_20001230.conll",'r').read()
conlllist = list(enumerate(conllfile))

artfile = codecs.open("C:/Users/u0102617/Box Sync/debugfiles/nrc20001230.wpr.art",'r').readlines()

# replace "alpino_ds" boundary tags with "sentence" boundary tags
newartfile = [re.sub(r'alpino_ds','sentence',x) if 'alpino_ds' in x else x for x in artfile]

# find all article-initial token trigrams in the file with article boundaries
tgs = []
for x in newartfile:
    if '<artikel' in x:
        trigram = newartfile[newartfile.index(x)+2:newartfile.index(x)+5]
        tgs += [tuple(y.split("\t")[0] for y in trigram)]

# find all sentence-initial token trigrams in the file without articles boundaries 
# and couple them to the original representation/line in the converted conll-file
sents = OrderedDict()
for i,t in conlllist:
    if '<sentence>' in t:
        trigram = conlllist[i+1:i+4]
        if '</sentence>\n' not in [b for a,b in trigram]:
            sents[tuple(y.split("\t")[1] for x,y in trigram)] = ''.join(y for x,y in trigram)
        else:
            sents[tuple(y for x,y in trigram)] = ''.join(y for x,y in trigram)

# split some items in the tuple-keys of the previous dictionary that could not be split
# cases in which there is a sentence boundary (<sentence>\n or </sentence>\n) in the token trigram
newkeys = []
for x in sents.keys():
    if '<sentence>\n' in x or '</sentence>\n' in x:
        trig = []
        for y in x:
            s = y.split("\t")
            if len(s) > 1:
                trig += [s[1]]
            elif len(s) == 1:
                trig += s
        newkeys += [tuple(trig)]
    else:
        newkeys += [tuple(x)]
        
# create a new dictionary with the new, updated keys
# and mapping the old dictionary values on those new keys
newdict = dict(zip(newkeys,sents.values()))

# filter the dictionary of sentence-initial token trigrams so that
# only sentence-initial trigrams are kept!
finaldict = OrderedDict((k, newdict[k]) for k in tgs)


# add new article tags (<artikellimiet>)
# to the article-initial trigrams 
# (make sure that a "sentence" tag is added to the keys, otherwise you get reduplication)
strings = []
finalkeys = []
for x in finaldict.values(): 
    strings += ['</artikel>\n<artikel>\n<sentence>\n' + x]
    finalkeys += ['<sentence>\n' + x]

# create dictionary with
# KEYS = article-initial sentences in original conll-file
# VALUES = article-initial sentence with article tag
stringsdict = OrderedDict(zip(finalkeys,strings))

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

text = replace_all(conllfile2,stringsdict)

output = codecs.open("C:/Users/u0102617/Box Sync/debugfiles/nrc_handelsblad_art.conll",'w')
output.write("<artikel>\n")
output.write(text)
output.write("</artikel>\n")
output.close()

