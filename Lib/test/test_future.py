# Test various flavors of legal and illegal future statements

import __future__
import ast
import unittest
from test import support
from test.support import import_helper
from textwrap import dedent
import os
import re
import sys
import types

rx = re.compile(r'\((\S+).py, line (\d+)')

def get_error_location(msg):
    mo = rx.search(str(msg))
    return mo.group(1, 2)

class FutureTest(unittest.TestCase):

    def check_syntax_error(self, err, basename, lineno, offset=1):
        self.assertIn('%s.py, line %d' % (basename, lineno), str(err))
        self.assertEqual(os.path.basename(err.filename), basename + '.py')
        self.assertEqual(err.lineno, lineno)
        self.assertEqual(err.offset, offset)

    def test_future1(self):
        with import_helper.CleanImport('future_test1'):
            from test import future_test1
            self.assertEqual(future_test1.result, 6)

    def test_future2(self):
        with import_helper.CleanImport('future_test2'):
            from test import future_test2
            self.assertEqual(future_test2.result, 6)

    def test_future3(self):
        with import_helper.CleanImport('test_future3'):
            from test import test_future3

    def test_badfuture3(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future3
        self.check_syntax_error(cm.exception, "badsyntax_future3", 3)

    def test_badfuture4(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future4
        self.check_syntax_error(cm.exception, "badsyntax_future4", 3)

    def test_badfuture5(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future5
        self.check_syntax_error(cm.exception, "badsyntax_future5", 4)

    def test_badfuture6(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future6
        self.check_syntax_error(cm.exception, "badsyntax_future6", 3)

    def test_badfuture7(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future7
        self.check_syntax_error(cm.exception, "badsyntax_future7", 3, 53)

    def test_badfuture8(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future8
        self.check_syntax_error(cm.exception, "badsyntax_future8", 3)

    def test_badfuture9(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future9
        self.check_syntax_error(cm.exception, "badsyntax_future9", 3)

    def test_badfuture10(self):
        with self.assertRaises(SyntaxError) as cm:
            from test import badsyntax_future10
        self.check_syntax_error(cm.exception, "badsyntax_future10", 3)

    def test_ensure_flags_dont_clash(self):
        # bpo-39562: test that future flags and compiler flags doesn't clash

        # obtain future flags (CO_FUTURE_***) from the __future__ module
        flags = {
            f"CO_FUTURE_{future.upper()}": getattr(__future__, future).compiler_flag
            for future in __future__.all_feature_names
        }
        # obtain some of the exported compiler flags (PyCF_***) from the ast module
        flags |= {
            flag: getattr(ast, flag)
            for flag in dir(ast) if flag.startswith("PyCF_")
        }
        self.assertCountEqual(set(flags.values()), flags.values())

    def test_parserhack(self):
        # test that the parser.c::future_hack function works as expected
        # Note: although this test must pass, it's not testing the original
        #       bug as of 2.6 since the with statement is not optional and
        #       the parser hack disabled. If a new keyword is introduced in
        #       2.6, change this to refer to the new future import.
        try:
            exec("from __future__ import print_function; print 0")
        except SyntaxError:
            pass
        else:
            self.fail("syntax error didn't occur")

        try:
            exec("from __future__ import (print_function); print 0")
        except SyntaxError:
            pass
        else:
            self.fail("syntax error didn't occur")

    def test_multiple_features(self):
        with import_helper.CleanImport("test.test_future5"):
            from test import test_future5

    def test_unicode_literals_exec(self):
        scope = {}
        exec("from __future__ import unicode_literals; x = ''", {}, scope)
        self.assertIsInstance(scope["x"], str)

class AnnotationsFutureTestCase(unittest.TestCase):
    template = dedent(
        """
        from __future__ import annotations
        def f() -> {ann}:
            ...
        def g(arg: {ann}) -> None:
            ...
        async def f2() -> {ann}:
            ...
        async def g2(arg: {ann}) -> None:
            ...
        var: {ann}
        var2: {ann} = None
        """
    )

    def getActual(self, annotation):
        scope = {}
        exec(self.template.format(ann=annotation), {}, scope)
        func_ret_ann = scope['f'].__annotations__['return']
        func_arg_ann = scope['g'].__annotations__['arg']
        async_func_ret_ann = scope['f2'].__annotations__['return']
        async_func_arg_ann = scope['g2'].__annotations__['arg']
        var_ann1 = scope['__annotations__']['var']
        var_ann2 = scope['__annotations__']['var2']
        self.assertEqual(func_ret_ann, func_arg_ann)
        self.assertEqual(func_ret_ann, async_func_ret_ann)
        self.assertEqual(func_ret_ann, async_func_arg_ann)
        self.assertEqual(func_ret_ann, var_ann1)
        self.assertEqual(func_ret_ann, var_ann2)
        return func_ret_ann

    def assertAnnotationEqual(
        self, annotation, expected=None, drop_parens=False, is_tuple=False,
    ):
        actual = self.getActual(annotation)
        if expected is None:
            expected = annotation if not is_tuple else annotation[1:-1]
        if drop_parens:
            self.assertNotEqual(actual, expected)
            actual = actual.replace("(", "").replace(")", "")

        self.assertEqual(actual, expected)

    def test_annotations(self):
        eq = self.assertAnnotationEqual
        eq('...')
        eq("'some_string'")
        eq("u'some_string'")
        eq("b'\\xa3'")
        eq('Name')
        eq('None')
        eq('True')
        eq('False')
        eq('1')
        eq('1.0')
        eq('1j')
        eq('True or False')
        eq('True or False or None')
        eq('True and False')
        eq('True and False and None')
        eq('Name1 and Name2 or Name3')
        eq('Name1 and (Name2 or Name3)')
        eq('Name1 or Name2 and Name3')
        eq('(Name1 or Name2) and Name3')
        eq('Name1 and Name2 or Name3 and Name4')
        eq('Name1 or Name2 and Name3 or Name4')
        eq('a + b + (c + d)')
        eq('a * b * (c * d)')
        eq('(a ** b) ** c ** d')
        eq('v1 << 2')
        eq('1 >> v2')
        eq('1 % finished')
        eq('1 + v2 - v3 * 4 ^ 5 ** v6 / 7 // 8')
        eq('not great')
        eq('not not great')
        eq('~great')
        eq('+value')
        eq('++value')
        eq('-1')
        eq('~int and not v1 ^ 123 + v2 | True')
        eq('a + (not b)')
        eq('lambda: None')
        eq('lambda arg: None')
        eq('lambda a=True: a')
        eq('lambda a, b, c=True: a')
        eq("lambda a, b, c=True, *, d=1 << v2, e='str': a")
        eq("lambda a, b, c=True, *vararg, d, e='str', **kwargs: a + b")
        eq("lambda a, /, b, c=True, *vararg, d, e='str', **kwargs: a + b")
        eq('lambda x, /: x')
        eq('lambda x=1, /: x')
        eq('lambda x, /, y: x + y')
        eq('lambda x=1, /, y=2: x + y')
        eq('lambda x, /, y=1: x + y')
        eq('lambda x, /, y=1, *, z=3: x + y + z')
        eq('lambda x=1, /, y=2, *, z=3: x + y + z')
        eq('lambda x=1, /, y=2, *, z: x + y + z')
        eq('lambda x=1, y=2, z=3, /, w=4, *, l, l2: x + y + z + w + l + l2')
        eq('lambda x=1, y=2, z=3, /, w=4, *, l, l2, **kwargs: x + y + z + w + l + l2')
        eq('lambda x, /, y=1, *, z: x + y + z')
        eq('lambda x: lambda y: x + y')
        eq('1 if True else 2')
        eq('str or None if int or True else str or bytes or None')
        eq('str or None if (1 if True else 2) else str or bytes or None')
        eq("0 if not x else 1 if x > 0 else -1")
        eq("(1 if x > 0 else -1) if x else 0")
        eq("{'2.7': dead, '3.7': long_live or die_hard}")
        eq("{'2.7': dead, '3.7': long_live or die_hard, **{'3.6': verygood}}")
        eq("{**a, **b, **c}")
        eq("{'2.7', '3.6', '3.7', '3.8', '3.9', '4.0' if gilectomy else '3.10'}")
        eq("{*a, *b, *c}")
        eq("({'a': 'b'}, True or False, +value, 'string', b'bytes') or None")
        eq("()")
        eq("(a,)")
        eq("(a, b)")
        eq("(a, b, c)")
        eq("(*a, *b, *c)")
        eq("[]")
        eq("[1, 2, 3, 4, 5, 6, 7, 8, 9, 10 or A, 11 or B, 12 or C]")
        eq("[*a, *b, *c]")
        eq("{i for i in (1, 2, 3)}")
        eq("{i ** 2 for i in (1, 2, 3)}")
        eq("{i ** 2 for i, _ in ((1, 'a'), (2, 'b'), (3, 'c'))}")
        eq("{i ** 2 + j for i in (1, 2, 3) for j in (1, 2, 3)}")
        eq("[i for i in (1, 2, 3)]")
        eq("[i ** 2 for i in (1, 2, 3)]")
        eq("[i ** 2 for i, _ in ((1, 'a'), (2, 'b'), (3, 'c'))]")
        eq("[i ** 2 + j for i in (1, 2, 3) for j in (1, 2, 3)]")
        eq("(i for i in (1, 2, 3))")
        eq("(i ** 2 for i in (1, 2, 3))")
        eq("(i ** 2 for i, _ in ((1, 'a'), (2, 'b'), (3, 'c')))")
        eq("(i ** 2 + j for i in (1, 2, 3) for j in (1, 2, 3))")
        eq("{i: 0 for i in (1, 2, 3)}")
        eq("{i: j for i, j in ((1, 'a'), (2, 'b'), (3, 'c'))}")
        eq("[(x, y) for x, y in (a, b)]")
        eq("[(x,) for x, in (a,)]")
        eq("Python3 > Python2 > COBOL")
        eq("Life is Life")
        eq("call()")
        eq("call(arg)")
        eq("call(kwarg='hey')")
        eq("call(arg, kwarg='hey')")
        eq("call(arg, *args, another, kwarg='hey')")
        eq("call(arg, another, kwarg='hey', **kwargs, kwarg2='ho')")
        eq("lukasz.langa.pl")
        eq("call.me(maybe)")
        eq("1 .real")
        eq("1.0.real")
        eq("....__class__")
        eq("list[str]")
        eq("dict[str, int]")
        eq("set[str,]")
        eq("tuple[str, ...]")
        eq("tuple[(str, *types)]")
        eq("tuple[str, int, (str, int)]")
        eq("tuple[(*int, str, str, (str, int))]")
        eq("tuple[str, int, float, dict[str, int]]")
        eq("slice[0]")
        eq("slice[0:1]")
        eq("slice[0:1:2]")
        eq("slice[:]")
        eq("slice[:-1]")
        eq("slice[1:]")
        eq("slice[::-1]")
        eq("slice[:,]")
        eq("slice[1:2,]")
        eq("slice[1:2:3,]")
        eq("slice[1:2, 1]")
        eq("slice[1:2, 2, 3]")
        eq("slice[()]")
        eq("slice[a, b:c, d:e:f]")
        eq("slice[(x for x in a)]")
        eq('str or None if sys.version_info[0] > (3,) else str or bytes or None')
        eq("f'f-string without formatted values is just a string'")
        eq("f'{{NOT a formatted value}}'")
        eq("f'some f-string with {a} {few():.2f} {formatted.values!r}'")
        eq('''f"{f'{nested} inner'} outer"''')
        eq("f'space between opening braces: { {a for a in (1, 2, 3)}}'")
        eq("f'{(lambda x: x)}'")
        eq("f'{(None if a else lambda x: x)}'")
        eq("f'{x}'")
        eq("f'{x!r}'")
        eq("f'{x!a}'")
        eq('(yield from outside_of_generator)')
        eq('(yield)')
        eq('(yield a + b)')
        eq('await some.complicated[0].call(with_args=True or 1 is not 1)')
        eq('[x for x in (a if b else c)]')
        eq('[x for x in a if (b if c else d)]')
        eq('f(x for x in a)')
        eq('f(1, (x for x in a))')
        eq('f((x for x in a), 2)')
        eq('(((a)))', 'a')
        eq('(((a, b)))', '(a, b)')
        eq("(x := 10)")
        eq("f'{(x := 10):=10}'")
        eq("1 + 2 + 3")

    def test_fstring_debug_annotations(self):
        # f-strings with '=' don't round trip very well, so set the expected
        # result explicitely.
        self.assertAnnotationEqual("f'{x=!r}'", expected="f'x={x!r}'")
        self.assertAnnotationEqual("f'{x=:}'", expected="f'x={x:}'")
        self.assertAnnotationEqual("f'{x=:.2f}'", expected="f'x={x:.2f}'")
        self.assertAnnotationEqual("f'{x=!r}'", expected="f'x={x!r}'")
        self.assertAnnotationEqual("f'{x=!a}'", expected="f'x={x!a}'")
        self.assertAnnotationEqual("f'{x=!s:*^20}'", expected="f'x={x!s:*^20}'")

    def test_infinity_numbers(self):
        inf = "1e" + repr(sys.float_info.max_10_exp + 1)
        infj = f"{inf}j"
        self.assertAnnotationEqual("1e1000", expected=inf)
        self.assertAnnotationEqual("1e1000j", expected=infj)
        self.assertAnnotationEqual("-1e1000", expected=f"-{inf}")
        self.assertAnnotationEqual("3+1e1000j", expected=f"3 + {infj}")
        self.assertAnnotationEqual("(1e1000, 1e1000j)", expected=f"({inf}, {infj})")
        self.assertAnnotationEqual("'inf'")
        self.assertAnnotationEqual("('inf', 1e1000, 'infxxx', 1e1000j)", expected=f"('inf', {inf}, 'infxxx', {infj})")
        self.assertAnnotationEqual("(1e1000, (1e1000j,))", expected=f"({inf}, ({infj},))")

o_was_deleted = False
from test import future_co_annotations

class CoAnnotationsFutureTestCase(unittest.TestCase):

    def _test(self, o):

        def pre_dict_able():
            return {'predict': int, 'able': str}

        ##
        ## this test scaffolding relies on instant object destruction.
        ## sorry, gilectomy!
        ##
        class CallableWithDelNotification:
            def __init__(self):
                global o_was_deleted
                o_was_deleted = False

            def __del__(self):
                global o_was_deleted
                o_was_deleted = True

            def __call__(self):
                raise RuntimeError("CallableWithDelNotification should never be called")

        class DictWithDelNotification(dict):
            def __init__(self):
                super().__init__()
                global o_was_deleted
                o_was_deleted = False

            def __del__(self):
                global o_was_deleted
                o_was_deleted = True

        # smoke test:
        # all the predefined annotations dicts should have 3 elements
        # and their values should be of the form
        #   "{name}_{type}" = type
        self.assertTrue(callable(o.__co_annotations__))
        self.assertIsInstance(o.__co_annotations__, types.FunctionType)
        value = o.__co_annotations__
        self.assertEqual(o.__co_annotations__, value)
        self.assertIsInstance(o.__annotations__, dict)
        self.assertIsNone(o.__co_annotations__)
        for name, value in o.__annotations__.items():
            self.assertIsInstance(value, type)
            self.assertEqual(name.partition("_")[2], value.__name__)

        # setting __co_annotations__ to a function should work as expected
        o.__co_annotations__ = pre_dict_able
        self.assertEqual(o.__co_annotations__, pre_dict_able)
        self.assertEqual(o.__annotations__, pre_dict_able())
        self.assertIsNone(o.__co_annotations__)

        # you can set __co_annotations__ to a lambda!
        o.__co_annotations__ = lambda: {'x': int}
        self.assertDictEqual(o.__annotations__, {'x': int})
        self.assertIsNone(o.__co_annotations__)

        # you can set __co_annotations__ to a method!
        class UselessClass:
            def make_dict(self):
                return {'x': int, 'y': str}
        uc = UselessClass()

        o.__co_annotations__ = uc.make_dict
        self.assertDictEqual(o.__annotations__, uc.make_dict())
        self.assertIsNone(o.__co_annotations__)

        # you can set __co_annotations__ to a type!
        o.__co_annotations__ = dict
        self.assertDictEqual(o.__annotations__, {})
        self.assertIsNone(o.__co_annotations__)

        # you can set __co_annotations__ to a closure!
        def outer(d):
            def inner():
                return d
            return inner
        d = {'name': float, 'name2': complex}
        o.__co_annotations__ = outer(d)
        self.assertDictEqual(o.__annotations__, d)
        self.assertIsNone(o.__co_annotations__)

        # setting __annotations__ unsets __co_annotations__!
        o.__co_annotations__ = pre_dict_able
        o.__annotations__ = pre_dict_able()
        self.assertIsNone(o.__co_annotations__)

        # let's confirm that another way
        o.__co_annotations__ = CallableWithDelNotification()
        self.assertFalse(o_was_deleted)
        o.__annotations__ = {}
        self.assertTrue(o_was_deleted)

        def assert_annotations_was_deleted():
            sentinel = object()
            if isinstance(o, types.FunctionType):
                # functions re-generate an empty annotations dict
                # when you delete them
                result = {}
            else:
                result = sentinel
            self.assertEqual(getattr(o, "__annotations__", sentinel), result)

        # setting __co_annotations__ unsets __annotations__!
        o.__annotations__ = pre_dict_able()
        o.__co_annotations__ = pre_dict_able
        o.__co_annotations__ = None
        assert_annotations_was_deleted()


        # let's confirm that another way
        o.__annotations__ = DictWithDelNotification()
        self.assertFalse(o_was_deleted)
        o.__co_annotations__ = pre_dict_able
        self.assertTrue(o_was_deleted)


        # you can't delete __co_annotations__.
        with self.assertRaises(TypeError):
            del o.__co_annotations__

        # you can delete __co_annotations__.
        o.__annotations__ = {}
        del o.__annotations__
        assert_annotations_was_deleted()

        # __co_annotations__ and __annotations__ are both strict
        # about what values you can set them to.
        class Subclass:
            pass

        for value in (
                1+2j,
                3.5,
                ("foo","bar"),
                [1,2,3],
                object(),
                Subclass(),
                set(),
                pre_dict_able.__code__, # code object
                {},

                # these values might work
                pre_dict_able,
                None,
                dict,

            ):
            # you can only set __co_annotations__ to either None or a callable
            if callable(value) or (value == None):
                o.__co_annotations__ = value
                self.assertEqual(o.__co_annotations__, value, f"failed with value {value}")
            else:
                with self.assertRaises(TypeError, msg=f"shouldn't have worked with value {value}"):
                    o.__co_annotations__ = value


    def test_function(self):
        self._test(future_co_annotations.fn)

        del future_co_annotations.fn.__annotations__
        self.assertEqual(future_co_annotations.fn.__annotations__, {})

    def test_class(self):
        self._test(future_co_annotations.MyType)

    def test_class_annotations_inheritance(self):
        class A:
            a_int:int=3
            a_str:str="foo"

        class B(A):
            pass

        self.assertDictEqual(B.__annotations__, {'a_int': int, 'a_str': str})

    def test_module(self):
        self._test(future_co_annotations)

    def test_class_scoping(self):
        self.assertEqual(
            future_co_annotations.Nested.f.__annotations__,
            {"x": int}
        )

    def test_closure_and_classvar(self):
        C = future_co_annotations.closure_and_classvars()

        co1 = C.method1.__co_annotations__
        co2 = C.method2.__co_annotations__
        co3 = C.method3.__co_annotations__
        co4 = C.method4.__co_annotations__
        co5 = C.method5.__co_annotations__

        self.assertEqual(C.method1.__annotations__, {'p1': 'a1'})
        self.assertEqual(C.method2.__annotations__, {'p2': 'a2'})
        self.assertEqual(C.method3.__annotations__, {'p3': 'a3'})
        self.assertEqual(C.method4.__annotations__, {'p4': 'a4'})
        self.assertEqual(C.method5.__annotations__, {'p5': int})

        self.assertFalse(co1)
        self.assertFalse(co2)
        self.assertTrue(co3)
        self.assertTrue(co4)
        self.assertTrue(co5)

        self.assertFalse(C.method1.__co_annotations__)
        self.assertFalse(C.method2.__co_annotations__)
        self.assertFalse(C.method3.__co_annotations__)
        self.assertFalse(C.method4.__co_annotations__)
        self.assertFalse(C.method5.__co_annotations__)


if __name__ == "__main__":
    unittest.main()
