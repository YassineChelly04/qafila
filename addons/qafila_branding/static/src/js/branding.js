/** @odoo-module **/
// Qafila — titre de l'onglet et menu utilisateur sans références Odoo.com
import { registry } from "@web/core/registry";

const APP_NAME = "Qafila";

const qafilaTitleService = {
    start() {
        const titleCounters = {};
        const titleParts = {};
        function updateTitle() {
            const counter = Object.values(titleCounters).reduce((acc, count) => acc + count, 0);
            const parts = Object.values(titleParts);
            const name = parts.length ? `${parts.join(" - ")} · ${APP_NAME}` : APP_NAME;
            document.title = counter ? `(${counter}) ${name}` : name;
        }
        function assign(target, values) {
            for (const key in values) {
                if (!values[key]) {
                    delete target[key];
                } else {
                    target[key] = values[key];
                }
            }
            updateTitle();
        }
        updateTitle();
        return {
            get current() {
                return document.title;
            },
            getParts: () => Object.assign({}, titleParts),
            setCounters: (counters) => assign(titleCounters, counters),
            setParts: (parts) => assign(titleParts, parts),
        };
    },
};
registry.category("services").add("title", qafilaTitleService, { force: true });

const userMenu = registry.category("user_menuitems");
for (const key of ["documentation", "support", "odoo_account", "install_pwa"]) {
    if (userMenu.contains(key)) {
        userMenu.remove(key);
    }
}
