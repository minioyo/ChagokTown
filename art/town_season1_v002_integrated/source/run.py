import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BLENDER='C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
stage=sys.argv[1];assert stage in ('study','models','map','verify','render')
suffix=('_preview' if '--preview' in sys.argv else '')+('_qa' if '--qa' in sys.argv else '')
log=ROOT/'reports'/f'{stage}{suffix}.log'
command=[BLENDER,'--background','--python-exit-code','1','--python',str(ROOT/'source'/f'{stage}.py')]
if len(sys.argv)>2:command+=['--']+sys.argv[2:]
with log.open('w',encoding='utf-8') as stream:
    result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print(log.read_text(encoding='utf-8',errors='replace')[-5000:]);raise SystemExit(result.returncode)
