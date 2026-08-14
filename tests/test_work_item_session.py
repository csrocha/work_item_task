# -*- coding: utf-8 -*-
"""BACKLOG.md (work_item_systray) ítem 2.2/2.3/2.4:
_get_switchable_work_items debe mostrar las tareas de hoy primero, el
resto ordenado por prioridad, y sin duplicados. Se prueba acá (no en
work_item_systray) porque ese módulo base no depende de ningún proveedor
real -- project.task (este módulo) es el proveedor usado para probar la
agregación. Los candidatos se mockean para no depender de en qué día de
la semana corre el test ni de qué otros proveedores estén instalados."""
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestWorkItemSessionAggregation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.session = cls.env['work.item.session']._get_or_create_for_user()
        cls.today_str = fields.Date.to_string(fields.Date.context_today(cls.session))

    def _aggregate(self, candidates):
        Session = type(self.session)
        Task = type(self.env['project.task'])
        with patch.object(Session, '_get_work_item_provider_models', return_value=['project.task']), \
                patch.object(Task, '_work_item_candidates', return_value=candidates):
            return self.session._get_switchable_work_items()

    def test_today_items_come_before_the_rest(self):
        items = self._aggregate([
            {'res_id': 1, 'name': 'Después', 'priority': '0', 'date_deadline': '2999-01-02'},
            {'res_id': 2, 'name': 'Hoy', 'priority': '0', 'date_deadline': self.today_str},
        ])
        self.assertEqual([i['res_id'] for i in items], [2, 1])

    def test_within_a_group_higher_priority_comes_first(self):
        items = self._aggregate([
            {'res_id': 1, 'name': 'Baja', 'priority': '0', 'date_deadline': False},
            {'res_id': 2, 'name': 'Alta', 'priority': '1', 'date_deadline': False},
        ])
        self.assertEqual([i['res_id'] for i in items], [2, 1])

    def test_duplicate_model_and_res_id_kept_once(self):
        items = self._aggregate([
            {'res_id': 1, 'name': 'Repetida', 'priority': '0', 'date_deadline': False},
            {'res_id': 1, 'name': 'Repetida', 'priority': '0', 'date_deadline': False},
        ])
        self.assertEqual(len(items), 1)


class TestPomodoro(TransactionCase):
    """BACKLOG.md (work_item_systray) ítem 3: período activo de 25' +
    5' de gracia titilando + cierre automático (ver
    work_item_systray/models/work_item_session.py: pomodoro_deadline,
    confirm_pomodoro, _cron_close_expired_pomodoros). Se prueba acá (no
    en work_item_systray) por el mismo motivo que la agregación de
    arriba: hace falta un proveedor real instalado, project.task no
    rompe _work_item_close sin hr.employee para el usuario de test (hace
    return temprano), así que no hace falta fixture de timesheets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task = cls.env['project.task'].create({'name': 'Pomodoro Task'})
        cls.session = cls.env['work.item.session']._get_or_create_for_user()

    def test_switch_work_item_sets_pomodoro_deadline(self):
        self.session.switch_work_item('project.task', self.task.id)
        expected = self.session.start_datetime + timedelta(minutes=25)
        self.assertAlmostEqual(
            self.session.pomodoro_deadline, expected, delta=timedelta(seconds=5),
        )

    def test_take_break_clears_pomodoro_deadline(self):
        self.session.switch_work_item('project.task', self.task.id)
        self.session.take_break()
        self.assertFalse(self.session.pomodoro_deadline)

    def test_confirm_pomodoro_pushes_deadline_without_touching_start(self):
        self.session.switch_work_item('project.task', self.task.id)
        start_datetime = self.session.start_datetime
        self.session.confirm_pomodoro()
        self.assertEqual(self.session.start_datetime, start_datetime)
        expected = fields.Datetime.now() + timedelta(minutes=25)
        self.assertAlmostEqual(
            self.session.pomodoro_deadline, expected, delta=timedelta(seconds=5),
        )

    def test_confirm_pomodoro_noop_when_not_active(self):
        self.session.take_break()
        self.session.confirm_pomodoro()
        self.assertFalse(self.session.pomodoro_deadline)

    def test_cron_closes_expired_pomodoro(self):
        self.session.switch_work_item('project.task', self.task.id)
        self.session.pomodoro_deadline = fields.Datetime.now() - timedelta(minutes=6)
        self.env['work.item.session']._cron_close_expired_pomodoros()
        self.assertEqual(self.session.state, 'break')
        self.assertFalse(self.session.work_item_ref)
        self.assertFalse(self.session.pomodoro_deadline)

    def test_cron_does_not_close_within_grace(self):
        self.session.switch_work_item('project.task', self.task.id)
        self.session.pomodoro_deadline = fields.Datetime.now() - timedelta(minutes=2)
        self.env['work.item.session']._cron_close_expired_pomodoros()
        self.assertEqual(self.session.state, 'active')
