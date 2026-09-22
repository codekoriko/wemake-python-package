"""
Does some basic tests on the generated project.

Almost completely taken from (you guys rock!):
https://github.com/pydanny/cookiecutter-django/blob/master/tests
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Final

import pytest
import tomli
from binaryornot.check import is_binary
from cookiecutter.exceptions import FailedHookException
from pytest_cookies.plugin import Cookies

RE_OBJ: Final = re.compile(r'{{(\s?cookiecutter)[.](.*?)}}')


def _build_files_list(root_dir: Path) -> list[Path]:
    """Build a list containing absolute paths to the generated files."""
    return [
        Path(dirpath) / file_path
        for dirpath, _subdirs, files in os.walk(str(root_dir))
        for file_path in files
    ]


def _assert_variables_replaced(paths: list[Path]) -> None:
    """Method to check that all paths have correct substitutions."""
    assert paths, 'No files are generated'

    for path in paths:
        if is_binary(str(path)):
            continue

        file_contents = path.read_text()

        match = RE_OBJ.search(file_contents)
        msg = 'cookiecutter variable not replaced in {0} at {1}'

        # Assert that no match is found:
        assert match is None, msg.format(path, match.start())


def test_with_default_configuration(
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Tests project structure with default prompt values."""
    baked_project = cookies.bake(extra_context=context)

    assert baked_project.exit_code == 0
    assert baked_project.exception is None
    assert baked_project.project_path.name == context['project_name']
    assert baked_project.project_path.is_dir()


def test_variables_replaced(cookies: Cookies, context: dict[str, str]) -> None:
    """Ensures that all variables are replaced inside project files."""
    baked_project = cookies.bake(extra_context=context)
    paths = _build_files_list(baked_project.project_path)

    _assert_variables_replaced(paths)


def test_dynamic_files_generated(
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Ensures that dynamic files are generated."""
    baked_project = cookies.bake(extra_context=context)
    if baked_project.exception is not None:
        raise baked_project.exception

    base_path = baked_project.project_path
    paths = _build_files_list(base_path)

    dynamic_files = [
        'LICENSE',
    ]

    for dynamic_file in dynamic_files:
        assert base_path / dynamic_file in paths


def test_pyproject_toml(cookies: Cookies, context: dict[str, str]) -> None:
    """Ensures that all variables are replaced inside project files."""
    baked_project = cookies.bake(extra_context=context)

    pyproject = tomli.loads(
        (baked_project.project_path / 'pyproject.toml').read_text(),
    )

    project = pyproject['project']
    poetry = pyproject['tool']['poetry']

    assert project['name'] == context['project_name']
    assert project['description'] == context['project_description']
    assert project['urls']['repository'] == 'https://github.com/{}/{}'.format(
        context['organization'],
        context['project_name'],
    )
    assert poetry


@pytest.mark.parametrize(
    ('prompt', 'entered_value'),
    [
        ('project_name', 'myProject'),
        ('project_name', '43prject'),
        ('project_name', '_test'),
        ('project_name', '-test'),
        ('project_name', 'test-'),
        ('project_name', '1_test'),
        ('project_name', 'test@'),
        ('project_name', '0123456'),
    ],
)
def test_validators_work(
    prompt: str,
    entered_value: str,
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Ensures that project can not be created with invalid name."""
    context.update({prompt: entered_value})
    baked_project = cookies.bake(extra_context=context)

    assert isinstance(baked_project.exception, FailedHookException)
    assert baked_project.exit_code == -1


def test_conda_environment_creates_envrc(
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Ensures .envrc and settings.json are created for conda environment."""
    context.update({'conda_environment': 'base'})
    baked_project = cookies.bake(extra_context=context)

    assert baked_project.project_path is not None
    envrc_path = baked_project.project_path / '.envrc'
    assert envrc_path.is_file()
    assert 'layout conda base' in envrc_path.read_text()

    settings_path = baked_project.project_path / '.vscode' / 'settings.json'
    assert settings_path.is_file()
    settings = json.loads(settings_path.read_text())
    assert 'salticidae' not in settings_path.read_text()
    if sys.platform == 'win32':
        assert 'terminal.integrated.env.windows' in settings
    else:
        assert 'terminal.integrated.env.linux' in settings
        assert (
            '${userHome}/miniconda3/envs/base'
            in (settings['python.defaultInterpreterPath'])
        )


def test_conda_environment_not_created_yet_uses_project_name(
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Ensures fallback to project_name when conda env is not created yet."""
    context.update({
        'conda_environment': (
            '[Conda env not created yet - use project_name value]'
        ),
    })
    baked_project = cookies.bake(extra_context=context)

    assert baked_project.project_path is not None
    envrc_path = baked_project.project_path / '.envrc'
    assert f'layout conda {context["project_name"]}' in envrc_path.read_text()

    settings_path = baked_project.project_path / '.vscode' / 'settings.json'
    assert settings_path.is_file()
    assert 'salticidae' not in settings_path.read_text()
    assert context['project_name'] in settings_path.read_text()


def test_conda_environment_none_no_envrc(
    cookies: Cookies,
    context: dict[str, str],
) -> None:
    """Ensures .envrc and settings.json are not created when env is none."""
    context.update({'conda_environment': 'none'})
    baked_project = cookies.bake(extra_context=context)

    assert baked_project.project_path is not None
    envrc_path = baked_project.project_path / '.envrc'
    assert not envrc_path.exists()
    settings_path = baked_project.project_path / '.vscode' / 'settings.json'
    assert not settings_path.exists()
