/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TimesheetCheckInOut } from "./js/timesheet_buttons";

registry.category("actions").add("timesheet_check_in_out", TimesheetCheckInOut);
