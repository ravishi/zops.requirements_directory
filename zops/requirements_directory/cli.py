# -*- coding: utf-8 -*-
import os

import click
from zerotk.zops import Console


click.disable_unicode_literals_warning = True


@click.group('requirements-directory')
def main():
    pass


@main.command()
@click.option('--update', is_flag=True, help='Updates all libraries versions.')
def compile(update):
    """
    Update requirements
    """
    from glob import glob

    def get_input_filenames(filename):
        import os

        result = []
        include_lines = [i for i in open(filename, 'r').readlines() if i.startswith('#!INCLUDE')]
        for i_line in include_lines:
            included_filename = i_line.split(' ', 1)[-1].strip()
            included_filename = os.path.join(os.path.dirname(filename), included_filename)
            result.append(included_filename)
        result.append(filename)
        return result

    def get_temporary_dependencies(filename):
        """
        List all dependencies declared in the input file that must be removed from the generated file (temporary).
        """
        result = []
        with open(filename, 'r') as iss:
            for i_line in iss.readlines():
                if '#!TEMPORARY' in i_line:
                    i_line = i_line.rsplit('#')[0]
                    i_line = i_line.strip()
                    result.append(i_line)
        return result

    def get_output_filename(filename):
        import os
        return os.path.splitext(filename)[0] + '.txt'

    def fixes(filename, temporary_dependencies):
        def replace_file_references(line):
            """
            Replaces file:// references by local ones.
            """
            parts = line.split('file://')
            if len(parts) > 1:
                ref_path = parts[-1]
                rel_path = os.path.relpath(ref_path)
                return '-e {}'.format(rel_path)
            return line

        def is_setuptools_dependency(line):
            """
            Remove setuptools dependencies from the generated file.
            """
            return 'via setuptools' in line

        def is_temporary_dependency(line):
            """
            Remove lines
            """
            for i_temporary_dependency in temporary_dependencies:
                if i_temporary_dependency in line:
                    return True
            return False

        with open(filename, 'r') as iss:
            lines = iss.readlines()
        lines = [replace_file_references(i) for i in lines]
        lines = [i for i in lines if not is_setuptools_dependency(i)]
        lines = [i for i in lines if not is_temporary_dependency(i)]
        with open(filename, 'w') as oss:
            oss.writelines(lines)

    base_params = ['--no-index', '--no-emit-trusted-host', '-r']
    if update:
        base_params += ['-U']

    for i_filename in glob('requirements/*.in'):
        output_filename = get_output_filename(i_filename)
        input_filenames = get_input_filenames(i_filename)
        temporary_dependencies = get_temporary_dependencies(i_filename)
        Console.info('{}: generating from {}'.format(output_filename, ', '.join(input_filenames)))

        params = base_params + input_filenames + ['-o', output_filename]
        Console.execution('pip-compile {}'.format(' '.join(params)))
        _pip_compile(*params)
        Console.info('{}: '.format(output_filename))
        fixes(output_filename, temporary_dependencies)


def _pip_compile(*args):
    """
    Performs pip-compile (from piptools) with a twist.

    We force editable requirements to use GIT repository (parameter obtain=True) so we have setuptools_scm working on
    them (axado.runner uses setuptools_scm).
    """
    from contextlib import contextmanager

    @contextmanager
    def replaced_argv(args):
        import sys
        argv = sys.argv
        sys.argv = [''] + list(args)
        yield
        sys.argv = argv

    from pip.req.req_install import InstallRequirement
    try:
        InstallRequirement.update_editable_
    except AttributeError:
        InstallRequirement.update_editable_ = InstallRequirement.update_editable
        InstallRequirement.update_editable = lambda s, _o: InstallRequirement.update_editable_(s, True)

    with replaced_argv(args):
        from piptools.scripts.compile import cli
        try:
            cli()
        except SystemExit as e:
            return e.code


if __name__ == '__main__':
    main()
