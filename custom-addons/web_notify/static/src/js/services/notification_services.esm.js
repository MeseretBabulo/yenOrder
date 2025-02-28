/** @odoo-module **/
import {Markup} from "web.utils";
import {browser} from "@web/core/browser/browser";
import {registry} from "@web/core/registry";

/**
 * @typedef {Object} NotificationButton
 * @property {string} name
 * @property {string} [icon]
 * @property {boolean} [primary=false]
 * @property {function(): void} onClick
 *
 * @typedef {Object} NotificationOptions
 * @property {string} [title]
 * @property {"warning" | "danger" | "success" | "info"} [type]
 * @property {boolean} [sticky=false]
 * @property {string} [className]
 * @property {function(): void} [onClose]
 * @property {NotificationButton[]} [buttons]
 */


export const webNotificationService = {
    dependencies: ["bus_service", "notification"],

    start(env, {bus_service, notification}) {
        let webNotifTimeouts = {};
        let notifId = 0;
        /**
         * Displays the web notification on user's screen
         */




        function displaywebNotification(notifications) {
            console.log("time out",notifications)
            Object.values(webNotifTimeouts).forEach((notif) =>
                browser.clearTimeout(notif)
            );
            webNotifTimeouts = 20000;

            notifications.forEach(function (notif) {
                browser.setTimeout(function () {
                    notification.cutom_add(Markup(notif.message), {
                        title: notif.title,
                        type: notif.type,
                        sticky: notif.sticky,
                        className: notif.className,
                    });
                });
            });

           function add(message, options = {})  {
            console.log("////////////////////////// fun", Object)
            const id = ++notifId;
            const closeFn = () => close(id);close
            const props = Object.assign({}, options, { message, close: closeFn });
            const sticky = props.sticky;
            delete props.sticky;
            delete props.onClose;
            const notification = {
                id,
                props,
                onClose: options.onClose,
            };
            notifications[id] = notification;
            if (!sticky) {
                console.log("close")
                browser.setTimeout(closeFn, 4000);
            }
            return closeFn;notifications
        }
        }

        bus_service.addEventListener("notification", ({detail: notifications}) => {
            console.log("custom module",notifications)
            const AUTOCLOSE_DELAY = 10000;
            for (const {payload, type} of notifications) {
                if (type === "web.notify") {
                    displaywebNotification(payload);
                }
            }
        });
        bus_service.start();
    },
};

registry.category("services").add("webNotification", webNotificationService);
