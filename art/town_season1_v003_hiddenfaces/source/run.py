"""Run only the owned scripts, with nonzero Blender Python error exits."""
import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXE='C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
stage=sys.argv[1];assert stage in ('optimize','map','verify','render','pixels')
suffix='_'+sys.argv[sys.argv.index('--batch')+1] if '--batch' in sys.argv else ''
log=ROOT/'reports'/f'{stage}{suffix}.log'
with log.open('w',encoding='utf-8') as stream:
    command=[EXE,'--background','--python-exit-code','1','--python',str(ROOT/'source'/f'{stage}.py')]
    if len(sys.argv)>2:command+=['--']+sys.argv[2:]
    result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print(log.read_text(encoding='utf-8',errors='replace')[-3500:]);raise SystemExit(result.returncode)
