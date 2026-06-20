# coding=utf-8
# author=uliontse

import asyncio
import os
import tempfile
import unittest

import exejs
from exejs.config import (
    ExejsError,
    ExejsProgramError,
    ExejsProcessExitError,
    ExejsRuntimeNameError,
    ExejsTimeoutError,
)
from exejs.runtimes import Exejs, RuntimeCompileContext, _temp_source_file


def _has_runtime():
    try:
        exejs.get_current_runtime_name()
        return True
    except Exception:
        return False


class ImportAndMetadataTests(unittest.TestCase):
    """Tests that must not require a JS runtime."""

    def test_import_exposes_version_and_author(self):
        self.assertTrue(exejs.__version__)
        self.assertTrue(exejs.__author__)

    def test_all_listed_names_are_exported(self):
        for name in exejs.__all__:
            self.assertTrue(hasattr(exejs, name), name)

    def test_module_level_callables_bound(self):
        for name in ('compile', 'execute', 'evaluate',
                     'execute_async', 'evaluate_async', 'reset_runtime',
                     'get_current_runtime', 'get_current_runtime_name',
                     'find_all_runtime_name_list'):
            self.assertTrue(callable(getattr(exejs, name)), name)

    def test_exception_hierarchy_exported(self):
        for name in ('ExejsError', 'ExejsProgramError', 'ExejsProcessExitError',
                     'ExejsRuntimeNameError', 'ExejsTimeoutError'):
            self.assertTrue(hasattr(exejs, name), name)

    def test_exejs_timeout_error_is_exejs_error(self):
        self.assertTrue(issubclass(ExejsTimeoutError, ExejsError))

    def test_lazy_init_does_not_probe_on_construction(self):
        # Constructing the engine must NOT trigger runtime detection.
        engine = Exejs()
        self.assertIsNone(engine._current_runtime)

    def test_reset_runtime_rejects_unknown_name(self):
        engine = Exejs()
        with self.assertRaises(ExejsRuntimeNameError):
            engine.reset_runtime('NotARealRuntime')

    def test_reset_runtime_to_known_name_succeeds(self):
        engine = Exejs()
        engine.reset_runtime('Node')
        self.assertEqual(engine.get_current_runtime_name(), 'Node')

    def test_runtime_map_contains_expected_names(self):
        engine = Exejs()
        for name in ('Node', 'NodeJS', 'JavaScriptCore', 'SpiderMonkey',
                     'JScript', 'Phantomjs', 'SlimerJS', 'Nashorn'):
            self.assertIn(name, engine.runtime_map)

    def test_runtime_cache_returns_same_instance(self):
        engine = Exejs()
        r1 = engine._get_or_create_runtime('Node')
        r2 = engine._get_or_create_runtime('Node')
        self.assertIs(r1, r2)

    def test_temp_source_file_removed_on_normal_exit(self):
        with _temp_source_file('var x = 1;') as path:
            self.assertTrue(os.path.exists(path))
        self.assertFalse(os.path.exists(path))

    def test_temp_source_file_removed_on_exception(self):
        # The temp file must be cleaned up even when an exception propagates
        # out of the `with` block (regression guard for the CM cleanup).
        captured = {}
        with self.assertRaises(RuntimeError):
            with _temp_source_file('var x = 1;') as path:
                captured['path'] = path
                self.assertTrue(os.path.exists(path))
                raise RuntimeError('boom')
        self.assertFalse(os.path.exists(captured['path']))


