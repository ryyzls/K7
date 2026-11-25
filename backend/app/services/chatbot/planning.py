"""Bounded, serializable conversation plans over the shared semantic parser."""
from __future__ import annotations

import re
from typing import Literal, Protocol
from pydantic import BaseModel, Field, model_validator
from app.services import hybrid_search as hs


class Condition(BaseModel):
    op: Literal['atom', 'text', 'none', 'and', 'or', 'not']
    field: Literal['class', 'type', 'region', 'region_group', 'province', 'owner', 'service', 'facility', 'concept', 'hours'] | None = None
    value: str = Field(default='', max_length=240)
    children: list['Condition'] = Field(default_factory=list, max_length=2)

    @model_validator(mode='after')
    def shape(self):
        count = 2 if self.op in ('and', 'or') else 1 if self.op == 'not' else 0
        if len(self.children) != count or (self.op == 'atom' and not self.field):
            raise ValueError('Invalid condition shape')
        return self

    def tree(self):
        if self.op == 'atom':
            return ('atom', hs.Atom(self.field, self.value))
        if self.op == 'text':
            return ('text', self.value)
        return (self.op, *(c.tree() for c in self.children))

    @classmethod
    def from_tree(cls, tree):
        if not tree:
            return None
        op = tree[0]
        if op == 'atom':
            return cls(op=op, field=tree[1].field, value=tree[1].value)
        if op == 'text':
            return cls(op=op, value=tree[1])
        return cls(op=op, children=[cls.from_tree(c) for c in tree[1:]])


class QueryPlan(BaseModel):
    version: Literal[3] = 3
    intent: str = Field(default='SEARCH_FILTER', max_length=40)
    condition: Condition | None = None
    hospital_ids: list[str] = Field(default_factory=list, max_length=3)
    excluded_ids: list[str] = Field(default_factory=list, max_length=206)
    requested_attributes: list[str] = Field(default_factory=list, max_length=12)
    sorting: Literal['relevance', 'distance', 'name'] = 'relevance'
    limit: int = Field(default=5, ge=1, le=20)
    operation: Literal['new', 'add', 'replace', 'remove', 'select'] = 'new'
    clarification: str | None = Field(default=None, max_length=300)
    preferences: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode='after')
    def bounded(self):
        def walk(c, depth=0):
            if depth > 12:
                raise ValueError('Plan too deep')
            return 0 if c is None else 1 + sum(walk(x, depth + 1) for x in c.children)
        if walk(self.condition) > 48:
            raise ValueError('Plan too complex')
        if any(not re.fullmatch(r'rs-\d{3}', x) for x in self.hospital_ids + self.excluded_ids):
            raise ValueError('Invalid hospital identifier')
        return self


class OptionalProvider(Protocol):
    """Future embedding/retrieval/reranking/LLM/response providers: disabled in phase 1."""
    async def execute(self, plan: QueryPlan, evidence: list[dict]) -> dict: ...


def normalize_message(text):
    text = text.casefold().strip()
    replacements = {'yg': 'yang', 'bs': 'bisa', 'gausah': 'hapus', 'gak usah': 'hapus',
                    'nggak usah': 'hapus', 'ga usah': 'hapus', 'jantng': 'jantung',
                    'cuci drah': 'cuci darah', 'siantarr': 'siantar', 'deket': 'dekat',
                    'telpnya': 'teleponnya', 'brp': 'berapa', 'sampe': 'sampai',
                    'carikan': 'cari', 'sama': 'dan', 'aja': 'saja', 'poliklinik': 'poli'}
    for old, new in replacements.items():
        text = re.sub(r'\b' + re.escape(old) + r'\b', new, text)
    return re.sub(r'\s+', ' ', text)


