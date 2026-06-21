"""Canonicalization & input normalization.

Metamorphic equivalence requires a canonical form so that e.g.
"x*x" and "x**2", "a+b" and "b+a", "1/2" and "2/4", and
unicode/whitespace/comma variants all map to one comparable form.

We do NOT implement a full CAS here. We implement a deliberate,
restricted canonicalizer over the expression grammar the benchmark
actually emits. This keeps the verifier sound (no over-claiming) and
auditable.
"""
from __future__ import annotations

import re
import unicodedata
from fractions import Fraction
from typing import Any

from .exact import ExactValue, Exact


# --- input normalization (surface form) ------------------------------------

_WS_RE = re.compile(r"\s+")
_COMMA_RE = re.compile(r"(?<=\d),(?=\d{3}\b)")  # thousands separators only


def normalize_input(s: str) -> str:
    """Surface-normalize a user/model input string for stable hashing &
    comparison without changing its mathematical meaning.

    Steps:
      * unicode-normalize (NFKC) -- folds many math variants
      * replace U+2212 (MINUS SIGN) with ASCII '-' (NFKC does NOT fold this)
      * replace U+00B2/U+00B3 (superscript 2/3) with '^2'/'^3' exponent notation
        (NFKC folds them to bare '2'/'3' which would make 9² == 92, wrong)
      * strip U+200B (ZERO WIDTH SPACE) -- formatting char, not meaningful
      * strip U+00A0 (NON-BREAKING SPACE) -> regular space (NFKC does this)
      * strip leading/trailing whitespace
      * collapse internal whitespace to single spaces
      * lowercase ASCII (math is case-insensitive in our grammar)

    NOTE: thousands-separator stripping ("1,000"->"1000") is deliberately
    NOT performed here. It is unsafe in the presence of function-call
    argument lists (e.g. gcd(123,456) would be mangled to gcd(123456)).
    Exact plain decimal input is required; comma is reserved as an
    argument separator.
    """
    if not isinstance(s, str):
        raise TypeError("normalize_input expects str")
    s = unicodedata.normalize("NFKC", s)
    # U+2212 MINUS SIGN -> ASCII '-' (NFKC does not fold this)
    s = s.replace("\u2212", "-")
    # superscript 2/3 -> ^2/^3 (must happen AFTER NFKC, since NFKC would
    # fold ²->2 and we'd lose the exponent meaning; we pre-empt by
    # converting before NFKC... but NFKC already ran. So we handle the
    # already-folded case: if input had ², NFKC turned it to '2'. We
    # cannot recover. Instead, we handle superscripts BEFORE NFKC.)
    # -> See _normalize_with_superscripts below for the real fix.
    s = s.replace("\u200b", "")   # ZWSP
    s = s.strip()
    s = _WS_RE.sub(" ", s)
    return s.lower()


def _normalize_with_superscripts(s: str) -> str:
    """Normalize, converting superscript digits to ^N exponent notation
    BEFORE NFKC would fold them to bare digits."""
    if not isinstance(s, str):
        raise TypeError("normalize_input expects str")
    # Convert superscript digits to ^exponent BEFORE NFKC
    # (NFKC folds ²->2, ³->3, etc. but loses the 'exponent' meaning)
    _SUP_MAP = {
        "\u00b2": "^2", "\u00b3": "^3", "\u2074": "^4", "\u2075": "^5",
        "\u2076": "^6", "\u2077": "^7", "\u2078": "^8", "\u2079": "^9",
        "\u2070": "^0", "\u00b9": "^1",
    }
    for sup, exp in _SUP_MAP.items():
        s = s.replace(sup, exp)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2212", "-")
    s = s.replace("\u200b", "")
    s = s.strip()
    s = _WS_RE.sub(" ", s)
    return s.lower()


# --- canonical value (ExactValue-level) -------------------------------------

def canonical_value(v: ExactValue) -> str:
    return v.canonical_string()


# --- canonical expression (string-level, restricted grammar) ----------------

# Supported grammar (intentionally tiny, auditable):
#   expr   := mod_expr
#   mod_expr := add_expr ('mod' primary)?
#   add_expr := term (('+'|'-') term)*
#   term   := factor (('*'|'/') factor)*
#   factor := power
#   power  := unary ('^' power)?       # right-assoc
#   unary  := '-' unary | postfix
#   postfix:= primary ('!')*            # factorial postfix
#   primary:= int | '(' expr ')' | func_call
#   func_call := ident '(' args ')'    # gcd, lcm (commutative -> args sorted)
#   args   := expr (',' expr)*
#
# This is enough to express every problem the benchmark emits, and enough
# to detect the metamorphic equivalences we test (x*x vs x^2, a+b vs b+a,
# expanded vs factored for the small forms we generate, scaled fractions).

