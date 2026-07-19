import sys, os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import categorize
# default: the folder that CONTAINS this tool folder (i.e. your "House Bills" folder)
folder=sys.argv[1] if len(sys.argv)>1 else os.path.dirname(HERE)
folder=os.path.abspath(folder)
print("Reading bills from:",folder,"\n")
res=categorize.generate(folder, outdir=HERE, progress=lambda m:print("  -",m))
print(); print("\n".join(res['summary_lines']))
print("\nSaved next to this program:")
for k,v in res['files'].items(): print("  ",os.path.basename(v))
