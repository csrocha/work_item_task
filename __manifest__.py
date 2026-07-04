# -*- coding: utf-8 -*-
{
    'name': "Work Item Systray — Tasks",
    'summary': "Habilita project.task como work item trabajable desde el Work Item Systray",
    'version': '17.0.3.0.0',
    'category': 'Productivity',
    'author': "Cristian S. Rocha <csrocha@gmail.com>",
    'website': "https://github.com/csrocha/work_item_task",
    'license': 'OPL-1',
    'depends': ['work_item_systray', 'project_improve', 'project', 'hr_timesheet', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'security/work_item_task_session_security.xml',
        'data/work_item_task_message_templates.xml',
        'views/project_task_views.xml',
        'views/work_item_session_switch_wizard_views.xml',
        'views/work_item_message_template_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'work_item_task/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
