import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    command=shutil.which('pdb-drain-witness')
    assert command, 'installed console command missing from PATH'
    data=json.loads((Path(__file__).parent/'example.json').read_text())
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'snapshot.json';path.write_text(json.dumps(data))
        result_run=subprocess.run([command,str(path)],cwd=d,capture_output=True,text=True)
        assert result_run.returncode == 0, result_run.stderr
        result=json.loads(result_run.stdout)
        assert result['wave'] == ['default/web-a']; assert result['pods'][1]['decision'] == 'hold'
        path.write_text('{}')
        failed=subprocess.run([command,str(path)],cwd=d,capture_output=True,text=True)
        assert failed.returncode == 2 and failed.stderr.startswith('error:'), failed
    print('installed example and malformed-input failure verified')


if __name__=='__main__':main()
