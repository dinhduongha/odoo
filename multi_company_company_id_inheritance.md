# Multi-company: child `company_id` inheriting from a parent

Reference for the uuidv7 port. In multi-company, many child tables must carry the
**same `company_id` as their parent record** (an order line's company follows the
order; lines/payments/leaves follow their order/employee/...). If a child row's
`company_id` is left NULL, multi-company record rules and consistency checks break.

This documents which models do this and how to backfill NULL child `company_id`.

## How it is expressed in Odoo

Almost always a **stored related** field:

```python
company_id = fields.Many2one(related='<parent_field>.company_id', store=True)
```

The stored column is physically present and should track the parent — but a row
created before the related was computed (or via raw SQL / migration) can be NULL.

## Canonical examples (child ← parent)

| Child model | Parent field → parent model |
|---|---|
| `sale.order.line` | `order_id` → `sale.order` |
| `account.move.line` | `move_id` → `account.move` |
| `purchase.order.line` | `order_id` → `purchase.order` |
| `pos.order.line` | `order_id` → `pos.order` |
| `pos.payment` | `pos_order_id` → `pos.order` |
| `pos.session` | `config_id` → `pos.config` |
| `mrp.bom.line` | `bom_id` → `mrp.bom` |
| `mrp.workorder` | `production_id` → `mrp.production` |
| `stock.quant` | `location_id` → `stock.location` |
| `loyalty.{card,reward,rule}` | `program_id` → `loyalty.program` |
| `event.event.ticket` | `event_id` → `event.event` |
| `hr.leave` / `hr.leave.allocation` | `employee_id` → `hr.employee` (field `employee_company_id`) |
| `hr.resume.line` | `employee_id` → `hr.employee` |
| `hr.attendance.overtime` | `employee_id` → `hr.employee` |
| `lunch.product` | `supplier_id` → `lunch.supplier` |
| `lunch.supplier` | `partner_id` → `res.partner` |
| `account.fiscal.position` company (partner) | `position_id` → ... |
| `res.bank`→`res.partner.bank` | `partner_id` → `res.partner` |

> Not parent-derived (own `company_id`, set by default/compute, do NOT backfill from a
> parent): `stock.move`, `stock.move.line`, `hr.employee`, `mrp.production`,
> `account.move`, `sale.order`, etc. These are the *parents*.

The full, always-current list is whatever the registry reports — generate it (below)
rather than trusting this table after code changes.

## Generate the backfill SQL (authoritative)

`gen_company_id_backfill_sql.py` introspects the live registry and emits one
`UPDATE` per stored `company_id` that is `related='<parent>.company_id'`:

```bash
# against a fully-installed db, inside the odoo container:
odoo shell -c /tmp/t.conf -d <db> --no-http < gen_company_id_backfill_sql.py \
  > company_id_backfill.sql
```

Each statement is of the form:

```sql
UPDATE <child_table> c
   SET company_id = p.company_id
  FROM <parent_table> p
 WHERE c.<parent_fk> = p.id
   AND c.company_id IS NULL
   AND p.company_id IS NOT NULL;
```

Only fills rows where the child `company_id` IS NULL (idempotent, non-destructive).
Computed-from-parent `company_id` fields that don't use `related=` are emitted as
`-- TODO` comments for manual mapping.

## Notes for uuidv7

- `company_id` is now `uuid`; the joins above are uuid = uuid (fine).
- After backfilling, a stored related `company_id` stays correct on subsequent
  writes because the ORM recomputes it from the parent.
- Run inside a transaction, on a backup first; review the generated file.
