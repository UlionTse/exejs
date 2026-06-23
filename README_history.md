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
- [Reference](#reference)
- [Why](#why)
- [Improvement & Change](#improvement-and-change)
- [Notable Usage](#notable-usage)

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
pip install .
```

## Getting Started

```python
import asyncio
import exejs

# evaluate (one-shot expression):
print(exejs.evaluate("'red yellow blue'.split(' ')"))
# ['red', 'yellow', 'blue']

# execute (one-shot statements; use `return` to send a value back):
print(exejs.execute('var x = 40 + 2; return x;'))
# 42

# compile + call (reuse a JS context across multiple calls):
ctx = exejs.compile('function add(x, y) { return x + y; }')
print(ctx.call('add', 1, 2))   # 3

# call an object method (key may be a property path):
ctx = exejs.compile('var calc = { mul: function(a, b) { return a * b; } };')
print(ctx.call('calc.mul', 3, 4))  # 12

# call with structured arguments (auto JSON-serialized):
ctx = exejs.compile('function greet(u) { return "hi " + u.name + ", age " + u.age; }')
print(ctx.call('greet', {'name': 'Tom', 'age': 18}))  # hi Tom, age 18

# async evaluate:
print(asyncio.run(exejs.evaluate_async("'red yellow blue'.split(' ')")))

# timeout (kill a runaway script instead of hanging forever):
try:
    exejs.execute('while (true) {}', timeout=2.0)
except exejs.ExejsTimeoutError as e:
    print('killed:', str(e))
```

## Reference

[PyExecJS (EOL)](https://github.com/doloopwhile/PyExecJS)

## Why

1. We need to run JavaScript from Python, but PyExecJS has been EOL since 2018. [Issue#1](https://github.com/UlionTse/translators/issues/91) 
2. Package builds that rely on PyExecJS fail or get cancelled. [Issue#2](https://github.com/NixOS/nixpkgs/issues/353446) 
3. PyExecJS writes compiled code to a temp file by default, which triggers antivirus alerts and blocks execution. [Issue#3](https://github.com/UlionTse/translators/issues/168) 

## Improvement and Change

1. Stop writing compiled code to a temp file (except `JScript`); compile and run just-in-time via stdin.
2. Drop Python 2 support.
3. Add an async API.

## Notable Usage
[ExeJS](https://github.com/UlionTse/exejs) is a core dependency of [Translators](https://github.com/UlionTse/translators), where it handles the JavaScript execution layer that translation engines rely on.
