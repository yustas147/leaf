# -*- coding: utf-8 -*-

import logging
import xmlrpclib
from openerp import models, fields
#from openerp.addons.connector.queue.job import job
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )
from openerp.addons.connector.exception import IDMissingInBackend
from ..unit.backend_adapter import (GenericAdapter)
#from ..unit.import_synchronizer import (DelayedBatchImporter,  WooImporter)
from ..unit.import_synchronizer import (DelayedBatchImporter, DirectBatchImporter, WooImporter)
from ..unit.binder import WooModelBinder
#from ..unit.export_synchronizer import  WooExporter
from ..connector import get_environment
from ..backend import woo
from openerp.addons.connector.event import on_record_write
#from openerp.addons.connector.unit.synchronizer import Importer, Exporter

_logger = logging.getLogger(__name__)


class WooArea(models.Model):
#class WooResPartner(models.Model):
    _name = 'woo.leaf.area'
#    _name = 'woo.res.partner'
    _inherit = 'woo.binding'
#    _inherits = {'res.partner': 'openerp_id'}
    _inherits = {'leaf.area': 'openerp_id'}
    _description = 'woo leaf area'
#    _description = 'woo res partner'

    _rec_name = 'name'

    #openerp_id = fields.Many2one(comodel_name='res.partner',
                                 #string='Partner',
                                 #required=True,
                                 #ondelete='cascade')
    openerp_id = fields.Many2one(comodel_name='leaf.area',
                                 string='Area',
                                 required=True,
                                 ondelete='cascade')
    #backend_id = fields.Many2one(
        #comodel_name='wc.backend',
        #string='Woo Backend',
        #store=True,
        #readonly=False,
    #)


class Area(models.Model):
    _inherit = 'leaf.area' 
    
    woo_ids = fields.One2many(comodel_name='woo.leaf.area', inverse_name='openerp_id', 
                             string='Woo bindings')

@woo
class AreaAdapter(GenericAdapter):
    _model_name = 'woo.leaf.area'
    _woo_model = 'areas'

    #yustas
    def write(self, data):
        try:
            return super(AreaAdapter, self).write(data)
        except xmlrpclib.Fault as err:
            # this is the error in the WooCommerce API
            # when the customer does not exist
            if err.faultCode == 102:
                raise IDMissingInBackend
            else:
                raise
    
    def _call(self, method, arguments):
        try:
            return super(AreaAdapter, self)._call(method, arguments)
#            return super(CustomerAdapter, self)._call(method, arguments)
        except xmlrpclib.Fault as err:
            # this is the error in the WooCommerce API
            # when the customer does not exist
            if err.faultCode == 102:
                raise IDMissingInBackend
            else:
                raise

    def search(self, filters=None, from_date=None, to_date=None):
        """ Search records according to some criteria and return a
        list of ids

        :rtype: list
        """
        if filters is None:
            filters = {}
        WOO_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'
        dt_fmt = WOO_DATETIME_FORMAT
        if from_date is not None:
            # updated_at include the created records
            filters.setdefault('updated_at', {})
            filters['updated_at']['from'] = from_date.strftime(dt_fmt)
        if to_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['to'] = to_date.strftime(dt_fmt)
        # the search method is on ol_customer instead of customer
        return self._call('areas',
#        return self._call('customers/list',
                          [filters] if filters else [{}])
    

@woo
class AreaBatchImporter(DirectBatchImporter):
#class AreaBatchImporter(DelayedBatchImporter):

    """ Import the WooCommerce Partners.

    For every partner in the list, a delayed job is created.
    """
    _model_name = ['woo.leaf.area']
    
    #yustas
    _records = []

    def _import_record(self, record, priority=None):
#    def _import_record(self, woo_id, priority=None):
        """ Delay a job for the import """
        super(AreaBatchImporter, self)._import_record(
            record)
    #        woo_id)
#            woo_id, priority=priority)

    def run(self, filters=None):
        """ Run the synchronization """
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        
        record_ids = [ x['global_id'] for x in self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
        )['data']]
        
        self._records =  self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
        )['data']
        
#         record_ids = self.env['wc.backend'].get_customer_ids(record_ids)
        _logger.info('search for woo areas %s returned %s',
                     filters, self._records)
#                     filters, record_ids)

       # for record_id in record_ids:
        for record in self._records:
            self._import_record(record)
#            self._import_record(record_id, 40)

