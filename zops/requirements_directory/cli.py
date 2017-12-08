# -*- coding: utf-8 -*-
import os

import click
from zerotk.zops import Console
from zerotk.lib.path import popd


click.disable_unicode_literals_warning = True


@click.group('requirements-directory')
def main():
    pass


@main.command()
@click.option('--upgrade', is_flag=True, help='Try to upgrade all dependencies to their latest versions.')
@click.option('--rebuild', is_flag=True, help='Clear any caches upfront, rebuild from scratch.')
def compile(upgrade, rebuild):
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
        return [os.path.abspath(i) for i in result]

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
        return os.path.abspath(os.path.splitext(filename)[0] + '.txt')

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

    # base_params = ['--no-index', '--no-emit-trusted-host', '-r']
    # if update:
    #     base_params += ['-U']

    # NOTE: Create before the loop to maintain the dependencies-cache.
    pip_tools = PipTools()

    for i_filename in glob('./**/requirements/*.in', recursive=True):
        output_filename = get_output_filename(i_filename)
        input_filenames = get_input_filenames(i_filename)
        temporary_dependencies = get_temporary_dependencies(i_filename)

        Console.item(output_filename)
        for k_input_filename in input_filenames:
            Console.item(k_input_filename, ident=1)

        cwd = os.path.normpath(output_filename + '/../..')
        Console.item(cwd)
        with popd(cwd):
            pip_tools.compile(output_filename, input_filenames, upgrade=upgrade, rebuild=rebuild)
        Console.info('{}: '.format(output_filename))
        fixes(output_filename, temporary_dependencies)


