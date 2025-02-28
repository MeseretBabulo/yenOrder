/** @odoo-module **/

// import { Field } from "@web/views/fields/abstract_field";
import { Field } from "@web/views/fields/field";

import {
    registry
} from "@web/core/registry";
class InheritStatusbarFields extends Field {
    setup() {
        super.setup();
        this._setState();
        this.onClickStage = this.debounce(this.onClickStageHandler, 300, true);
    }

    _setState() {
        // Implement the state setting logic here.
    }

    onClickStageHandler() {
        // Implement what happens when you click a stage.
    }

    get isClickable() {
        // Retro-compatibility: check if statusbar is clickable
        try {
            return !!JSON.parse(this.props.attrs.clickable);
        } catch {
            if (this.props.model === "crm.lead" && this.props.mode !== 'edit') {
                return false;
            } else {
                return !!this.props.nodeOptions.clickable;
            }
        }
    }

    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const context = this;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }
}

// Register your custom field in the field registry
registry.category("fields").add("inherit_statusbar_fields", InheritStatusbarFields);
