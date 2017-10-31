# -*- coding: utf-8 -*-
{
    'name': "Leaf Backend",
    'author': "Simbioz, Yury Stasovsky",
    'license': 'LGPL-3',
    'website' : "https://coraltree.co",
    'category': 'Custom integration',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['sale'],
#    'depends': ['sale', 'purchase', 'mrp', 'sce'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        #'security/groups.xml',
       # 'wizard/wiz_view.xml',
        'views/area.xml',
        'views/menu.xml',
    ],
    'installable': True,
}
