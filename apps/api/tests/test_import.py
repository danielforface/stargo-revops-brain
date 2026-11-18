import sys
import zipfile
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from import_take_home import EXPECTED, import_pack


def test_private_import(tmp_path):
    archive=tmp_path/"pack.zip"
    with zipfile.ZipFile(archive,'w') as zf:
        for name in EXPECTED:
            zf.writestr('StargoTakeHome/data/'+name, 'fixture')
        zf.writestr('StargoTakeHome/../../.env', 'secret')
    output=tmp_path/"dest"
    assert len(import_pack(archive,output))==len(EXPECTED)
    assert sorted(p.name for p in output.iterdir())==sorted(EXPECTED)
    assert not (tmp_path/'.env').exists()


def test_incomplete_import_does_not_write(tmp_path):
    archive=tmp_path/'incomplete.zip'
    with zipfile.ZipFile(archive,'w') as zf:
        zf.writestr('data/gtm_events.json','{}')
    with pytest.raises(ValueError,match='Missing'):
        import_pack(archive,tmp_path/'dest')
    assert not (tmp_path/'dest').exists()
