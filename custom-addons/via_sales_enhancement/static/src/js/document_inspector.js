/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


export class EnhancedDocumentsInspector extends Component {
    static template = 'via_sales_enhancement.EnhancedDocumentsInspector';

    setup() {
        this.orm = useService('orm');
        this.state = {
            records: this.props.records || [],
        };
    }

    async _renderFields() {
        console.log('test========', this);
        const options = { mode: 'edit' };
        const proms = [];

        if (this.state.records.length === 1) {
            proms.push(this._renderField('name', options));
            if (this.state.records[0].data.type === 'url') {
                proms.push(this._renderField('url', options));
            }
            proms.push(this._renderField('partner_id', options));

            const record = this.state.records[0];
            if (record.data.res_model !== 'sale.order') {
                proms.push(this._renderField('sale_id', options));
            }
        }

        if (this.state.records.length > 0) {
            proms.push(this._renderField('owner_id', options));
            proms.push(this._renderField('folder_id', {
                icon: 'fa fa-folder o_documents_folder_color',
                mode: 'edit',
            }));
        }

        return Promise.all(proms);
    }

    // Render method to call _renderFields and manage the output
    async render() {
        await this._renderFields();
    }
}

// Registering the new component as a view widget
registry.category("view_widgets").add("enhanced_documents_inspector", {
    component: EnhancedDocumentsInspector,
});
















// odoo.define('via_sales_enhancement.document_inspector', function (require) {
// "use strict";
// /**
//  * This file defines the DocumentsInspector Widget, which is displayed next to
//  * the KanbanRenderer in the DocumentsKanbanView.
//  */
// var core = require('web.core');
// var fieldRegistry = require('web.field_registry');
// var session = require('web.session');
// var dialogs = require('web.view_dialogs');
// var Widget = require('web.Widget');
// var DocumentsInspector = require('documents.DocumentsInspector');
// var _t = core._t;
// var qweb = core.qweb;
// var TAGS_SEARCH_LIMIT = 8;
// var DocumentsInspector1 = DocumentsInspector.include({
//     _renderFields: function () {
//         console.log('test========', this)
//         var options = {mode: 'edit'};
//         var proms = [];
//         if (this.records.length === 1) {
//             proms.push(this._renderField('name', options));
//             if (this.records[0].data.type === 'url') {
//                 proms.push(this._renderField('url', options));
//             }
//             proms.push(this._renderField('partner_id', options));
//             const record = this.records[0];
//             if(record.data.res_model != 'sale.order'){
//                 proms.push(this._renderField('sale_id', options));
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
// })
// })