#!/usr/bin/env python3
"""
Generate SQL to backfill a child table's company_id from its parent, for every
*stored* company_id field that is derived from a parent record's company_id.

Multi-company rule: many child tables must carry the same company_id as their
parent (order line ← order, payment ← pos_order, leave ← employee, ...). In Odoo
this is almost always expressed as:

    company_id = fields.Many2one(related='<parent_field>.company_id', store=True)

This script introspects the live registry and, for each such field, emits:

    UPDATE <child_table> c
       SET company_id = p.company_id
      FROM <parent_table> p
     WHERE c.<parent_fk> = p.id
       AND c.company_id IS NULL
       AND p.company_id IS NOT NULL;

It also reports stored company_id fields computed from a parent (related not set)
as TODO comments — those need a manual parent mapping.

Run inside the Odoo shell against a fully-installed database:

    odoo shell -c <conf> -d <db> --no-http < gen_company_id_backfill_sql.py > company_id_backfill.sql

`env` is provided by the shell.
"""

lines = []
todo = []
seen = set()

for model_name in sorted(env.registry):                       # noqa: F821 (env from shell)
    model = env[model_name]
    if model._abstract or model._transient or not model._auto:
        continue
    field = model._fields.get('company_id')
    if field is None or not field.store or field.type != 'many2one':
        continue
    table = model._table
    if table in seen:
        continue
    seen.add(table)

    related = getattr(field, 'related', None)
    if related and related.endswith('.company_id') and related.count('.') == 1:
        parent_fname = related.split('.')[0]
        pf = model._fields.get(parent_fname)
        if pf is not None and pf.type == 'many2one' and pf.store:
            parent_table = env[pf.comodel_name]._table
            # the FK column for a stored many2one is the field name
            lines.append(
                f"-- {model_name}.company_id <- {pf.comodel_name}.company_id (via {parent_fname})\n"
                f"UPDATE {table} c\n"
                f"   SET company_id = p.company_id\n"
                f"  FROM {parent_table} p\n"
                f" WHERE c.{parent_fname} = p.id\n"
                f"   AND c.company_id IS NULL\n"
                f"   AND p.company_id IS NOT NULL;\n"
            )
            continue
        todo.append(f"-- TODO related but parent field not stored m2o: {model_name}.company_id (related={related})")
    elif field.compute and not related:
        todo.append(f"-- TODO computed company_id (map parent manually): {model_name}.company_id (compute={field.compute})")

print("-- =====================================================================")
print("-- Backfill child.company_id from parent.company_id where child is NULL")
print("-- Generated from the live Odoo registry. Review before running.")
print("-- Wrap in BEGIN/COMMIT and run on a backup first.")
print("-- =====================================================================\n")
print("BEGIN;\n")
print("\n".join(lines))
print("COMMIT;\n")
if todo:
    print("\n-- ---- needs manual review (computed / non-trivial parent) ----")
    print("\n".join(sorted(set(todo))))
