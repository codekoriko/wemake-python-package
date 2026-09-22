"""
This module is called after project is created.

From pydanny's cookiecutter-django:
https://github.com/pydanny/cookiecutter-django

"""

import json
import shutil
import subprocess  # noqa: S404
import sys
import textwrap
from pathlib import Path
from typing import Final

# Get the root project directory:
PROJECT_DIRECTORY = Path.cwd().resolve(strict=True)
PROJECT_NAME: Final = '{{ cookiecutter.project_name }}'
ENCODING: Final = 'utf8'

# We need these values to generate correct license:
LICENSE: Final = '{{ cookiecutter.license }}'
ORGANIZATION: Final = '{{ cookiecutter.organization }}'
ADD_DOCS_SUPPORT: Final = '{{ cookiecutter.add_docs_support }}'
NOT_CREATED_YET: Final = '[Conda env not created yet - use project_name value]'
NONE_ENV: Final = 'none'
ENV_PATH_VAR: Final = r'${env:PATH}'
RAW_CONDA_ENV: Final[str] = '{{ cookiecutter.conda_environment }}'.strip()
CONDA_ENV: Final[str] = (
    PROJECT_NAME if RAW_CONDA_ENV == NOT_CREATED_YET else RAW_CONDA_ENV
)


def generate_license() -> None:
    """Generates license file for the project."""
    license_result = subprocess.check_output(  # noqa: S603
        [  # noqa: S607
            'lice',
            LICENSE.lower(),
            '-o',
            ORGANIZATION,
            '-p',
            PROJECT_NAME,
        ],
        universal_newlines=True,
        encoding=ENCODING,
    )
    with (PROJECT_DIRECTORY / 'LICENSE').open(
        mode='w',
        encoding=ENCODING,
    ) as license_file:
        license_file.write(
            license_result.strip()
            .replace(' \n ', ' \n')
            .replace('\n \n', '\n\n'),
        )
        license_file.write('\n')


def handle_docs_support() -> None:
    """Remove docs directory if documentation support is not needed."""
    if ADD_DOCS_SUPPORT == 'n':  # type: ignore[comparison-overlap]
        docs_dir = PROJECT_DIRECTORY / 'docs'
        if docs_dir.exists():
            shutil.rmtree(docs_dir)


def _get_vscode_settings() -> dict[str, object]:
    """Build platform-specific vscode settings for selected conda env."""
    if sys.platform == 'win32':
        prefix = f'D:/miniconda3/envs/{CONDA_ENV}'
        win_path_parts = (
            prefix,
            f'{prefix}/Library/bin',
            f'{prefix}/Scripts',
            ENV_PATH_VAR,
        )
        return {
            'terminal.integrated.env.windows': {
                'PATH': ';'.join(win_path_parts),
                'CONDA_PREFIX': prefix,
                'CONDA_DEFAULT_ENV': CONDA_ENV,
            },
            'python.defaultInterpreterPath': f'{prefix}/python.exe',
        }

    prefix = f'{Path.home()}/miniconda3/envs/{CONDA_ENV}'
    linux_path = f'{prefix}/bin:{ENV_PATH_VAR}'
    return {
        'terminal.integrated.env.linux': {
            'PATH': linux_path,
            'CONDA_PREFIX': prefix,
            'CONDA_DEFAULT_ENV': CONDA_ENV,
        },
        'python.defaultInterpreterPath': f'{prefix}/bin/python',
    }


def handle_conda_environment() -> None:
    """Creates .envrc and .vscode/settings.json if conda env was selected."""
    if CONDA_ENV == NONE_ENV:
        return

    envrc_file = PROJECT_DIRECTORY / '.envrc'
    envrc_file.write_text(f'layout conda {CONDA_ENV}\n', encoding=ENCODING)

    vscode_dir = PROJECT_DIRECTORY / '.vscode'
    vscode_dir.mkdir(exist_ok=True)
    settings_file = vscode_dir / 'settings.json'
    settings = _get_vscode_settings()

    settings_file.write_text(
        f'{json.dumps(settings, indent=2)}\n',
        encoding=ENCODING,
    )


def print_futher_instuctions() -> None:
    """Shows user what to do next after project creation."""
    gh_cmd = (
        'gh repo create (Get-Item .).Basename --private --source=.'
        if sys.platform == 'win32'
        else 'gh repo create "$(basename $(pwd))" --private --source=.'
    )
    conda_step = ''
    if CONDA_ENV != NONE_ENV:
        step_lines = (
            '',
            '    Activate conda environment:',
            f'        conda activate {CONDA_ENV}',
        )
        conda_step = '\n'.join(step_lines)
    message = """
    Your project {0} is created.
    Now you can start working on it:

        cd {0}{2}

    One liner to create github Private Repo:
        cd {0} && git init && git add . && git commit -m "Initial commit" && {1}
    """
    print(textwrap.dedent(message.format(PROJECT_NAME, gh_cmd, conda_step)))  # noqa: WPS421


generate_license()
handle_docs_support()
handle_conda_environment()
print_futher_instuctions()
