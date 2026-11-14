"""Own-folder Blender runner, with failure exit codes and persistent logs."""
from pathlib import Path
import sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
stage=sys.argv[1];assert stage in ('probe','tones','map','verify','render','pixels')
suffix='_'+sys.argv[sys.argv.index('--batch')+1] if '--batch' in sys.argv else ''
log=ROOT/'reports'/f'{stage}{suffix}.log'
command=['C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe','--background','--python-exit-code','1','--python',str(ROOT/'source'/f'{stage}.py')]
if len(sys.argv)>2:command+=['--']+sys.argv[2:]
with log.open('w',encoding='utf-8') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print(log.read_text(encoding='utf-8',errors='replace')[-5000:]);raise SystemExit(result.returncode)
