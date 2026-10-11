"""Narrow source check for literal CSRF fields and the reviewed token macro.

Rendered HTML and middleware behavior are tested separately. A macro name alone
is never evidence: its definition must be unconditional and emit a signed field.
"""
import re
from html.parser import HTMLParser
from jinja2 import Environment, nodes

FORM=re.compile(r'<form\b[^>]*method=[\"\']post[\"\'][^>]*>(.*?)</form\s*>',re.I|re.S)
MACRO=re.compile(r'{%\s*macro\s+token\(\)\s*%}(.*?){%\s*endmacro\s*%}',re.S)
CALL=re.compile(r'{{\s*token\(\)\s*}}')

def without_comments(source):
    return re.sub(r'<!--.*?-->|{#.*?#}', '', source, flags=re.S)

class Inputs(HTMLParser):
    def __init__(self): super().__init__(); self.secure=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='input' and a.get('type','').lower()=='hidden' and a.get('name')=='csrf_token' and 'disabled' not in a:
            self.secure |= bool(re.fullmatch(r'{{\s*csrf_token\(\)\s*}}',a.get('value','')))

def literal_protected(fragment):
    # Conditional/macro bodies are not unconditional field evidence.
    fragment=re.sub(r'{%\s*(if|for|macro)\b.*?{%\s*end\1\s*%}', '',fragment,flags=re.S)
    parser=Inputs();parser.feed(fragment);return parser.secure

# Existing reply JS copies the escaped server-rendered meta token into its field.
DYNAMIC_FIELD = """<input type="hidden" name="csrf_token" value="' + escapeHtml(document.querySelector("meta[name='csrf-token']").content) + '">"""
SIGNED_FIELD = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

def unprotected_forms(source):
    source=without_comments(source).replace(DYNAMIC_FIELD, SIGNED_FIELD)
    definitions=list(MACRO.finditer(source))
    approved=False
    if len(definitions)==1:
        body=definitions[0][1]
        parsed=Environment().parse(body)
        approved=(len(parsed.body)==1 and isinstance(parsed.body[0],nodes.Output)
                  and all(isinstance(n,nodes.TemplateData) or
                          (isinstance(n,nodes.Call) and isinstance(n.node,nodes.Name)
                           and n.node.name=='csrf_token' and not n.args and not n.kwargs
                           and n.dyn_args is None and n.dyn_kwargs is None)
                          for n in parsed.body[0].nodes)
                  and literal_protected(body))
    failures=[]
    for form in FORM.finditer(source):
        fragment=form[1]
        if approved: fragment=CALL.sub(lambda m:definitions[0][1],fragment)
        if not literal_protected(fragment): failures.append(form.start())
    # An unterminated form is also invalid.
    starts=list(re.finditer(r'<form\b[^>]*method=[\"\']post[\"\'][^>]*>',source,re.I))
    if len(starts)!=len(list(FORM.finditer(source))): failures.extend(m.start() for m in starts)
    return failures
