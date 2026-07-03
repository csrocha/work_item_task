/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { WorkItemSystrayItem } from "@work_item_systray/components/work_item_systray/work_item_systray";

patch(WorkItemSystrayItem.prototype, {
    /**
     * Las tareas con allocated_hours cuentan hacia atrás el presupuesto
     * restante, coloreado según cuánto queda; cualquier otro work item
     * (incluidos tickets) sigue el comportamiento ascendente del base.
     */
    _tick() {
        const extra = this.state.extra || {};
        if (this.state.workItemModel !== "project.task" || !extra.allocated_hours) {
            super._tick();
            return;
        }
        if (this.state.status !== "active" || !this.state.startDatetime) {
            this.state.elapsed = "00:00:00";
            this.state.timeColorClass = "o_work_item_time-neutral";
            return;
        }
        const start = new Date(this.state.startDatetime.replace(" ", "T") + "Z");
        const liveSeconds = Math.max(0, Math.floor((Date.now() - start.getTime()) / 1000));
        const allocatedSeconds = extra.allocated_hours * 3600;
        const remainingSeconds = (extra.remaining_hours || 0) * 3600 - liveSeconds;
        this.state.elapsed = this._formatDuration(remainingSeconds);
        this.state.timeColorClass = this._colorClass(remainingSeconds, allocatedSeconds);
    },

    _colorClass(remainingSeconds, allocatedSeconds) {
        if (remainingSeconds < 0) {
            return "o_work_item_time-overtime";
        }
        const ratio = allocatedSeconds > 0 ? remainingSeconds / allocatedSeconds : 0;
        if (ratio >= 0.5) {
            return "o_work_item_time-ok";
        }
        if (ratio >= 0.15) {
            return "o_work_item_time-warning";
        }
        return "o_work_item_time-critical";
    },
});
