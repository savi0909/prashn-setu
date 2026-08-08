"""The executable half of the domain knowledge base (ADR 0002).

``shared/domain/`` holds the facts. This package holds the rules that no row can
express — the ones Appendix C stated in prose and the §5.5 DDL never
implemented.

Every rule carries a ``RULE <id>:`` first line in its docstring. ``make
domain-docs`` harvests those into ``docs/domain-model.md``, so the rendered
document and the enforced behaviour cannot drift: a rule that stops being true
fails the build rather than quietly becoming stale documentation.
"""
