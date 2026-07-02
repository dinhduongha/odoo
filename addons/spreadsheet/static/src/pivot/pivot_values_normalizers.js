import { registries, helpers, constants } from "@odoo/o-spreadsheet";

const { DEFAULT_LOCALE } = constants;
const { pivotNormalizationValueRegistry } = registries;
const { toString, toNumber } = helpers;

/**
 * Add pivot normalizaton functions to support odoo specific fields
 * in spreadsheet
 */

pivotNormalizationValueRegistry
    .add("text", (value) => toString(value))
    .add("reference", (value) => toString(value))
    .add("selection", (value) => toString(value))
    // uuid PKs: relational record ids are uuid strings, not numbers.
    .add("many2one_reference", (value) => toString(value))
    .add("monetary", (value) => toNumber(value, DEFAULT_LOCALE))
    .add("many2one", (value) => toString(value))
    .add("many2many", (value) => toString(value))
    .add("float", (value) => toNumber(value, DEFAULT_LOCALE));
