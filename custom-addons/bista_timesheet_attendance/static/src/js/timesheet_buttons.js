/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { xml } from "@odoo/owl";

export class TimesheetCheckInOut extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            task_id: null,  // Assume you fetch the task dynamically
        });
    }

    async checkInOut(type) {
        if (!this.state.task_id) {
            this.displayNotification({
                type: "warning",
                message: "No active task found.",
            });
            return;
        }

        const { error, message } = await this.rpc("/timesheet/location_check_in_out", {
            type: type,
            latitude: 9.145,  // Example, replace with actual coordinates
            longitude: 40.489,
        });

        if (error) {
            this.displayNotification({ type: "danger", message: error });
        } else {
            this.displayNotification({ type: "success", message });
        }
    }
}
TimesheetCheckInOut.template = xml`
    <TimesheetCheckInOutButtons/>
`;
