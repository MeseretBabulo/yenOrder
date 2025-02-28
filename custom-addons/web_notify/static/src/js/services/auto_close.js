/** @odoo-module **/

import { notificationService as BaseNotificationService } from 'path/to/base/notification_service';

export const notificationService = Object.assign({}, BaseNotificationService, {
    start() {
        const baseService = BaseNotificationService.start();
        const customAUTOCLOSE_DELAY = 6000; // Custom autoclose delay in milliseconds

        // Override the AUTOCLOSE_DELAY constant
        const AUTOCLOSE_DELAY = customAUTOCLOSE_DELAY;

        // Return the modified service
        return Object.assign({}, baseService, { AUTOCLOSE_DELAY });
    },
});