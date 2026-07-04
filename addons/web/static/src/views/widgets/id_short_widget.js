/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class IdShortField extends Component {
    static template = "web.IdShortField";
    static props = standardFieldProps;

    get displayValue() {
        const id = this.props.record.data[this.props.name];
        return id ? String(id).split("-")[0] : "";
    }
}

// The fields registry validates entries as a field descriptor { component, ... },
// not the component class directly (fails debug-mode validation otherwise).
export const idShortField = {
    component: IdShortField,
};
registry.category("fields").add("id_short", idShortField);
