/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@web/core/utils/component";

export class IdShortField extends Component {
    static template = "web.IdShortField";
    static props = standardFieldProps;

    get displayValue() {
        const id = this.props.record.data[this.props.name];
        return id ? String(id).split("-")[0] : "";
    }
}
registry.category("fields").add("id_short", IdShortField);
