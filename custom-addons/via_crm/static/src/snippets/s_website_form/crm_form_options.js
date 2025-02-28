/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CRMFormOptions extends Component {
    static template = xml`
        <div t-name="CRMFormOptions">
            <!-- Your actual template markup -->
            <div class="custom-field-options">
                <t t-foreach="props.fields" t-as="field">
                    <div class="field-option" t-on-click="() => this.replaceField(field)">
                        <span t-esc="field.label"/>
                    </div>
                </t>
            </div>
        </div>
    `;

    static props = {
        fields: { type: Array },
    };

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        // Initialize other services or state here
    }

    async replaceField(field) {
        await this.fetchFieldRecords(field);
        const activeField = this.getActiveField();
        
        if (field.name !== 'partner_relationship' && activeField.type !== field.type) {
            this.clearFieldValue(field);
            this.renderNewField(field);
        }
    }

    // Example service call
    async fetchFieldRecords(field) {
        return this.rpc("/your/custom/route", {
            field_id: field.id,
        });
    }

    // Add remaining method implementations...
}