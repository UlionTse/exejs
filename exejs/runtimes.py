# coding=utf-8
# author=uliontse

import os
import re
import stat
import json
import shutil
import asyncio
import platform
import tempfile
import contextlib
import subprocess
from typing import Any, Dict, List, Optional, TypedDict, Union

from exejs.config import ExejsProgramError, ExejsProcessExitError, ExejsTimeoutError
from exejs.config import ExejsRuntimeNameError, ExejsRuntimeUnavailableError
from exejs.config import JScript_Source, PhantomJS_Source, Nashorn_Source, SlimerJS_Source
from exejs.config import Json2_Source, Node_Source, JavaScriptCore_Source, SpiderMonkey_Source


@contextlib.contextmanager
def _temp_source_file(src: str):
    """Write compiled JS to a temp file, yield its path, and remove it on exit."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', prefix='exejs_temp_', encoding='utf-8', delete=False) as f:
        f.write(src)
        t_file = f.name
    try:
        yield t_file
    finally:
        if os.path.exists(t_file):
            os.remove(t_file)


class Runtime:
    def __init__(self, name: str, command: Union[str, List[str]], run_source: str):
        self.name = name
        self.command = [command] if isinstance(command, str) else list(command)
        self.run_source = run_source.replace('#{json2_source}', Json2_Source)
        self.cmd_app = self._resolve_cmd_app()

    def _resolve_cmd_app(self) -> Optional[List[str]]:
        name, args = self.command[0], self.command[1:]
        if os.path.isabs(name):
            if os.path.isfile(name) and self._is_executable(name):
                return [name] + args
            return None
        resolved = shutil.which(name)
        return [resolved] + args if resolved else None

    @staticmethod
    def _is_executable(path: str) -> bool:
        st = os.stat(path)
        if platform.system() == 'Windows':
            return stat.S_ISREG(st.st_mode)
        return stat.S_ISREG(st.st_mode) and (stat.S_IMODE(st.st_mode) & 0o111)

    def is_available(self) -> bool:
        return self.cmd_app is not None

    def compile(self, source: str = '', cwd: Optional[str] = None) -> 'RuntimeCompileContext':  # forward ref: defined below
        if not self.is_available():
            raise ExejsRuntimeUnavailableError(
                'Runtime {!r} is not available. Install it or call reset_runtime to switch.'.format(self.name)
            )
        return RuntimeCompileContext(self, source, cwd)


class RuntimeCompileContext:
    _PLACEHOLDER_RE = re.compile(r'#\{(\w+)\}')  # block cache

    def __init__(self, runtime: Runtime, source: str = '', cwd: Optional[str] = None):
        self.runtime = runtime
        self.source = source
        self.cwd = cwd

    def _compile(self, source: str) -> str:
        encoded_source = json.dumps('(function(){{ {} }})()'.format(source))
        mapping = {
            'source': source,
            'encoded_source': encoded_source,
        }
        return self._PLACEHOLDER_RE.sub(lambda m: mapping.get(m.group(1), m.group(0)), self.runtime.run_source)

    def _execute(self, source: str, timeout: Optional[float] = None) -> str:
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        try:
            process = subprocess.run(
                cmd,
                input=src, cwd=self.cwd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8',
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            # direct cause of timeout error
            raise ExejsTimeoutError('Runtime {!r} timed out after {}s.'.format(self.runtime.name, timeout)) from e
        except Exception as e:
            raise ExejsProcessExitError(str(e))
        if process.returncode != 0:
            raise ExejsProcessExitError(process.stderr)
        return process.stdout

    async def _execute_async(self, source: str, timeout: Optional[float] = None) -> str:
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            raise ExejsProcessExitError(str(e))
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=src.encode('utf-8')),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
            raise ExejsTimeoutError(
                'Runtime {!r} timed out after {}s.'.format(self.runtime.name, timeout)
            )
        if process.returncode != 0:
            raise ExejsProcessExitError(stderr.decode('utf-8'))
        return stdout.decode('utf-8')

    def _execute_with_tempfile(self, source: str, timeout: Optional[float] = None) -> str:
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        with _temp_source_file(src) as t_file:
            new_cmd = cmd + [t_file]
            try:
                proc = subprocess.run(
                    new_cmd,
                    cwd=self.cwd,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8',
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as e:
                raise ExejsTimeoutError(
                    'Runtime {!r} timed out after {}s.'.format(self.runtime.name, timeout)
                ) from e
            except Exception as e:
                raise ExejsProcessExitError(str(e))
        if proc.returncode != 0:
            raise ExejsProcessExitError(proc.stderr)
        return proc.stdout

    async def _execute_with_tempfile_async(self, source: str, timeout: Optional[float] = None) -> str:
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        with _temp_source_file(src) as t_file:
            new_cmd = cmd + [t_file]
            try:
                process = await asyncio.create_subprocess_exec(
                    *new_cmd,
                    cwd=self.cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except Exception as e:
                raise ExejsProcessExitError(str(e))
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
                raise ExejsTimeoutError('Runtime {!r} timed out after {}s.'.format(self.runtime.name, timeout))
            if process.returncode != 0:
                raise ExejsProcessExitError(stderr.decode('utf-8'))
            return stdout.decode('utf-8')

    def _extract(self, outputs: str) -> Any:
        outputs = outputs.replace('\r\n', '\n').replace('\r', '\n')
        lines = [ln for ln in outputs.split('\n') if ln.strip()]
        if not lines:
            raise ExejsProgramError('Empty output from runtime. JS code may have crashed before printing.')
        try:
            data = json.loads(lines[-1])
        except json.JSONDecodeError as e:
            raise ExejsProgramError('Failed to parse runtime output as JSON: {}. Last line: {!r}'.format(e, lines[-1]))
        if len(data) == 1:
            data = [data[0], None]
        status, value = data
        if status != 'ok':
            raise ExejsProgramError(
                'Extract failed. Javascript code may contain undefined variables or functions. '
                'Runtime message: {!r}'.format(value)
            )
        return value

    def execute(self, source: str, timeout: Optional[float] = None) -> Any:
        source = '{}\n{}'.format(self.source, source) if self.source else source
        if self.runtime.name == 'JScript':
            outputs = self._execute_with_tempfile(source, timeout=timeout)
        else:
            outputs = self._execute(source, timeout=timeout)
        return self._extract(outputs)

    def evaluate(self, source: str, timeout: Optional[float] = None) -> Any:
        expr = json.dumps('({})'.format(source), ensure_ascii=True) if source.strip() else '""'
        code = 'return eval({})'.format(expr)
        return self.execute(code, timeout=timeout)

    def call(self, key: str, *args: Any, timeout: Optional[float] = None) -> Any:
        args_json = json.dumps(args)
        return self.evaluate('{key}.apply(this, {args})'.format(key=key, args=args_json), timeout=timeout)

    async def execute_async(self, source: str, timeout: Optional[float] = None) -> Any:
        source = '{}\n{}'.format(self.source, source) if self.source else source
        if self.runtime.name == 'JScript':
            outputs = await self._execute_with_tempfile_async(source, timeout=timeout)
        else:
            outputs = await self._execute_async(source, timeout=timeout)
        return self._extract(outputs)

    async def evaluate_async(self, source: str, timeout: Optional[float] = None) -> Any:
        expr = json.dumps('({})'.format(source), ensure_ascii=True) if source.strip() else '""'
        code = 'return eval({})'.format(expr)
        return await self.execute_async(code, timeout=timeout)

    async def call_async(self, key: str, *args: Any, timeout: Optional[float] = None) -> Any:
        args_json = json.dumps(args)
        return await self.evaluate_async('{key}.apply(this, {args})'.format(key=key, args=args_json), timeout=timeout)


class _RuntimeSpec(TypedDict):
    command: List[str]
    run_source: str


class Exejs:
    def __init__(self):
        jsc_path = shutil.which('jsc') or '/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc'
        self.runtime_map: Dict[str, _RuntimeSpec] = {
            'Node': {'command': ['node'], 'run_source': Node_Source},
            'NodeJS': {'command': ['nodejs'], 'run_source': Node_Source},
            'JavaScriptCore': {'command': [jsc_path], 'run_source': JavaScriptCore_Source},
            'SpiderMonkey': {'command': ['js'], 'run_source': SpiderMonkey_Source},
            'Phantomjs': {'command': ['phantomjs'], 'run_source': PhantomJS_Source},
            'SlimerJS': {'command': ['slimerjs'], 'run_source': SlimerJS_Source},
            'Nashorn': {'command': ['jjs'], 'run_source': Nashorn_Source},
            'JScript': {'command': ['cscript', '//E:jscript', '//Nologo'], 'run_source': JScript_Source},
        }
        self._runtime_cache: Dict[str, Runtime] = {}
        self._current_runtime: Optional[Runtime] = None

    def _get_or_create_runtime(self, name: str) -> Runtime:
        if name not in self._runtime_cache:
            spec = self.runtime_map[name]
            self._runtime_cache[name] = Runtime(name, spec['command'], spec['run_source'])
        return self._runtime_cache[name]

    @property
    def current_runtime(self) -> Runtime:
        if self._current_runtime is None:
            self._current_runtime = self.find_available_runtime()
        return self._current_runtime

    def get_current_runtime(self) -> Runtime:
        return self.current_runtime

    def get_current_runtime_name(self) -> str:
        return self.current_runtime.name

    def find_available_runtime(self) -> Runtime:
        for name in self.runtime_map:
            runtime = self._get_or_create_runtime(name)
            if runtime.is_available():
                return runtime
        raise ExejsRuntimeUnavailableError(
            'Unable to find available javascript runtime. '
            'Maybe you can download and install node.js from https://nodejs.org/en/download/'
        )

    def find_all_runtime_name_list(self, is_available: bool = True) -> List[str]:
        runtime_name_list: List[str] = []
        for name in self.runtime_map:
            runtime = self._get_or_create_runtime(name)
            if not is_available or runtime.is_available():
                runtime_name_list.append(name)
        return runtime_name_list

    def reset_runtime(self, name: str) -> None:
        if name not in self.runtime_map:
            raise ExejsRuntimeNameError("Invalid runtime name {!r}. Available: {}".format(name, list(self.runtime_map)))
        self._current_runtime = self._get_or_create_runtime(name)

    def compile(self, source: str = '', cwd: Optional[str] = None) -> RuntimeCompileContext:
        return self.current_runtime.compile(source, cwd)

    def execute(self, source: str, timeout: Optional[float] = None) -> Any:
        return self.compile().execute(source, timeout=timeout)

    def evaluate(self, source: str, timeout: Optional[float] = None) -> Any:
        return self.compile().evaluate(source, timeout=timeout)

    async def execute_async(self, source: str, timeout: Optional[float] = None) -> Any:
        return await self.compile().execute_async(source, timeout=timeout)

    async def evaluate_async(self, source: str, timeout: Optional[float] = None) -> Any:
        return await self.compile().evaluate_async(source, timeout=timeout)


exe = Exejs()
compile = exe.compile
execute = exe.execute
evaluate = exe.evaluate
execute_async = exe.execute_async
evaluate_async = exe.evaluate_async
reset_runtime = exe.reset_runtime
get_current_runtime = exe.get_current_runtime
get_current_runtime_name = exe.get_current_runtime_name
find_available_runtime = exe.find_available_runtime
find_all_runtime_name_list = exe.find_all_runtime_name_list
