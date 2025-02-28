/** @odoo-module **/
import { registry } from "@web/core/registry";
import { DocumentsInspector } from "@documents/views/inspector/documents_inspector";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

const TAGS_SEARCH_LIMIT = 8;

patch(DocumentsInspector.prototype, {
    setup() {
        super.setup(); // <-- Use `super.setup()` instead of `this._super()`
        this.state = useState({
            abc: true
        });
    },

    async _renderFields() {
        const options = { mode: 'edit' };
        const proms = [];

        if (this.records.length === 1) {
            proms.push(this._renderField('name', options));
            
            if (this.records[0].data.type === 'url') {
                proms.push(this._renderField('url', options));
            }
            
            proms.push(this._renderField('partner_id', options));
            const record = this.records[0];
            
            if (this.state.abc) {
                proms.push(this._renderField('team_id', options));
            }
        }

        if (this.records.length > 0) {
            proms.push(this._renderField('owner_id', options));
            proms.push(this._renderField('folder_id', {
                icon: 'fa fa-folder o_documents_folder_color',
                mode: 'edit',
            }));
        }

        return Promise.all(proms);
    },
});

// /** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { DocumentsInspector } from "@documents/views/inspector/documents_inspector";
// import { patch } from "@web/core/utils/patch";
// import { useState } from "@odoo/owl";

// const TAGS_SEARCH_LIMIT = 8;

// patch(DocumentsInspector.prototype, {
//     setup() {
//         this._super();
//         this.state = useState({
//             abc: true
//         });
//     },

//     async _renderFields() {
//         const options = { mode: 'edit' };
//         const proms = [];

//         if (this.records.length === 1) {
//             proms.push(this._renderField('name', options));
            
//             if (this.records[0].data.type === 'url') {
//                 proms.push(this._renderField('url', options));
//             }
            
//             proms.push(this._renderField('partner_id', options));
//             const record = this.records[0];
            
//             if (this.state.abc) {
//                 proms.push(this._renderField('team_id', options));
//             }
//         }

//         if (this.records.length > 0) {
//             proms.push(this._renderField('owner_id', options));
//             proms.push(this._renderField('folder_id', {
//                 icon: 'fa fa-folder o_documents_folder_color',
//                 mode: 'edit',
//             }));
//         }

//         return Promise.all(proms);
//     },
// });