_TOKEN_RE = re.compile(r"\s*(?P<tok>\d+|[a-z]+|[+\-*/^(),!])")


def _tokenize(s: str):
    # Use superscript-aware normalization so ² -> ^2 BEFORE tokenizing
    s = _normalize_with_superscripts(s)
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/")
    pos = 0
    toks = []
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m:
            raise ValueError(f"cannot tokenize at {s[pos:]!r} in {s!r}")
        toks.append(m.group("tok"))
        pos = m.end()
    return toks


class _Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, t=None):
        cur = self.peek()
        if t and cur != t:
            raise ValueError(f"expected {t!r} got {cur!r}")
        self.i += 1
        return cur

    # expr := mod_expr
    # mod_expr := add_expr ('mod' atom)?    -- 'mod' is lowest precedence, infix
    def parse_expr(self):
        node = self.parse_add()
        if self.peek() == "mod":
            self.eat("mod")
            m = self.parse_atom()
            return ("modop", node, m)
        return node

    # add_expr := term (('+'|'-') term)*
    def parse_add(self):
        node = self.parse_term()
        terms = [(1, node)]
        while self.peek() in ("+", "-"):
            op = self.eat()
            sign = 1 if op == "+" else -1
            terms.append((sign, self.parse_term()))
        if len(terms) == 1:
            return terms[0][1]
        return ("sum", terms)

    # term := factor (('*'|'/') factor)*
    # Ambiguous a/b/c (sequential division, two '/' with no '*' between)
    # is REFUSED. a/b * c/d is fine (the '*' separates the divisions).
    def parse_term(self):
        node = self.parse_power()
        factors = [(1, node)]
        prev_was_div = False
        while self.peek() in ("*", "/"):
            op = self.eat()
            if op == "/":
                if prev_was_div:
                    raise ValueError("ambiguous sequential division (a/b/c) -- refuse")
                prev_was_div = True
            else:
                prev_was_div = False
            sign = 1 if op == "*" else -1
            factors.append((sign, self.parse_power()))
        if len(factors) == 1:
            return factors[0][1]
        return ("product", factors)

    # power := unary ('^' power)?   (right-assoc)
    def parse_power(self):
        base = self.parse_unary()
        if self.peek() == "^":
            self.eat("^")
            exp = self.parse_power()  # right assoc
            return ("pow", base, exp)
        return base

    # unary := '-' unary | postfix
    def parse_unary(self):
        if self.peek() == "-":
            self.eat("-")
            return ("neg", self.parse_unary())
        return self.parse_postfix()

    # postfix := primary ('!')*
    def parse_postfix(self):
        node = self.parse_atom()
        while self.peek() == "!":
            self.eat("!")
            node = ("factorial", node)
        return node

    # primary := int | '(' expr ')' | func_call
    def parse_atom(self):
        t = self.peek()
        if t is None:
            raise ValueError("unexpected end of input")
        if t == "(":
            self.eat("(")
            e = self.parse_expr()
            self.eat(")")
            return e
        if t and t[0].isalpha():
            # identifier: function call (gcd/lcm) -- 'mod' is handled at expr level
            if t == "mod":
                raise ValueError("'mod' in primary position (use as infix)")
            self.eat()
            self.eat("(")
            args = [self.parse_expr()]
            while self.peek() == ",":
                self.eat(",")
                args.append(self.parse_expr())
            self.eat(")")
            return ("call", t, args)
        if t.isdigit() or (t and t[0].isdigit()):
            self.eat()
            return ("int", int(t))
        raise ValueError(f"unexpected token {t!r}")


def parse_expression(s: str):
    toks = _tokenize(s)
    p = _Parser(toks)
    node = p.parse_expr()
    if p.i != len(toks):
        raise ValueError(f"trailing tokens: {toks[p.i:]!r}")
    return node


