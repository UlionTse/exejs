ExeJS
=====

<p align="center">
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/exejs.svg?color=blue"></a>
  <a href="https://anaconda.org/conda-forge/exejs"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/exejs.svg?color=blue"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/exejs.svg?color=brightgreen"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/exejs.svg?color=blue"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Status" src="https://img.shields.io/pypi/status/exejs.svg?color=brightgreen"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Wheel" src="https://img.shields.io/badge/wheel-yes-brightgreen.svg"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Downloads" src="https://static.pepy.tech/personalized-badge/exejs?period=total&units=international_system&left_text=downloads&left_color=grey&right_color=blue"></a>
</p>

* * *

Run JavaScript code from Python.  

- [Supported Runtime](#supported-runtime)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Reference](#Reference)
- [Why](#Why)
- [Improvement & Change](#Improvement-and-Change)
- [Excellent Case](#Excellent-Case)

## Supported Runtime

| ID  | Runtime        | Browser Engine | Team      |
| --- | -------------- | -------------- | --------- |
| 1   | Node           | Chrome         | Google    |
| 2   | JavaScriptCore | Safari         | Apple     |
| 3   | SpiderMonkey   | Firefox        | Mozilla   |
| 4   | JScript        | IE             | Microsoft |
| 5   | PhantomJS      | Webkit*        | Apple     |
| 6   | SlimerJS       | Gecko*         | Mozilla   |
| 7   | Nashorn        | Java*          | Oracle    |

## Installation

```sh
# PYPI
pip install --upgrade exejs

# Conda
conda install conda-forge::exejs

# Source
git clone https://github.com/UlionTse/exejs.git
cd exejs
python setup.py install
```

## Getting Started

```python
import exejs

# evaluate:
print(exejs.evaluate("'red yellow blue'.split(' ')"))

# call:
print(exejs.compile('function add(x, y) { return x+y; }').call('add', 1, 2))
```

## Reference

[PyExecJS (EOL)](https://github.com/doloopwhile/PyExecJS)

## Why

1. We need to run javascript by python, but pyexecjs was EOL in 2018. [Issue#1](https://github.com/UlionTse/translators/issues/91) 
2. Package builds that rely on pyexecjs will fail or be cancelled. [Issue#2](https://github.com/NixOS/nixpkgs/issues/353446) 
3. Because pyexecjs will temporarily write compiled files by default, it will cause antivirus software to issue an alarm and block the program from running. [Issue#3](https://github.com/UlionTse/translators/issues/168) 

## Improvement and Change

1. Remove the interactive behavior of temporarily writing compiled code locally, and replace it with just-in-time compilation and running.
2. Remove support for python2.

## Excellent Case
[ExsJS](https://github.com/UlionTse/exejs) is currently an important dependency library of [Translators](https://github.com/UlionTse/translators).

