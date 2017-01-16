# zops.requirements_directory

This plugin for [zops](https://github.com/zerotk/zops) adds suport to manage Python requirements in a directory, using [pip-tools](https://github.com/nvie/pip-tools).

## Instalation

```bash
$ pip install zops.requirements_directory
```

## Usage

Place your python dependencies files inside the `requirements` directory, using the `.in` exension. Declare the dependencies with minimal
version references.

```
/requirements
  /production.in
  /development.in
```

Use the `req compile` command to generate the final `.txt` files, with pinned versions:

```bash
$ zops req compile
/requirements/production.txt (sources: /requirements/production.in)
/requirements/development.txt (sources: /requirements/development.in, /requirements/production.in)
```
Use the `--update` option to also update all the dependencies versions.

```bash
$ zops req compile --update
```

## Include directive

You can "include" other ".in" files using the include directive as follows:

```
#!INCLUDE production.in
```

# Examples

### requirements/production.in

```
django
```

### requirements/development.in

```
#!INCLUDE production.in
zops.requirements_directory
pytest-django
```
