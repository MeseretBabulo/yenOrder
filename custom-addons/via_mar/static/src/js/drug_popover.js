/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useCalendarPopover } from "@web/views/calendar/hooks";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

patch(useCalendarPopover, {
    setup() {
        this._super();
        this.state = useState({
            drugComment: "",
            initialsId: false
        });
        this.orm = useService("orm");
        this.action = useService("action");
    },

    async _onClickAddDrug(ev) {
        ev.preventDefault();
        const val = ev.target.closest('form').querySelector("input[name='drug_comment']").value;
        const initialId = ev.target.closest('form').querySelector("select[name='initials_s']").value;
        
        await this.orm.call(
            'drug.doses.schedule',
            'add_dose_line',
            [parseInt(this.props.record.id), val, initialId]
        );
        
        await this.action.doAction('reload');
    },

    async _onClickSaveDrug(ev) {
        ev.preventDefault();
        const form = ev.target.closest('form');
        const val = form.querySelector("input[name='drug_comment']").value;
        const initial = form.querySelector("select[name='initials_s']").value;
        
        const writeValues = {
            comment: val,
            initials_id: initial || false
        };

        await this.orm.write(
            'drug.doses.schedule',
            [parseInt(this.props.record.id)],
            writeValues
        );
        
        await this.action.doAction('reload');
    },

    _isShowDrugDoseButton() {
        return this.props.record.is_dose_added || false;
    }
});