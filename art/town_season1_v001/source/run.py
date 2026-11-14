"""Background Blender runner. All outputs stay inside the owned season folder."""
import sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BLENDER='C:/Users/hy/AppData/Local/Programs/Blender Foundation/blender-5.2.3-windows-x64/blender.exe'
stage=sys.argv[1] if len(sys.argv)>1 else 'blockout'
SCRIPTS={'blockout':'build_blockout.py','models':'build_models.py','variants':'bake_compact_variants.py','map':'build_map.py','verify':'verify.py','renders':'render.py'}
assert stage in SCRIPTS
command=[BLENDER,'--background','--python-exit-code','1','--python',str(ROOT/'source'/SCRIPTS[stage])]
if len(sys.argv)>2:command+=['--']+sys.argv[2:]
suffix=('_backs' if '--backs' in sys.argv else ('_preview' if '--preview' in sys.argv else '_final')) if stage=='renders' else ''
log=ROOT/'reports'/f'{stage}{suffix}.log'
with log.open('w',encoding='utf-8') as stream:
    result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print(log.read_text(encoding='utf-8',errors='replace')[-5000:])
raise SystemExit(result.returncode)
