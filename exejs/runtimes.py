# coding=utf-8
# author=uliontse

import asyncio
import json
import os
import platform
import re
import stat
import subprocess
import tempfile

from exejs.config import ExejsProgramError, ExejsProcessExitError
from exejs.config import ExejsRuntimeNameError, ExejsRuntimeUnavailableError
from exejs.config import JScript_Source, PhantomJS_Source, Nashorn_Source, SlimerJS_Source
from exejs.config import Json2_Source, Node_Source, JavaScriptCore_Source, SpiderMonkey_Source


class Runtime:
    def __init__(self, name, command, run_source):
        self.name = name
        self.command = [command] if isinstance(command, str) else list(command)
        self.run_source = run_source
        self.cmd_app = self.get_cmd_app()

    def get_cmd_app(self):
        name, args = self.command[0], self.command[1:]
        pathext_list = os.environ.get('PATHEXT', '').split(os.pathsep) if platform.system() == 'Windows' else ['']
        path_list = os.environ.get('PATH', '').split(os.pathsep)
        for _dir in path_list:
            for ext in pathext_list:
                filename = os.path.join(_dir, name + ext)
                try:
                    st = os.stat(filename)
                except (os.error, OSError):
                    continue
                if stat.S_ISREG(st.st_mode) and (stat.S_IMODE(st.st_mode) & 0o111):
                    return [filename] + args
        return

    def is_available(self):
        return True if self.cmd_app else False

    def compile(self, source, cwd=None):
        if not self.is_available():
            raise ExejsRuntimeUnavailableError
        return RuntimeCompileContext(self, source, cwd)


