/** @odoo-module **/

// import { Component, xml } from "owl";
import { Component, xml} from  "@odoo/owl";
class WebsiteCrmFormEditor extends Component {
    constructor() {
        super(...arguments);
        this.formFields = this._getFormFields();
        this.fields = this._getFields();
    }

    _getFormFields() {
        return [
            { type: 'char', required: true, name: 'contact_name', fillWith: 'name', string: 'Your Name' },
            { type: 'tel', name: 'phone', fillWith: 'phone', string: 'Phone Number' },
            { type: 'email', required: true, fillWith: 'email', name: 'email_from', string: 'Your Email' },
            { type: 'char', required: true, fillWith: 'commercial_company_name', name: 'partner_name', string: 'Your Company' },
            { type: 'char', modelRequired: true, name: 'name', string: 'Subject' },
            { type: 'text', required: true, name: 'description', string: 'Your Question' },
            {
                type: 'selection',
                required: true,
                name: 'partner_relationship',
                fillWith: 'partner_relationship',
                string: 'Partner Relationship',
                isCheckedBox: true,
                records: [
                    { 'display_name': 'Self', 'name': 'self' },
                    { 'display_name': 'Mother', 'name': 'mother' },
                    { 'display_name': 'Father', 'name': 'father' },
                    { 'display_name': 'Spouse', 'name': 'spouse' },
                    { 'display_name': 'Son', 'name': 'son' },
                    { 'display_name': 'Daughter', 'name': 'daughter' },
                    { 'display_name': 'Friend', 'name': 'friend' },
                    { 'display_name': 'Sibling', 'name': 'sibling' },
                    { 'display_name': 'Relative', 'name': 'relative' },
                    { 'display_name': 'Other', 'name': 'other' }
                ],
            },
            { type: 'char', required: true, name: 'representative_firstname', fillWith: 'representative_firstname', string: 'First Name', class: 'first_name_div' },
            { type: 'char', required: true, name: 'representative_lastname', fillWith: 'representative_lastname', string: 'Last Name' }
        ];
    }

    _getFields() {
        return [
            { name: 'team_id', type: 'many2one', relation: 'crm.team', domain: [['use_opportunities', '=', true]], string: 'Sales Team', title: 'Assign leads/opportunities to a sales team.' },
            { name: 'user_id', type: 'many2one', relation: 'res.users', string: 'Salesperson', title: 'Assign leads/opportunities to a salesperson.' },
        ];
    }
}

WebsiteCrmFormEditor.template = xml`<div>
    <!-- Implement form rendering here -->
</div>`;
