# coding=utf-8
# author=uliontse

import os
import re
import stat
import json
import platform
import subprocess

from exejs.config import Json2_Source, Node_Source, JavaScriptCore_Source, SpiderMonkey_Source
from exejs.config import JScript_Source, PhantomJS_Source, Nashorn_Source, SlimerJS_Source
from exejs.config import ExejsProgramError, ExejsProcessExitError, ExejsRuntimeUnavailableError


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
                    return filename
        return ''

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
            data = subprocess.check_output(cmd, input=src, cwd=self.cwd, text=True)
        except Exception as e:
            raise ExejsProcessExitError(str(e))
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
        outputs = self._execute(source)
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


class Tse:
    def __init__(self):
        self.runtime_list = [
            Runtime(
                name='Node.js (V8)',
                command=['node'],
                run_source=Node_Source,
            ),
            Runtime(
                name='Node.js (V8)',
                command=['nodejs'],
                run_source=Node_Source,
            ),
            Runtime(
                name='JavaScriptCore',
                command=['/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc'],
                run_source=JavaScriptCore_Source,
            ),
            Runtime(
                name='SpiderMonkey',
                command=['js'],
                run_source=SpiderMonkey_Source,
            ),
            Runtime(
                name='JScript',
                command=['cscript', '//E:jscript', '//Nologo'],
                run_source=JScript_Source,
            ),
            Runtime(
                name='PhantomJS',
                command=['phantomjs'],
                run_source=PhantomJS_Source,
            ),
            Runtime(
                name='SlimerJS',
                command=['slimerjs'],
                run_source=SlimerJS_Source,
            ),
            Runtime(
                name='Nashorn',
                command=['jjs'],
                run_source=Nashorn_Source,
            ),
        ]
        self.current_runtime = self.find_available_runtime()

    def find_available_runtime(self):
        runtime = None
        for _runtime in self.runtime_list:
            if _runtime.is_available():
                runtime = _runtime
                break

        if not runtime:
            error_message = 'Unable to find available javascript runtime.'
            error_message += ' Maybe you can download and install node.js from https://nodejs.org/en/download/'
            raise ExejsRuntimeUnavailableError(error_message)
        return runtime

    def compile(self, source='', cwd=None):
        return self.current_runtime.compile(source, cwd)

    def execute(self, source):
        return self.compile().execute(source)

    def evaluate(self, source):
        return self.compile().evaluate(source)


tse = Tse()
compile = tse.compile
execute = tse.execute
evaluate = tse.evaluate
runtime = tse.current_runtime