@unittest.skipUnless(_has_runtime(), 'No JavaScript runtime available')
class RuntimeExecutionTests(unittest.TestCase):
    """Tests that need a real JS runtime (e.g. Node)."""

    # --- runtime management -------------------------------------------------

    def test_find_all_runtime_name_list_returns_available(self):
        names = exejs.find_all_runtime_name_list(is_available=True)
        self.assertIsInstance(names, list)
        self.assertTrue(names, 'expected at least one available runtime')

    def test_find_all_runtimes_with_unavailable_flag(self):
        all_names = exejs.find_all_runtime_name_list(is_available=False)
        # runtime_map has 8 entries
        self.assertGreaterEqual(len(all_names), 8)

    def test_get_current_runtime_name_is_string(self):
        self.assertIsInstance(exejs.get_current_runtime_name(), str)

    # --- evaluate -----------------------------------------------------------

    def test_evaluate_array(self):
        result = exejs.evaluate("'red yellow blue'.split(' ')")
        self.assertEqual(result, ['red', 'yellow', 'blue'])

    def test_evaluate_number(self):
        self.assertEqual(exejs.evaluate('1 + 2'), 3)

    def test_evaluate_empty_source(self):
        self.assertIsNone(exejs.evaluate('   '))

    def test_evaluate_string_with_quotes(self):
        self.assertEqual(exejs.evaluate("'he said \"hi\"'"), 'he said "hi"')

    def test_evaluate_unicode_literal(self):
        self.assertEqual(exejs.evaluate("'你好' + '世界'"), '你好世界')

    def test_evaluate_float(self):
        self.assertAlmostEqual(exejs.evaluate('1.5 + 2.5'), 4.0)

    def test_evaluate_boolean(self):
        self.assertIs(exejs.evaluate('1 < 2'), True)
        self.assertIs(exejs.evaluate('1 > 2'), False)

    def test_evaluate_object(self):
        self.assertEqual(exejs.evaluate('({a: 1, b: "x"})'), {'a': 1, 'b': 'x'})

    # --- execute ------------------------------------------------------------

    def test_execute_returns_explicit_value(self):
        # `execute` wraps source in an IIFE; a value comes back only via `return`.
        self.assertEqual(exejs.execute('var x = 40 + 2; return x;'), 42)

    def test_execute_without_return_yields_none(self):
        self.assertIsNone(exejs.execute('var x = 40 + 2; x;'))

    def test_execute_multi_statement(self):
        self.assertEqual(
            exejs.execute('var a = 10; var b = 20; return a + b;'),
            30,
        )

    def test_execute_multiple_prints_last_line_wins(self):
        # _extract takes the last JSON line; intermediate console.log is harmless.
        result = exejs.execute('console.log("noise"); return 7;')
        self.assertEqual(result, 7)

    def test_execute_returns_none_for_undefined(self):
        self.assertIsNone(exejs.execute('return undefined;'))

    def test_execute_returns_nested_structure(self):
        result = exejs.execute('return {list: [1, 2, {k: "v"}]};')
        self.assertEqual(result, {'list': [1, 2, {'k': 'v'}]})

    # --- compile + call -----------------------------------------------------

    def test_compile_then_call(self):
        ctx = exejs.compile('function add(x, y) { return x + y; }')
        self.assertIsInstance(ctx, RuntimeCompileContext)
        self.assertEqual(ctx.call('add', 1, 2), 3)
        self.assertEqual(ctx.call('add', 10, 5), 15)

    def test_call_with_no_args(self):
        ctx = exejs.compile('function answer() { return 42; }')
        self.assertEqual(ctx.call('answer'), 42)

    def test_call_object_method(self):
        ctx = exejs.compile('var calc = { mul: function(a, b) { return a * b; } };')
        self.assertEqual(ctx.call('calc.mul', 3, 4), 12)

    def test_call_with_dict_arg(self):
        ctx = exejs.compile('function greet(u) { return "hi " + u.name + ", age " + u.age; }')
        self.assertEqual(ctx.call('greet', {'name': 'Tom', 'age': 18}), 'hi Tom, age 18')

    def test_call_with_list_arg(self):
        ctx = exejs.compile('function sum(arr) { return arr.reduce(function(a,b){return a+b}, 0); }')
        self.assertEqual(ctx.call('sum', [1, 2, 3, 4]), 10)

    def test_call_returns_string(self):
        ctx = exejs.compile('function who() { return "exejs"; }')
        self.assertEqual(ctx.call('who'), 'exejs')

    def test_call_returns_bool(self):
        ctx = exejs.compile('function isEven(n) { return n % 2 === 0; }')
        self.assertIs(ctx.call('isEven', 4), True)
        self.assertIs(ctx.call('isEven', 5), False)

    def test_call_returns_none_for_undefined(self):
        ctx = exejs.compile('function maybe() { return; }')
        self.assertIsNone(ctx.call('maybe'))

    def test_call_returns_nested_object(self):
        ctx = exejs.compile('function make() { return {a: 1, b: {c: 2}}; }')
        self.assertEqual(ctx.call('make'), {'a': 1, 'b': {'c': 2}})

    def test_call_returns_array(self):
        ctx = exejs.compile('function range(n) { var r=[]; for(var i=0;i<n;i++){r.push(i)} return r; }')
        self.assertEqual(ctx.call('range', 4), [0, 1, 2, 3])

    def test_call_with_unicode_arg_and_return(self):
        ctx = exejs.compile('function echo(s) { return s + "世界"; }')
        self.assertEqual(ctx.call('echo', '你好'), '你好世界')

    def test_call_undefined_function_raises_program_error(self):
        ctx = exejs.compile('function real() { return 1; }')
        with self.assertRaises(ExejsProgramError):
            ctx.call('notDefined')

    def test_call_context_isolation_between_compiles(self):
        # Two independent ctx instances must not share their source.
        ctx1 = exejs.compile('function f() { return "one"; }')
        ctx2 = exejs.compile('function f() { return "two"; }')
        self.assertEqual(ctx1.call('f'), 'one')
        self.assertEqual(ctx2.call('f'), 'two')

    def test_call_reusable_context_multiple_calls(self):
        ctx = exejs.compile('function fib(n) { return n < 2 ? n : fib(n-1) + fib(n-2); }')
        self.assertEqual([ctx.call('fib', i) for i in range(8)],
                         [0, 1, 1, 2, 3, 5, 8, 13])

    def test_compile_prefix_is_prepended(self):
        ctx = exejs.compile('var base = 100;')
        self.assertEqual(ctx.evaluate('base + 1'), 101)

    def test_compile_then_execute_uses_prefix(self):
        ctx = exejs.compile('var base = 100;')
        self.assertEqual(ctx.execute('return base + 1;'), 101)

    def test_compile_with_cwd(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = exejs.compile('', cwd=d)
            # No exception means cwd was accepted by subprocess.
            self.assertEqual(ctx.evaluate('1 + 1'), 2)

    def test_placeholder_literal_in_user_source_not_corrupted(self):
        # User JS containing placeholder syntax must survive verbatim (regression
        # guard for the single-pass substitution fix).
        result = exejs.evaluate("'#{source} #{encoded_source}'")
        self.assertEqual(result, '#{source} #{encoded_source}')

    # --- error paths --------------------------------------------------------

    def test_program_error_on_bad_js(self):
        with self.assertRaises(ExejsProgramError):
            exejs.evaluate('notADefinedVariable_xyz + 1')

    def test_program_error_on_js_throwing(self):
        with self.assertRaises(ExejsProgramError):
            exejs.evaluate('throw new Error("boom")')

    def test_program_error_on_bad_json_output(self):
        # Monkeypatch _execute to return non-JSON; verify _extract raises.
        ctx = exejs.compile('')
        original = RuntimeCompileContext._execute
        RuntimeCompileContext._execute = lambda self, source, timeout=None: 'not json at all'
        try:
            with self.assertRaises(ExejsProgramError):
                ctx.execute('return 1;')
        finally:
            RuntimeCompileContext._execute = original

    def test_program_error_on_empty_output(self):
        ctx = exejs.compile('')
        original = RuntimeCompileContext._execute
        RuntimeCompileContext._execute = lambda self, source, timeout=None: ''
        try:
            with self.assertRaises(ExejsProgramError):
                ctx.execute('return 1;')
        finally:
            RuntimeCompileContext._execute = original

    # --- async --------------------------------------------------------------

    def test_evaluate_async(self):
        self.assertEqual(asyncio.run(exejs.evaluate_async('2 * 21')), 42)

    def test_execute_async(self):
        self.assertEqual(
            asyncio.run(exejs.execute_async('var y = 5 * 5; return y;')), 25
        )

    def test_call_async(self):
        ctx = exejs.compile('function mul(a, b) { return a * b; }')
        self.assertEqual(asyncio.run(ctx.call_async('mul', 6, 7)), 42)

    # --- timeout: sync ------------------------------------------------------

    def test_execute_timeout_kills_infinite_loop(self):
        with self.assertRaises(ExejsTimeoutError):
            exejs.execute('while (true) {}', timeout=1.0)

    def test_execute_timeout_none_default_no_raise(self):
        # Default None must not change existing behavior.
        self.assertEqual(exejs.evaluate('1 + 1', timeout=None), 2)

    def test_evaluate_timeout(self):
        with self.assertRaises(ExejsTimeoutError):
            exejs.evaluate('(function(){ while(true){} })()', timeout=1.0)

    def test_call_with_timeout(self):
        ctx = exejs.compile('function loop() { while (true) {} }')
        with self.assertRaises(ExejsTimeoutError):
            ctx.call('loop', timeout=1.0)

    def test_call_with_timeout_success_path(self):
        # A generous timeout must not interfere with a normal call.
        ctx = exejs.compile('function add(x, y) { return x + y; }')
        self.assertEqual(ctx.call('add', 1, 2, timeout=10.0), 3)

    def test_timeout_message_contains_runtime_name_and_seconds(self):
        try:
            exejs.execute('while (true) {}', timeout=0.5)
        except ExejsTimeoutError as e:
            msg = str(e)
            self.assertIn('timed out', msg)
            self.assertIn('0.5', msg)
        else:
            self.fail('expected ExejsTimeoutError')

    def test_timeout_does_not_leave_orphan_process(self):
        # After a timeout the subprocess must be killed; the runtime must still
        # be usable for subsequent calls.
        try:
            exejs.execute('while (true) {}', timeout=0.5)
        except ExejsTimeoutError:
            pass
        self.assertEqual(exejs.evaluate('2 + 2'), 4)

    # --- timeout: async -----------------------------------------------------

    def test_execute_async_timeout(self):
        async def run():
            return await exejs.execute_async('while (true) {}', timeout=1.0)
        with self.assertRaises(ExejsTimeoutError):
            asyncio.run(run())

    def test_evaluate_async_timeout(self):
        async def run():
            return await exejs.evaluate_async('(function(){ while(true){} })()', timeout=1.0)
        with self.assertRaises(ExejsTimeoutError):
            asyncio.run(run())

    def test_call_async_with_timeout(self):
        ctx = exejs.compile('function loop() { while (true) {} }')
        async def run():
            return await ctx.call_async('loop', timeout=1.0)
        with self.assertRaises(ExejsTimeoutError):
            asyncio.run(run())

    def test_call_async_with_timeout_success_path(self):
        ctx = exejs.compile('function add(x, y) { return x + y; }')
        async def run():
            return await ctx.call_async('add', 1, 2, timeout=10.0)
        self.assertEqual(asyncio.run(run()), 3)


if __name__ == '__main__':
    unittest.main()
