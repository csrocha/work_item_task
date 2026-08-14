# -*- coding: utf-8 -*-
"""BACKLOG.md (work_item_systray) ítem 2.1: el systray debía mostrar
también las tareas sin proyecto asignado. La búsqueda de candidatos
(_work_item_search_week_tasks) nunca filtró por project_id -- este test
fija ese comportamiento como contrato. De paso confirma que el candidato
lleva priority/date_deadline, que _get_switchable_work_items necesita para
ordenar (ítem 2.4) y separar las tareas de hoy (ítem 2.2)."""
from odoo import fields
from odoo.tests.common import TransactionCase


class TestWorkItemCandidates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task_no_project = cls.env['project.task'].create({
            'name': 'Sin proyecto',
            'project_id': False,
            'user_ids': [(6, 0, [cls.env.uid])],
            'date_deadline': fields.Datetime.now(),
            'priority': '1',
        })

    def test_candidates_include_tasks_without_project(self):
        res_ids = {c['res_id'] for c in self.env['project.task']._work_item_candidates()}
        self.assertIn(self.task_no_project.id, res_ids)

    def test_candidate_carries_priority_and_date_deadline(self):
        by_id = {c['res_id']: c for c in self.env['project.task']._work_item_candidates()}
        candidate = by_id[self.task_no_project.id]
        self.assertEqual(candidate['priority'], '1')
        self.assertEqual(
            candidate['date_deadline'],
            fields.Date.to_string(self.task_no_project.date_deadline.date()),
        )
