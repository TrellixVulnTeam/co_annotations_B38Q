from __future__ import co_annotations

m_int:int=3
m_str:str=b"foo"
m_MyType:MyType=None

def fn(fn_int:int=3, fn_str:str="foo", fn_MyType:MyType=None):
    pass

class MyType:
    kls_int:int=3
    kls_str:str="foo"
    kls_MyType:MyType=None


class Nested:
    alias = int
    def f(self, x: alias):
        pass