AreaBatchImporter = AreaBatchImporter  # deprecated

        #""" Run the synchronization """
        #from_date = filters.pop('from_date', None)
        #to_date = filters.pop('to_date', None)
        #record_ids = self.backend_adapter.search(
            #filters,
            #from_date=from_date,
            #to_date=to_date,
        #)
##         record_ids = self.env['wc.backend'].get_customer_ids(record_ids)
        #_logger.info('search for woo partners %s returned %s',
                     #filters, record_ids)

#CustomerBatchImporter = CustomerBatchImporter  # deprecated


@woo
class AreaImporter(WooImporter):
    _model_name = ['woo.leaf.area']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        return

    def _create(self, data):
        openerp_binding = super(AreaImporter, self)._create(data)
        return openerp_binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

AreaImporter = AreaImporter  # deprecated


@woo
class AreaExporter(Exporter):
    _model_name = ['woo.leaf.area']
    
    def _export_area(self, data):
        return self.backend_adapter.write(data)

    def _get_data(self, record, fields):
        result = {}
        result.update({'global_id': record.global_id})
        
        for fld in AREA_FIELDS:
            if fld in fields:
                if fld == 'a_type':
                    fld = 'type'
                    result.update({ fld: getattr(record, 'a_type')})
                    continue
                result.update({ fld: getattr(record, fld)})
        return result    

    def run(self, record_id, fields):
        record = self.model.browse(record_id)
        data = self._get_data(record, fields)

        try:
            export_res = self._export_area(data)
            
        except xmlrpclib.Fault as err:
            # When the invoice is already created on Magento, it returns:
            # <Fault 102: 'Cannot do invoice for order.'>
            # We'll search the Magento invoice ID to store it in OpenERP
            if err.faultCode == 102:
                _logger.debug('Invoice already exists on Magento for '
                              'sale order with magento id %s, trying to find '
                              'the invoice id.',
                              magento_order.magento_id)
                magento_id = self._get_existing_invoice(magento_order)
                if magento_id is None:
                    # In that case, we let the exception bubble up so
                    # the user is informed of the 102 error.
                    # We couldn't find the invoice supposedly existing
                    # so an investigation may be necessary.
                    raise
            else:
                raise

AreaExporter = AreaExporter  # deprecated

@woo
class AreaImportMapper(ImportMapper):
    _model_name = 'woo.leaf.area'
    direct = [('name', 'name'), ('global_id', 'global_id'),('external_id','external_id'),('type','a_type')]
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}    

#@woo
#class AreaExportMapper(ExportMapper):
    #_model_name = 'woo.leaf.area'
    #direct = [('name', 'name'), ('global_id', 'global_id'),('external_id','external_id'),('type','a_type')]

@job(default_channel='root.woo')
def area_import_batch_bak(session, model_name, backend_id, filters=None):
    """ Prepare the import of Customer """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(AreaBatchImporter)
#    importer = env.get_connector_unit(CustomerBatchImporter)
    importer.run(filters=filters)
    
def area_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of Area """
    
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(AreaBatchImporter)
    importer.run(filters=filters)
    
###############################
    
AREA_FIELDS = ('name',
               'external_id',
               'a_type'
                             )
#woombinder = WooModelBinder()
    
@on_record_write(model_names='leaf.area')
#@on_record_write(model_names='woo.leaf.area')
def woo_leaf_area_modified(session, model_name, record_id, vals):
#def magento_product_modified(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    fields_to_export = list(set(vals).intersection(AREA_FIELDS))
    if fields_to_export:
        export_leaf_area(session, model_name, record_id, fields=AREA_FIELDS)
                                       #record_id, fields=inventory_fields,
                                       #priority=20)


#@job(default_channel='root.magento')
#@related_action(action=unwrap_binding)
def export_leaf_area(session, model_name, record_id, fields=None):
#def export_product_inventory(session, model_name, record_id, fields=None):
    #b_id = woombinder.to_backend(record_id)
    aenv = session.env['woo.leaf.area']
    area = aenv.search([('openerp_id','=', record_id)])
    area = area[0]
#    area = session.env[model_name].browse(record_id)
    backend_id = area.backend_id.id
#    backend_id = product.backend_id.id
    env = get_environment(session, 'woo.leaf.area', backend_id)
#    env = get_environment(session, model_name, backend_id)
    area_exporter = env.get_connector_unit(AreaExporter)
#    inventory_exporter = env.get_connector_unit(ProductInventoryExporter)
    return area_exporter.run(record_id, fields)
#    return inventory_exporter.run(record_id, fields)

    
    