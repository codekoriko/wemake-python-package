"""Hook executed before cookiecutter prompts the user."""

import json
import os
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import Final

BASE_ENV: Final = 'base'
NONE_ENV: Final = 'none'
NOT_CREATED_YET: Final = '[Conda env not created yet - use project_name value]'
EXCLUDED_ENVS: Final = frozenset(('mybase',))
ENCODING: Final = 'utf8'


class _CondaEnvDetector:
    """Helper to detect, resolve, and sort conda environments."""

    @classmethod
    def get_conda_executable(cls) -> str | None:
        conda_exe = os.environ.get('CONDA_EXE')
        if conda_exe and Path(conda_exe).is_file():
            return conda_exe
        return shutil.which('conda')

    @classmethod
    def envs_from_cli(
        cls,
        conda_bin: str,
    ) -> tuple[list[str], str | None, str | None]:
        cmd = [conda_bin, 'info', '--envs', '--json']
        try:
            output = subprocess.check_output(  # noqa: S603
                cmd,
                universal_newlines=True,
                encoding=ENCODING,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            return ([], None, None)
        parsed = json.loads(output)
        return (
            parsed.get('envs', []),
            parsed.get('root_prefix'),
            parsed.get('active_prefix'),
        )

    @classmethod
    def envs_from_txt(cls) -> list[str]:
        env_txt = Path.home() / '.conda' / 'environments.txt'
        if not env_txt.is_file():
            return []
        try:
            raw_text = env_txt.read_text(encoding=ENCODING)
        except Exception:
            return []
        lines = raw_text.splitlines()
        return [line.strip() for line in lines if line.strip()]

    @classmethod
    def resolve_name(cls, env_path_str: str, root_prefix: str | None) -> str:
        real_path = os.path.realpath(env_path_str)
        if root_prefix and real_path == os.path.realpath(root_prefix):
            return BASE_ENV
        return Path(real_path).name

    @classmethod
    def determine_active_name(
        cls,
        active_prefix: str | None,
        root_prefix: str | None,
    ) -> str | None:
        if active_prefix:
            return cls.resolve_name(active_prefix, root_prefix)
        conda_default = os.environ.get('CONDA_DEFAULT_ENV')
        if conda_default:
            return conda_default
        env_prefix = os.environ.get('CONDA_PREFIX')
        if env_prefix:
            return cls.resolve_name(env_prefix, root_prefix)
        return None

    @classmethod
    def fetch_env_data(cls) -> tuple[list[str], str | None, str | None]:
        conda_bin = cls.get_conda_executable()
        if conda_bin:
            paths, root_prefix, active_prefix = cls.envs_from_cli(conda_bin)
            if paths:
                return paths, root_prefix, active_prefix
        return cls.envs_from_txt(), None, None

    @classmethod
    def detect(cls) -> list[str]:
        raw_paths, root_prefix, active_prefix = cls.fetch_env_data()
        active_name = cls.determine_active_name(active_prefix, root_prefix)
        sorted_names = sorted(
            {cls.resolve_name(path, root_prefix) for path in raw_paths}
            - EXCLUDED_ENVS
        )

        if active_name and active_name in sorted_names:
            sorted_names.remove(active_name)
            sorted_names.append(active_name)
        elif BASE_ENV in sorted_names:
            sorted_names.remove(BASE_ENV)
            sorted_names.append(BASE_ENV)

        if NONE_ENV not in sorted_names:
            sorted_names.append(NONE_ENV)

        sorted_names.insert(0, NOT_CREATED_YET)
        return sorted_names


def update_cookiecutter_context() -> None:
    """Inject detected conda environments into cookiecutter.json."""
    config_file = Path('cookiecutter.json')
    if not config_file.is_file():
        return

    try:
        file_text = config_file.read_text(encoding=ENCODING)
    except Exception as err:
        sys.stderr.write(f'Warning: could not read cookiecutter.json: {err}\n')
        return

    context = json.loads(file_text)
    context['conda_environment'] = _CondaEnvDetector.detect()
    config_file.write_text(
        f'{json.dumps(context, indent=2)}\n',
        encoding=ENCODING,
    )


if __name__ == '__main__':
    update_cookiecutter_context()
