# -*- coding: utf-8 -*-
import re
from datetime import datetime, time, timedelta
from html import unescape

from odoo import _, api, fields, models

_TAG_RE = re.compile(r'<[^>]+>')
_SPACE_RE = re.compile(r'\s+')


def _html_to_text(html_value, max_len=280):
    if not html_value:
        return ''
    text = unescape(_TAG_RE.sub(' ', html_value))
    text = _SPACE_RE.sub(' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + '…'
    return text


class ProjectTask(models.Model):
    _inherit = 'project.task'
    _work_item_provider = True

    def _work_item_label(self):
        self.ensure_one()
        icon, css_class = self._work_item_icon()
        return {
            'name': self.name,
            'icon': icon,
            'css_class': css_class,
            'description': _html_to_text(self.description),
            'allocated_hours': self.allocated_hours,
            'remaining_hours': self.remaining_hours,
        }

    def _work_item_icon(self):
        """⚡ camino crítico / ❗ revisión pendiente. is_critical_path es un
        campo genérico de project_improve (queda en False sin un motor de
        scheduling que lo compute); state/'02_changes_requested' ya es
        nativo de project, no hace falta ningún addon extra para esto."""
        self.ensure_one()
        if self.is_critical_path:
            return '⚡', 'text-danger fw-bold'
        if self.state == '02_changes_requested':
            return '❗', 'text-warning fw-bold'
        return '', ''

    def _work_item_close(self, start_datetime, intent_note, outcome_note, outcome_blocked):
        """Registra el tiempo trabajado como account.analytic.line,
        combinando la nota de inicio ('qué se iba a hacer') con la de cierre
        ('qué se logró'), y aplica blocked = True si corresponde."""
        self.ensure_one()
        if outcome_blocked:
            self.blocked = True
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1
        )
        if not employee:
            return
        duration = self._work_item_elapsed_hours(start_datetime)
        if duration <= 0:
            return
        self.env['account.analytic.line'].sudo().create({
            'name': self._work_item_compose_analytic_name(intent_note, outcome_note),
            'project_id': self.project_id.id,
            'task_id': self.id,
            'employee_id': employee.id,
            'unit_amount': duration,
            'date': start_datetime.date(),
        })

    def _work_item_elapsed_hours(self, start_datetime):
        """Horas trabajadas desde el inicio del período. Punto de extensión:
        work_item_enterprise_task lo pisa para usar el timer.timer nativo
        (que contempla pausas) en vez de la resta simple contra 'ahora'."""
        self.ensure_one()
        return (fields.Datetime.now() - start_datetime).total_seconds() / 3600.0

    def _work_item_compose_analytic_name(self, intent_note, outcome_note):
        self.ensure_one()
        if not intent_note and not outcome_note:
            return self.name or _('Trabajo registrado')
        parts = []
        if intent_note:
            parts.append(_('Se quiso hacer: %s.') % intent_note)
        if outcome_note:
            parts.append(_('Se logró: %s.') % outcome_note)
        return ' '.join(parts)

    @api.model
    def _work_item_candidates(self):
        """Mis tareas vigentes esta semana (lunes → domingo); si no hay
        ninguna, las vigentes la próxima semana completa. 'Vigente' = no
        terminada y con date_deadline dentro de la ventana."""
        today = fields.Date.context_today(self)
        this_monday = today - timedelta(days=today.weekday())
        this_sunday = this_monday + timedelta(days=6)
        tasks = self._work_item_search_week_tasks(this_monday, this_sunday)
        if not tasks:
            next_monday = this_monday + timedelta(days=7)
            next_sunday = next_monday + timedelta(days=6)
            tasks = self._work_item_search_week_tasks(next_monday, next_sunday)
        return [{
            'res_id': t.id,
            'name': t.name,
            'icon': t._work_item_icon()[0],
            'css_class': t._work_item_icon()[1],
        } for t in tasks]

    def _work_item_search_week_tasks(self, date_from, date_to):
        return self.search([
            ('user_ids', 'in', self.env.uid),
            ('state', 'not in', ['1_done', '1_canceled']),
            ('date_deadline', '>=', datetime.combine(date_from, time.min)),
            ('date_deadline', '<=', datetime.combine(date_to, time.max)),
        ]).sorted(key=lambda t: t.date_deadline)

    def action_switch_to_session(self):
        """Activa esta tarea en la sesión del systray del usuario actual."""
        self.ensure_one()
        self.env['work.item.session'].action_switch_work_item('project.task', self.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tarea activada'),
                'message': _('Ahora estás trabajando en "%s".') % self.name,
                'type': 'success',
                'sticky': False,
            },
        }
