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
        return {
            'name': self.name,
            'icon': '',
            'css_class': '',
            'description': _html_to_text(self.description),
            'allocated_hours': self.allocated_hours,
            'remaining_hours': self.remaining_hours,
        }

    def _work_item_close(self, start_datetime, intent_note, outcome_note, outcome_blocked):
        """Registra el tiempo trabajado como account.analytic.line,
        combinando la nota de inicio ('qué se iba a hacer') con la de cierre
        ('qué se logró')."""
        self.ensure_one()
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1
        )
        if not employee:
            return
        duration = (fields.Datetime.now() - start_datetime).total_seconds() / 3600.0
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
            'icon': '',
            'css_class': '',
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
