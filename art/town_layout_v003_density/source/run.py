"""Run the background comparison without PowerShell profile/transcript side effects."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
preview='--preview' in sys.argv
log=ROOT/'reports'/('preview.log' if preview else 'final.log')
blender='C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
command=[blender,
         '--background','--python-exit-code','1','--python',str(ROOT/'source/build_density.py')]
if preview:command+=['--','--preview']
def run(command,log):
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    print(log.read_text(encoding='utf-8',errors='replace')[-3500:])
    if result.returncode:raise SystemExit(result.returncode)
if '--verify-only' not in sys.argv:run(command,log)
if not preview:
    run([blender,'--background',str(ROOT/'blend/chagok_density_comparison.blend'),'--python-exit-code','1','--python',str(ROOT/'source/verify_blend.py')],ROOT/'reports/reopen.log')
