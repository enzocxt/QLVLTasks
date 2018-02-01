import re
import codecs
import os
import errno

conllPath = "/home/stefano/TokenClouds/dependencyCONLL/WRPPG_1.conll.txt"

conllFile = codecs.open(conllPath,"r",encoding="latin1").readlines()
conllText = codecs.open(conllPath,"r",encoding="latin1").read()


filelist = []
for x in conllFile:
	filelist += re.findall(r'<file-id>([^<]+)</file-id>',x)

fileset = list(set(filelist))

# remove unparsed sentences (WRPPG_1: 392)
fileset.remove("t_of_memory")
fileset.remove("me_out")
fileset.remove("art_hook(time_out)")


metaBE = "/home/stefano/WR-P-P-G_newspapers.lectinfo.bel.txt"
metaNL = "/home/stefano/WR-P-P-G_newspapers.lectinfo.ned.txt"

metaBEFile = codecs.open(metaBE,"r",encoding="latin1").readlines()
metadataBE = [line.strip().split('"') for line in metaBEFile]

dictBE = dict((x[1][:-9],(x[11],"".join(x[13].split("-")))) for x in metadataBE[1:])

metaNLFile = codecs.open(metaNL,"r",encoding="latin1").readlines()
metadataNL = [line.strip().split('"') for line in metaNLFile]

for x in metadataNL[1:]:
	if x[3].startswith("WR-P"):
		x[3] = "unknown"
	else:
		x1 = x[3].split(": ")[1]
		x2 = x1.replace(" ","_").lower()
		x[3] = x2
		

dictNL = dict((x[1][:-9],(x[3],"".join(x[13].split("-")))) for x in metadataNL[1:])
dictNL.update(dictBE)

kranten = []
for x in fileset:
	kranten += [(dictNL[x][0])]


for name in fileset:
	my_regex = r'<pre>\n   <code sentence-id="file:/home/aardvark/corp/nl/SONAR_ccl/WRPPG_1/[^"]+">\n      <file-id>' + name + r'</file-id>.+?</pre>'
	file = re.findall(my_regex,conllText, re.DOTALL)
	krant = dictNL[name][0]
	if krant in ['nrc_handelsblad','trouw','volkskrant','unknown','algemeen_dagblad']:
			nation = "Netherlands"
	if krant in ['de_standaard','dm_magazine','de_morgen']:
			nation = "Belgium"
	jaar = dictNL[name][1][0:4]
	datum = dictNL[name][1]
	newpath = "/home/stefano/TokenClouds/dependencyCONLL/" + nation + "/" + jaar + "/" + krant + "/" + krant + datum + "_" + name[9:] + ".conll"
	if not os.path.exists(os.path.dirname(newpath)):
		try:
			os.makedirs(os.path.dirname(newpath))
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	conllsingle = codecs.open(newpath,'w',encoding='latin1')
	for line in file:
		conllsingle.write(line)
