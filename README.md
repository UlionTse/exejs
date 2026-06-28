<div align="center">

<img src="docs/logo.svg" width="380" alt="ExeJS">

```text
███████╗██╗  ██╗███████╗     ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝     ██║██╔════╝
█████╗   ╚███╔╝ █████╗       ██║███████╗
██╔══╝   ██╔██╗ ██╔══╝  ██   ██║╚════██║
███████╗██╔╝ ██╗███████╗╚█████╔╝███████║
╚══════╝╚═╝  ╚═╝╚══════╝ ╚════╝ ╚══════╝
```

**Run JavaScript from Python — the modern successor to PyExecJS.**

Zero dependencies · Multi-runtime auto-detection · Async-ready · No temp files · Timeout guard

<p>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/exejs.svg?color=blue"></a>
  <a href="https://anaconda.org/conda-forge/exejs"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/exejs.svg?color=blue"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/exejs.svg?color=blue"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/exejs.svg?color=brightgreen"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Status" src="https://img.shields.io/pypi/status/exejs.svg?color=brightgreen"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Wheel" src="https://img.shields.io/badge/wheel-yes-brightgreen.svg"></a>
  <a href="https://pypi.org/project/exejs"><img alt="PyPI - Downloads" src="https://static.pepy.tech/personalized-badge/exejs?period=total&units=international_system&left_text=downloads&left_color=grey&right_color=blue"></a>
</p>

</div>

---

## Table of Contents