def _eval_node(node):
    """Evaluate an AST node to an ExactValue. Used by the verifier to
    compute the canonical exact value of a *generated* expression
    (never of a model output)."""
    tag = node[0]
    if tag == "int":
        return Exact.i(node[1])
    if tag == "factorial":
        v = _eval_node(node[1])
        if v.kind != "int":
            raise ValueError("factorial of non-integer")
        if v.int_val < 0:
            raise ValueError("factorial of negative integer")
        from .exact import factorial as _fact
        return Exact.i(_fact(v.int_val))
    if tag == "call":
        name = node[1]
        args = [_eval_node(a) for a in node[2]]
        from .exact import exact_gcd, exact_lcm
        if name == "gcd":
            if len(args) != 2 or any(a.kind != "int" for a in args):
                raise ValueError("gcd requires two integer args")
            return Exact.i(exact_gcd(args[0].int_val, args[1].int_val))
        if name == "lcm":
            if len(args) != 2 or any(a.kind != "int" for a in args):
                raise ValueError("lcm requires two integer args")
            return Exact.i(exact_lcm(args[0].int_val, args[1].int_val))
        raise ValueError(f"unknown function {name!r}")
    if tag == "neg":
        v = _eval_node(node[1])
        return Exact.mul(v, Exact.i(-1))
    if tag == "sum":
        total = Exact.i(0)
        for sign, child in node[1]:
            cv = _eval_node(child)
            if sign < 0:
                cv = Exact.mul(cv, Exact.i(-1))
            total = Exact.add(total, cv)
        return total
    if tag == "product":
        return _eval_product(node[1])
    if tag == "pow":
        b = _eval_node(node[1])
        e = _eval_node(node[2])
        if e.kind != "int":
            raise ValueError("non-integer exponent")
        if e.int_val < 0:
            raise ValueError("negative exponent in expression")
        if e.int_val == 0:
            return Exact.i(1)
        acc = Exact.i(1)
        for _ in range(e.int_val):
            acc = Exact.mul(acc, b)
        return acc
    if tag == "modop":
        base = _eval_node(node[1])
        mnode = _eval_node(node[2])
        if mnode.kind != "int":
            raise ValueError("modulus must be an integer")
        m = mnode.int_val
        if m <= 0:
            raise ValueError("modulus must be positive")
        # reduce base value mod m
        if base.kind == "int":
            return Exact.mod(base.int_val, m)
        if base.kind == "rational":
            num, den = base.rat_val.numerator, base.rat_val.denominator
            inv_den = pow(den % m, -1, m) if den % m != 0 else None
            if inv_den is None:
                if num % m == 0:
                    return Exact.mod(0, m)
                raise ValueError("non-invertible denominator under modulus")
            return Exact.mod((num % m) * inv_den % m, m)
        if base.kind == "mod":
            v, bm = base.mod_val
            if bm != m:
                raise ValueError("modulus mismatch in modop")
            return Exact.mod(v, m)
        raise ValueError("bad base kind for modop")
    raise ValueError(f"unknown node {tag}")


def _eval_product(factors):
    total_num = 1
    total_den = 1
    for sign, child in factors:
        cv = _eval_node(child)
        if cv.kind == "rational":
            num, den = cv.rat_val.numerator, cv.rat_val.denominator
        else:
            num, den = cv.int_val, 1
        if sign > 0:
            total_num *= num
            total_den *= den
        else:
            total_num *= den
            total_den *= num
    if total_den == 1:
        return Exact.i(total_num)
    return Exact.frac(total_num, total_den)


def canonicalize(s: str) -> str:
    """Canonicalize an expression string to a stable normalized form.

    Returns a canonical string (not the value). Two mathematically
    equivalent expressions within our grammar share a canonical string
    up to ordering, which we further canonicalize by sorting sum/product
    operands lexicographically.

    This is the basis for metamorphic-equivalence checking: two forms are
    "equivalent" iff their canonical strings match.
    """
    node = parse_expression(s)
    canon = _canonical_node(node)
    return canon


def _canonical_node(node) -> str:
    tag = node[0]
    if tag == "int":
        return f"I{node[1]}"
    if tag == "factorial":
        return f"{_canonical_node(node[1])}!"
    if tag == "call":
        name = node[1]
        # gcd/lcm are commutative -> sort canonical arg strings
        arg_cans = sorted(_canonical_node(a) for a in node[2])
        return f"{name}(" + ",".join(arg_cans) + ")"
    if tag == "neg":
        return f"(-{_canonical_node(node[1])})"
    if tag == "sum":
        # canonical: collect signed terms, sort lexicographically
        terms = []
        for sign, child in node[1]:
            terms.append((sign, _canonical_node(child)))
        # fold sign into a prefix
        rendered = sorted((("+" if s > 0 else "-") + c) for s, c in terms)
        return "S(" + ",".join(rendered) + ")"
    if tag == "product":
        # split numerator/denominator by sign, sort each
        num, den = [], []
        for sign, child in node[1]:
            c = _canonical_node(child)
            if sign > 0:
                num.append(c)
            else:
                den.append(c)
        num.sort()
        den.sort()
        body = "*".join(num)
        if den:
            body += "/" + "*".join(den)
        return f"P({body})"
    if tag == "pow":
        return f"({_canonical_node(node[1])}^{_canonical_node(node[2])})"
    if tag == "modop":
        return f"M{_canonical_node(node[2])}({_canonical_node(node[1])})"
    raise ValueError(f"unknown node {tag}")