class RuntimeCompileContext:
    def __init__(self, runtime, source='', cwd=None):
        self.runtime = runtime
        self.source = source
        self.cwd = cwd

    def encode_unicode_codepoints(self, text):
        """not ascii to encode unicode characters"""
        return re.sub(pattern='[^\x00-\x7f]', repl=lambda x: '\\u{0:04x}'.format(ord(x.group(0))), string=text)

    def _compile(self, source):
        encode_source = json.dumps('(function(){{ {} }})()'.format(self.encode_unicode_codepoints(source)))
        repl = {
            '#{source}': lambda: source,
            '#{json2_source}': lambda: Json2_Source,
            '#{encoded_source}': lambda: encode_source,
        }
        pattern = "|".join(re.escape(k) for k in repl)
        run_source = re.sub(pattern=pattern, repl=lambda x: repl[x.group(0)](), string=self.runtime.run_source)
        return run_source

    def _execute(self, source):
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        try:
            data = subprocess.check_output(cmd, input=src, cwd=self.cwd, text=True, encoding='utf-8')
        except Exception as e:
            raise ExejsProcessExitError(str(e))
        return data

    async def _execute_async(self, source):
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        try:
            # Create the subprocess asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            # Communicate with the process (send input, get output)
            stdout, stderr = await process.communicate(input=src.encode('utf-8'))

            if process.returncode != 0:
                raise ExejsProcessExitError(stderr.decode('utf-8'))
            data = stdout.decode('utf-8')
        except Exception as e:
            raise ExejsProcessExitError(str(e))
        return data

    def _execute_with_tempfile(self, source):
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        fd, t_file = tempfile.mkstemp(prefix='exejs_temp_', suffix='.js', text=False)
        os.close(fd)
        try:
            with open(t_file, 'w+', encoding='utf-8') as f:
                f.write(src)

            new_cmd = cmd + [t_file]
            data = subprocess.check_output(new_cmd, cwd=self.cwd, text=True, encoding='utf-8')
        except Exception as e:
            raise ExejsProcessExitError(str(e))
        finally:
            os.remove(t_file)
        return data

    async def _execute_with_tempfile_async(self, source):
        src = self._compile(source)
        cmd = self.runtime.cmd_app
        fd, t_file = tempfile.mkstemp(prefix='exejs_temp_', suffix='.js', text=False)
        os.close(fd)
        try:
            # File writing remains sync (usually fast enough), execution is async
            with open(t_file, 'w+', encoding='utf-8') as f:
                f.write(src)

            new_cmd = cmd + [t_file]

            process = await asyncio.create_subprocess_exec(
                *new_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise ExejsProcessExitError(stderr.decode('utf-8'))
            data = stdout.decode('utf-8')

        except Exception as e:
            raise ExejsProcessExitError(str(e))
        finally:
            if os.path.exists(t_file):
                os.remove(t_file)
        return data

    def _extract(self, outputs):
        outputs = outputs.replace('\r\n', '\n').replace('\r', '\n')
        outputs_last_line = outputs.split('\n')[-2]
        data = json.loads(outputs_last_line)

        if len(data) == 1:
            data = data[0], None

        status, value = data
        if status != 'ok':
            raise ExejsProgramError
        return value

    def execute(self, source):
        source = '{}\n{}'.format(self.source, source) if self.source else source
        outputs = self._execute_with_tempfile(source) if self.runtime.name == 'JScript' else self._execute(source)
        outputs = self._extract(outputs)
        return outputs

    def evaluate(self, source):
        data = "'('+" + json.dumps(source, ensure_ascii=True) + "+')'" if source.strip() else "''"
        code = 'return eval({})'.format(data)
        outputs = self.execute(code)
        return outputs

    def call(self, key, *args):
        args = json.dumps(args)
        return self.evaluate('{key}.apply(this, {args})'.format(key=key, args=args))

    async def execute_async(self, source):
        source = '{}\n{}'.format(self.source, source) if self.source else source
        if self.runtime.name == 'JScript':
            outputs = await self._execute_with_tempfile_async(source)
        else:
            outputs = await self._execute_async(source)
        outputs = self._extract(outputs)
        return outputs

    async def evaluate_async(self, source):
        data = "'('+" + json.dumps(source, ensure_ascii=True) + "+')'" if source.strip() else "''"
        code = 'return eval({})'.format(data)
        outputs = await self.execute_async(code)
        return outputs

    async def call_async(self, key, *args):
        args = json.dumps(args)
        return await self.evaluate_async('{key}.apply(this, {args})'.format(key=key, args=args))


class Tse:
    def __init__(self):
        self.jsc_cmd = ['/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc']
        self.runtime_map = {
            'Node': {'command': ['node'], 'run_source': Node_Source},
            'NodeJS': {'command': ['nodejs'], 'run_source': Node_Source},
            'JavaScriptCore': {'command': self.jsc_cmd, 'run_source': JavaScriptCore_Source},
            'SpiderMonkey': {'command': ['js'], 'run_source': SpiderMonkey_Source},
            'Phantomjs': {'command': ['phantomjs'], 'run_source': PhantomJS_Source},
            'SlimerJS': {'command': ['slimerjs'], 'run_source': SlimerJS_Source},
            'Nashorn': {'command': ['jjs'], 'run_source': Nashorn_Source},
            'JScript': {'command': ['cscript', '//E:jscript', '//Nologo'], 'run_source': JScript_Source},
        }
        self.current_runtime = self.find_available_runtime()

    def get_current_runtime(self):
        return self.current_runtime

    def get_current_runtime_name(self):
        return self.current_runtime.name

    def find_available_runtime(self):
        runtime = None
        for name, engine_map in self.runtime_map.items():
            runtime = Runtime(name, engine_map['command'], engine_map['run_source'])
            if runtime.is_available():
                return runtime

        if runtime is None:
            error_message = 'Unable to find available javascript runtime.'
            error_message += ' Maybe you can download and install node.js from https://nodejs.org/en/download/'
            raise ExejsRuntimeUnavailableError(error_message)
        return runtime

    def find_all_runtime_name_list(self, is_available=True):
        runtime_name_list = []
        for name, engine_map in self.runtime_map.items():
            runtime = Runtime(name, engine_map['command'], engine_map['run_source'])
            if is_available:
                if runtime.is_available():
                    runtime_name_list.append(name)
            else:
                runtime_name_list.append(name)
        return runtime_name_list

    def reset_runtime(self, name):
        if name not in self.runtime_map.keys():
            raise ExejsRuntimeNameError

        engine_map = self.runtime_map[name]
        self.current_runtime = Runtime(name, engine_map['command'], engine_map['run_source'])
        return

    def compile(self, source='', cwd=None):
        return self.current_runtime.compile(source, cwd)

    def execute(self, source):
        return self.compile().execute(source)

    def evaluate(self, source):
        return self.compile().evaluate(source)

    async def execute_async(self, source):
        return await self.compile().execute_async(source)

    async def evaluate_async(self, source):
        return await self.compile().evaluate_async(source)

tse = Tse()
compile = tse.compile
execute = tse.execute
evaluate = tse.evaluate
execute_async = tse.execute_async
evaluate_async = tse.evaluate_async
reset_runtime = tse.reset_runtime
find_all_runtime_name_list = tse.find_all_runtime_name_list
get_current_runtime = tse.get_current_runtime
get_current_runtime_name = tse.get_current_runtime_name