- [Features](#features)
- [Why ExeJS](#why-exejs)
- [Comparison](#comparison)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Runtimes](#supported-runtimes)
- [API Reference](#api-reference)
- [Advanced](#advanced)
- [FAQ](#faq)
- [Changelog](#changelog)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [Notable Usage](#notable-usage)
- [License](#license)

## Features

- **Multi-runtime** — auto-detects among Node, JavaScriptCore, SpiderMonkey, JScript, PhantomJS, SlimerJS, and Nashorn.
- **Zero dependencies** — built on the Python standard library; `pip install exejs` and you're done.
- **Async-ready** — `evaluate_async` / `execute_async` / `call_async` built on `asyncio`.
- **No temp files** — compiles and runs via stdin (except `JScript`), so it won't trigger antivirus alerts.
- **Timeout guard** — `timeout` parameter kills runaway scripts instead of hanging forever.
- **Structured args** — `call()` auto JSON-serializes objects and supports property paths like `calc.mul`.
- **Typed** — ships `py.typed`, fully annotated, Python 3.9+.

## Why ExeJS

PyExecJS has been EOL since 2018. ExeJS exists to fix three concrete pain points:

1. PyExecJS is unmaintained, and downstream builds that depend on it fail or get cancelled. ([Issue#1](https://github.com/UlionTse/translators/issues/91), [Issue#2](https://github.com/NixOS/nixpkgs/issues/353446))
2. PyExecJS writes compiled code to a temp file by default, which triggers antivirus alerts and blocks execution. ([Issue#3](https://github.com/UlionTse/translators/issues/168))
3. No async API, no timeout control, still carries Python 2 baggage.

## Comparison

| | PyExecJS (EOL 2018) | ExeJS |
|---|:---:|:---:|
| Maintained | stopped 2018 | active |
| Python 2 | yes | no (3.9+) |
| Async API | — | yes |
| Temp files | yes (antivirus alerts) | no (stdin, except JScript) |
| Timeout | — | yes |
| Context reuse (`compile`/`call`) | limited | yes |
| Structured args (auto JSON, property paths) | — | yes |
| Dependencies | some (`six`) | zero |
| Typed (`py.typed`) | — | yes |

## Requirements

- **Python** >= 3.9
- **A JavaScript runtime** installed and on `PATH` — Node.js is the recommended default. See [Supported Runtimes](#supported-runtimes) for the full list and install hints.

## Installation

```sh
# PyPI
pip install --upgrade exejs

# Conda
conda install conda-forge::exejs

# From source
git clone https://github.com/UlionTse/exejs.git
cd exejs
pip install .
```

## Quick Start

```python
import exejs

exejs.evaluate("[1, 2, 3].map(x => x * 2)")  # [2, 4, 6]

# evaluate (one-shot expression)
exejs.evaluate("'red yellow blue'.split(' ')")  # ['red', 'yellow', 'blue']

# execute (one-shot statements; use `return` to send a value back)
exejs.execute('var x = 40 + 2; return x;')  # 42
```

For context reuse, structured args, async, and timeout, see [Advanced](#advanced).

## Supported Runtimes

| Runtime | Command | Engine | Install / Notes |
|---|---|---|---|
| Node | `node` | Chrome (V8) | recommended, all platforms — [nodejs.org/download](https://nodejs.org/en/download) |
| NodeJS | `nodejs` | Chrome (V8) | Debian/Ubuntu alias of Node |
| JavaScriptCore | `jsc` | Safari (WebKit) | macOS only (bundled) |
| SpiderMonkey | `js` | Firefox (Gecko) | `js` package on most Linux distros |
| Phantomjs | `phantomjs` | WebKit | upstream abandoned 2018 |
| SlimerJS | `slimerjs` | Gecko | upstream abandoned 2021 |
| Nashorn | `jjs` | Java (JVM) | Oracle JDK; removed since JDK 15 |
| JScript | `cscript //E:jscript //Nologo` | IE (Trident) | Windows only (built-in); uses temp file |

ExeJS auto-detects the first available runtime in the order above. Use `reset_runtime` to pick one explicitly.

## API Reference

### Top-level functions

```python
exejs.evaluate(source: str, timeout: float | None = None) -> Any
exejs.execute(source: str, timeout: float | None = None) -> Any
exejs.compile(source: str = '', cwd: str | None = None) -> RuntimeCompileContext

async exejs.evaluate_async(source: str, timeout: float | None = None) -> Any
async exejs.execute_async(source: str, timeout: float | None = None) -> Any
```

### Compile context

```python
ctx = exejs.compile(source='', cwd=None)

ctx.call(key: str, *args, timeout: float | None = None) -> Any        # key supports paths like 'calc.mul'
ctx.evaluate(source: str, timeout: float | None = None) -> Any
ctx.execute(source: str, timeout: float | None = None) -> Any

async ctx.call_async(key: str, *args, timeout: float | None = None) -> Any
async ctx.evaluate_async(source: str, timeout: float | None = None) -> Any
async ctx.execute_async(source: str, timeout: float | None = None) -> Any
```

### Runtime management

```python
exejs.reset_runtime(name: str) -> None                       # switch runtime by name
exejs.get_current_runtime() -> Runtime
exejs.get_current_runtime_name() -> str
exejs.find_available_runtime() -> Runtime                    # first available
exejs.find_all_runtime_name_list(is_available: bool = True) -> list[str]
```

### Exception hierarchy

```
ExejsError
├── ExejsRuntimeNameError          # unknown runtime name passed to reset_runtime
├── ExejsRuntimeUnavailableError   # no runtime found / runtime not on PATH
├── ExejsProcessExitError          # subprocess failed / non-zero exit
├── ExejsProgramError              # JS crashed or returned invalid JSON
└── ExejsTimeoutError              # timeout exceeded
```

## Advanced

### Compile & call (context reuse)

Reuse a single JS context across multiple calls instead of re-launching a runtime each time:

```python
import exejs

ctx = exejs.compile('function add(x, y) { return x + y; }')
ctx.call('add', 1, 2)  # 3
ctx.call('add', 10, 20)  # 30
```

### Structured arguments

`call()` auto JSON-serializes arguments and supports property paths as the key:

```python
# call an object method (key may be a property path)
ctx = exejs.compile('var calc = { mul: function(a, b) { return a * b; } };')
ctx.call('calc.mul', 3, 4)  # 12

# call with a dict argument (auto JSON-serialized)
ctx = exejs.compile('function greet(u) { return "hi " + u.name + ", age " + u.age; }')
ctx.call('greet', {'name': 'Tom', 'age': 18})  # 'hi Tom, age 18'
```

### Async API

Async is useful inside async web frameworks (FastAPI, aiohttp) or when you want to avoid blocking the event loop:

```python
import asyncio
import exejs

asyncio.run(exejs.evaluate_async("'red yellow blue'.split(' ')"))
```

### Timeout

`timeout` (seconds) applies to both sync and async variants. On expiry the subprocess is killed and `ExejsTimeoutError` is raised:

```python
try:
    exejs.execute('while (true) {}', timeout=2.0)
except exejs.ExejsTimeoutError as e:
    print('killed:', e)
```

### Choosing a runtime

```python
import exejs

# see what's available on this machine
print(exejs.find_all_runtime_name_list())  # e.g. ['Node', 'JScript']

# force a specific one
exejs.reset_runtime('Node')
print(exejs.get_current_runtime_name())  # 'Node'
```

### Working directory

`compile(source, cwd=...)` sets the subprocess working directory, useful when your JS reads relative files:

```python
ctx = exejs.compile('return require("./config.json")', cwd='/path/to/project')
ctx.evaluate('')
```

## FAQ

- **`ExejsRuntimeUnavailableError: Unable to find available javascript runtime`** — No JS runtime is installed or none is on `PATH`. Install Node.js from [nodejs.org](https://nodejs.org/en/download) and reopen your terminal, or call `exejs.reset_runtime('JScript')` on Windows where `cscript` is built in.
- **Antivirus blocks execution** — If you are using the `JScript` runtime (Windows), it still writes a temp file which may trigger antivirus. Switch to Node (`exejs.reset_runtime('Node')`) to avoid this. All other runtimes use stdin and should not be affected.
- **`cscript` not recognized on Windows** — JScript is provided by Windows Script Host. Ensure `cscript.exe` exists (usually at `C:\Windows\System32\`) and is on `PATH`; on stripped-down Windows images you may need to enable the Windows Script Host feature.
- **Blocks the event loop in asyncio code** — The sync `evaluate` / `execute` block the calling thread. Inside an async framework use `evaluate_async` / `execute_async` instead so the event loop stays responsive.

## Changelog

See [change_log.md](change_log.md).

## Contributing

Pull requests are welcome. To set up a dev environment:

```sh
git clone https://github.com/UlionTse/exejs.git
cd exejs
pip install -e .
pip install pytest
pytest exejs/tests
```

Run `pytest exejs/tests` before submitting a PR. Code style follows PEP 8. Please open an issue first to discuss any non-trivial change.

## Acknowledgements

- [PyExecJS](https://github.com/doloopwhile/PyExecJS) — the original project ExeJS succeeds.
- [JSON-js (json2.js)](https://github.com/douglascrockford/JSON-js) — embedded for legacy runtimes without native `JSON`.

## Notable Usage

ExeJS is a core dependency of [Translators](https://github.com/UlionTse/translators), where it handles the JavaScript execution layer that translation engines rely on.

## License

[Apache-2.0](LICENSE) © UlionTse
