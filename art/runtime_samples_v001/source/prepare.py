"""Freeze three reviewed model families for the Android 3D demo handoff."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
FAMILIES = [
    ('house', '주택', 'town_house_florist_v001', [-2.4, -3.2], [2.4, 1.6]),
    ('cafe', '카페', 'town_cafe_v003', [-2.4, -3.2], [2.4, 1.6]),
    ('cathedral', '성당', 'town_season1_v001', [-4.0, -4.65], [3.75, 4.65]),
]
manifest = {
    'schema_version': 1,
    'created_date': '2026-11-10',
    'purpose': 'Frozen temporary samples for Android stage-1 3D conversion; not final season art.',
    'file_format': 'glTF 2.0 binary, self-contained',
    'units': 'metres',
    'gltf_up_axis': '+Y',
    'authoring_axes': 'Blender +Z up, front -Y; respect glTF node transforms on import.',
    'renderer_requirements': ['COLOR_0 vertex colors', 'opaque PBR', 'node transforms and normals'],
    'families': [],
}
(ROOT / 'exports').mkdir(parents=True, exist_ok=True)
for kind, label, version, lot_min, lot_max in FAMILIES:
    family = {'id': kind, 'display_name': label, 'source_version': version,
              'authoring_footprint_xy_min': lot_min, 'authoring_footprint_xy_max': lot_max,
              'levels': []}
    for level in (1, 2, 3):
        source = PROJECT / 'art' / version / 'exports' / f'{kind}_level_{level}.glb'
        raw = source.read_bytes()
        magic, gltf_version, total = struct.unpack_from('<4sII', raw)
        assert magic == b'glTF' and gltf_version == 2 and total == len(raw)
        json_size, chunk_type = struct.unpack_from('<II', raw, 12)
        assert chunk_type == 0x4e4f534a
        doc = json.loads(raw[20:20 + json_size])
        assert len(doc['meshes']) == len(doc['materials']) == 1
        assert not doc.get('textures') and not doc.get('images')
        assert all('uri' not in buffer for buffer in doc['buffers'])
        primitives = doc['meshes'][0]['primitives']
        assert len(primitives) == 1
        p = primitives[0]
        assert all(name in p['attributes'] for name in ('POSITION', 'NORMAL', 'COLOR_0'))
        assert p.get('mode', 4) == 4
        material = doc['materials'][0]
        assert material.get('alphaMode', 'OPAQUE') == 'OPAQUE'
        assert not material.get('doubleSided', False)
        triangles = doc['accessors'][p['indices']]['count'] // 3
        assert triangles <= {1: 4000, 2: 6000, 3: 8000}[level]
        target = ROOT / 'exports' / source.name
        if target.exists():
            assert target.read_bytes() == raw, 'Snapshot already exists with different content: ' + str(target)
        else:
            shutil.copyfile(source, target)
        sha = hashlib.sha256(raw).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == sha
        family['levels'].append({
            'level': level, 'file': target.relative_to(ROOT).as_posix(),
            'source': source.relative_to(PROJECT).as_posix(),
            'sha256': sha, 'bytes': len(raw), 'triangles': triangles,
            'mesh_count': 1, 'material_count': 1, 'primitive_count': 1,
            'textures': 0, 'vertex_color_attribute': 'COLOR_0',
        })
    manifest['families'].append(family)
manifest['validation'] = {
    'files': 9, 'copied_bytes_match_sources': True,
    'glb_headers_and_structure_checked': True,
    'prior_blender_validation_reports': [
        f'art/{version}/reports/validation.json' for _, _, version, _, _ in FAMILIES
    ],
    'android_rendering_verified': False,
}
(ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'families': 3, 'glbs': 9,
                  'bytes': sum(x['bytes'] for f in manifest['families'] for x in f['levels']),
                  'all_copy_and_structure_checks_passed': True}))