def is_emergency(text):
    """Clause-aware triage trigger, not a diagnosis. Runs before any data access."""
    clauses = re.split(r'[.!?;]|\btapi\b|\btetapi\b|\bnamun\b', normalize_message(text))
    symptoms = r'nyeri dada|sesak napas|sulit bernapas|kesulitan bernapas|tidak (?:sadar|sadarkan diri)|pingsan|perdarahan (?:berat|hebat)|pendarahan (?:berat|hebat)|gejala stroke|wajah mencong|bicara pelo|kejang|mengalami kondisi darurat'
    for clause in clauses:
        if re.search(r'\b(jika|kalau|seandainya|misalnya|apa itu|apa penyebab|apa arti|kemarin|dulu|sudah sembuh|sudah berlalu|riwayat)\b', clause):
            continue
        for match in re.finditer(symptoms, clause):
            prefix = clause[max(0, match.start()-45):match.start()]
            if re.search(r'\b(tidak|bukan|tanpa|tak|nggak|gak)\b[^,]*$', prefix):
                continue
            return True
    return False


def leaves(condition):
    if condition is None:
        return []
    if condition.op in ('atom', 'text'):
        return [condition]
    return [a for c in condition.children for a in leaves(c)]


def prune(condition, predicate):
    if not condition or predicate(condition):
        return None
    if not condition.children:
        return condition
    children = [v for c in condition.children if (v := prune(c, predicate))]
    if not children:
        return None
    if len(children) == 1 and condition.op in ('and', 'or'):
        return children[0]
    return condition.model_copy(update={'children': children})


def combine(a, b, op='and'):
    return Condition(op=op, children=[a, b]) if a and b else a or b


def parse_condition(text, snap, depth=0):
    """Parentheses compose the shared parser; never interpolate input into SPARQL."""
    if depth > 6 or len(text) > 240:
        raise ValueError('Gunakan maksimal 240 karakter dan enam tingkat kondisi.')
    text = text.strip()
    if '(' in text or ')' in text:
        level, start, segments = 0, 0, []
        for i, char in enumerate(text):
            if char == '(':
                if level == 0:
                    segments.append(text[start:i]); start = i + 1
                level += 1
            elif char == ')':
                level -= 1
                if level < 0:
                    raise ValueError('Tanda kurung tidak seimbang.')
                if level == 0:
                    segments.append(('group', text[start:i])); start = i + 1
        if level:
            raise ValueError('Tanda kurung tidak seimbang.')
        segments.append(text[start:])
        result, connector = None, 'and'
        for part in segments:
            if isinstance(part, tuple):
                node = parse_condition(part[1], snap, depth+1)
            else:
                connector = 'or' if re.match(r'^\s*(atau|or)\b', part) else connector
                stripped = re.sub(r'^(dan|atau|and|or)\s+|\s+(dan|atau|and|or)$', '', part.strip()).strip()
                if stripped in ('dan', 'atau', 'and', 'or', 'rs', 'rumah sakit', 'cari rs', 'yang punya', ''):
                    if stripped in ('atau', 'or'): connector = 'or'
                    continue
                node = parse_condition(stripped, snap, depth+1)
            result = combine(result, node, connector); connector = 'and'
        return result
    # Exclusion of a hospital name uses the same entity matcher as shared search.
    exclusion = re.search(r'\b(?:selain|bukan)\s+(.+)$', text)
    if exclusion and not hs.norm(exclusion[1]) in snap['vocab']:
        excl_tail = exclusion[1].strip()
        # selain kelas A/B/C/D → NOT(class=X) condition
        kelas_match = re.fullmatch(r'kelas\s+([abcd])', excl_tail, re.IGNORECASE)
        if kelas_match:
            base_txt = text[:exclusion.start()].strip()
            base = parse_condition(base_txt, snap, depth+1) if base_txt not in ('', 'rs', 'rumah sakit') else None
            not_class = Condition(op='not', children=[Condition(op='atom', field='class', value=kelas_match[1].upper())])
            return combine(base, not_class)
        base = parse_condition(text[:exclusion.start()], snap, depth+1) if text[:exclusion.start()].strip() not in ('', 'rs', 'rumah sakit') else None
        return combine(base, Condition(op='not', children=[Condition(op='text', value=excl_tail)]))
    tree, atoms, corrections, notices, suggestions = hs.parse(text, snap)
    if tree and tree[0] == 'none' and notices:
        raise ValueError(notices[0])
    return Condition.from_tree(tree)