class PipTools(object):

    def __init__(self):
        from zops.piptools.cache import DependencyCache
        self.dependency_cache = DependencyCache()

    def compile(self, dst_file, src_files, upgrade=False, rebuild=False):
        """
        Performs pip-compile (from piptools) with a twist.

        We force editable requirements to use GIT repository (parameter obtain=True) so we have setuptools_scm working on
        them (we use setuptools_scm).
        """
        from pip.req.req_install import InstallRequirement

        # NOTE: Debugging
        # Show some debugging information.
        # from zops.piptools.logging import log
        # log.verbose = True

        try:
            InstallRequirement.update_editable_
        except AttributeError:
            InstallRequirement.update_editable_ = InstallRequirement.update_editable
            InstallRequirement.update_editable = lambda s, _o: InstallRequirement.update_editable_(s, True)

        return self._piptools_cli(dst_file, src_files, upgrade=upgrade, rebuild=False)

    def _piptools_cli2(
        self,
        dst_file,
        src_files,
        upgrade=False,
        upgrade_packages=[],
        rebuild=False,
        allow_unsafe=False,
        max_rounds=10,
        generate_hashes=False,
        annotate=True,
        header=True,
        index=False,
        emit_trusted_host=False,
        dry_run=False,
    ):
        from zops.piptools.scripts.compile import get_pip_command
        from zops.piptools.repositories import PyPIRepository, LocalRequirementsRepository
        from zops.piptools.utils import key_from_req, is_pinned_requirement, dedup
        from zops.piptools.resolver import Resolver
        from zops.piptools.logging import log
        from pip.req import InstallRequirement, parse_requirements
        import tempfile
        import sys

        pip_command = get_pip_command()

        pip_args = []
        # if find_links:
        #     for link in find_links:
        #         pip_args.extend(['-f', link])
        # if index_url:
        #     pip_args.extend(['-i', index_url])
        # if extra_index_url:
        #     for extra_index in extra_index_url:
        #         pip_args.extend(['--extra-index-url', extra_index])
        # if cert:
        #     pip_args.extend(['--cert', cert])
        # if client_cert:
        #     pip_args.extend(['--client-cert', client_cert])
        # if pre:
        #     pip_args.extend(['--pre'])
        # if trusted_host:
        #     for host in trusted_host:
        #         pip_args.extend(['--trusted-host', host])

        pip_options, _ = pip_command.parse_args(pip_args)

        session = pip_command._build_session(pip_options)
        repository = PyPIRepository(pip_options, session)

        # Proxy with a LocalRequirementsRepository if --upgrade is not specified
        # (= default invocation)
        if not upgrade and os.path.exists(dst_file):
            ireqs = parse_requirements(
                dst_file, finder=repository.finder, session=repository.session, options=pip_options
            )
            # Exclude packages from --upgrade-package/-P from the existing pins: We want to upgrade.
            upgrade_pkgs_key = {
                key_from_req(InstallRequirement.from_line(pkg).req)
                for pkg in upgrade_packages
            }
            existing_pins = {
                key_from_req(ireq.req): ireq
                for ireq in ireqs
                if is_pinned_requirement(ireq) and key_from_req(ireq.req) not in upgrade_pkgs_key
            }
            repository = LocalRequirementsRepository(existing_pins, repository)

        log.debug('Using indexes:')
        # remove duplicate index urls before processing
        repository.finder.index_urls = list(dedup(repository.finder.index_urls))
        for index_url in repository.finder.index_urls:
            log.debug('  {}'.format(index_url))

        if repository.finder.find_links:
            log.debug('')
            log.debug('Configuration:')
            for find_link in repository.finder.find_links:
                log.debug('  -f {}'.format(find_link))

        ###
        # Parsing/collecting initial requirements
        ###

        constraints = []
        for src_file in src_files:
            is_setup_file = os.path.basename(src_file) == 'setup.py'
            if is_setup_file or src_file == '-':
                # pip requires filenames and not files. Since we want to support
                # piping from stdin, we need to briefly save the input from stdin
                # to a temporary file and have pip read that.  also used for
                # reading requirements from install_requires in setup.py.
                tmpfile = tempfile.NamedTemporaryFile(mode='wt', delete=False)
                if is_setup_file:
                    from distutils.core import run_setup
                    dist = run_setup(src_file)
                    tmpfile.write('\n'.join(dist.install_requires))
                else:
                    tmpfile.write(sys.stdin.read())
                tmpfile.flush()
                constraints.extend(parse_requirements(
                    tmpfile.name, finder=repository.finder, session=repository.session, options=pip_options))
            else:
                constraints.extend(parse_requirements(
                    src_file, finder=repository.finder, session=repository.session, options=pip_options))

        # Check the given base set of constraints first
        Resolver.check_constraints(constraints)

        from zops.piptools.exceptions import PipToolsError
        try:
            resolver = Resolver(
                constraints,
                repository,
                prereleases=False,
                cache=self.dependency_cache,
                clear_caches=rebuild,
                allow_unsafe=allow_unsafe
            )
            results = resolver.resolve(max_rounds=max_rounds)
            if generate_hashes:
                hashes = resolver.resolve_hashes(results)
            else:
                hashes = None
        except PipToolsError as e:
            log.error(str(e))
            sys.exit(2)

        log.debug('')

        ##
        # Output
        ##

        # Compute reverse dependency annotations statically, from the
        # dependency cache that the resolver has populated by now.
        #
        # TODO (1a): reverse deps for any editable package are lost
        #            what SHOULD happen is that they are cached in memory, just
        #            not persisted to disk!
        #
        # TODO (1b): perhaps it's easiest if the dependency cache has an API
        #            that could take InstallRequirements directly, like:
        #
        #                cache.set(ireq, ...)
        #
        #            then, when ireq is editable, it would store in
        #
        #              editables[egg_name][link_without_fragment] = deps
        #              editables['pip-tools']['git+...ols.git@future'] = {'click>=3.0', 'six'}
        #
        #            otherwise:
        #
        #              self[as_name_version_tuple(ireq)] = {'click>=3.0', 'six'}
        #
        reverse_dependencies = None
        if annotate:
            reverse_dependencies = resolver.reverse_dependencies(results)

        from zops.piptools.writer import OutputWriter
        writer = OutputWriter(
            src_files,
            dst_file,
            dry_run=dry_run,
            emit_header=header,
            emit_index=index,
            emit_trusted_host=emit_trusted_host,
            annotate=annotate,
            generate_hashes=generate_hashes,
            default_index_url=repository.DEFAULT_INDEX_URL,
            index_urls=repository.finder.index_urls,
            trusted_hosts=pip_options.trusted_hosts,
            format_control=repository.finder.format_control
        )
        writer.write(
            results=results,
            unsafe_requirements=resolver.unsafe_constraints,
            reverse_dependencies=reverse_dependencies,
            primary_packages={key_from_req(ireq.req) for ireq in constraints if not ireq.constraint},
            markers={
                key_from_req(ireq.req): ireq.markers
                for ireq in constraints
                if ireq.markers
            },
            hashes=hashes,
            allow_unsafe=allow_unsafe
        )

        if dry_run:
            log.warning('Dry-run, so nothing updated.')


if __name__ == '__main__':
    main()
