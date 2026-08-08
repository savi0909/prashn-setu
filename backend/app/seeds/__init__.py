"""Reading the domain knowledge base and seeding it into the database.

``shared/domain/`` is master for the subject taxonomy and the class-level list
(ADR 0002) and is also the source this package reads — there is no second copy.
``kb.py`` parses and validates it; the loader writes it to Postgres.
"""
