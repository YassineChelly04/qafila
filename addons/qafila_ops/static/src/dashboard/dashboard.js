/** @odoo-module **/
// Qafila — tableau d'exploitation (action client « qafila_dashboard »)
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Carte des statuts, identique partout (pastilles, barre de flotte, légendes)
const LEVEL_LABEL = { critical: "Urgent", warning: "À surveiller", info: "Info" };

export class QafilaDashboard extends Component {
    static template = "qafila_ops.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.levelLabel = LEVEL_LABEL;
        this.state = useState({ data: null, loading: true, error: false, tip: null });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.error = false;
        try {
            this.state.data = await this.orm.call("qafila.dashboard", "get_data", []);
        } catch {
            this.state.error = true;
        } finally {
            this.state.loading = false;
        }
    }

    run(act) {
        if (act) {
            this.action.doAction(act);
        }
    }

    open(key) {
        this.run(this.state.data?.actions[key]);
    }

    openRecord(model, id) {
        this.run({ type: "ir.actions.act_window", res_model: model, res_id: id, views: [[false, "form"]], target: "current" });
    }

    openClientInvoices(row) {
        this.run({
            type: "ir.actions.act_window",
            name: `Factures — ${row.name}`,
            res_model: "account.move",
            domain: [["move_type", "=", "out_invoice"], ["state", "=", "posted"], ["partner_id.commercial_partner_id", "=", row.id]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    showTip(ev, row) {
        const box = ev.currentTarget.closest(".qf-bars").getBoundingClientRect();
        this.state.tip = { text: `${row.name} · ${row.label} HT · ${row.share} du CA`, x: ev.clientX - box.left, y: ev.clientY - box.top };
    }

    hideTip() {
        this.state.tip = null;
    }

    get tipStyle() {
        const t = this.state.tip;
        return t ? `left:${t.x + 12}px;top:${t.y - 34}px` : "";
    }
}

registry.category("actions").add("qafila_dashboard", QafilaDashboard);
