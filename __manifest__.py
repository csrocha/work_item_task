# -*- coding: utf-8 -*-
{
    'name': "Work Item Systray — Tasks",
    'summary': "Habilita project.task como work item trabajable desde el Work Item Systray",
    'version': '17.0.1.0.1',
    'category': 'Productivity',
    'author': "Cristian S. Rocha <csrocha@gmail.com>",
    'website': "https://github.com/csrocha/work_item_task",
    'license': 'OPL-1',
    'depends': ['work_item_systray', 'project', 'hr_timesheet'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'work_item_task/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
