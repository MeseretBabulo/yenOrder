/** @odoo-module **/
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";

class KanbanButton extends KanbanController {
    setup() {
        super.setup();
    }

    async openWizardKanban() {
        return this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'create.project.task.wizard',
            name: 'Create Project Task',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: { 'default_project_id': parseInt(this.env.searchModel.context.default_project_id) }
        });
    }
}

KanbanButton.template = 'ks_project_task.buttons';
KanbanButton.components = {
    ...KanbanController.components
};

export const buttonInKanbanView = {
    ...kanbanView,
    Controller: KanbanButton,
};

registry.category("views").add("button_in_kanban", buttonInKanbanView);