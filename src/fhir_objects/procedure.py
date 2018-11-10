from .fhir_resources import procedure_resources
from .fhir_base_object import FHIRBaseObject

import datetime as dt


class Procedure(FHIRBaseObject):

    def __init__(self, **kwargs):
        resource_dict = kwargs['resource_dict']
        if resource_dict['resourceType'] != 'Procedure':
            raise ValueError("Can not generate a Procedure from {}".format(
                resource_dict['resourceType']))

        kwargs['fhir_resources'] = procedure_resources
        super().__init__(**kwargs)

    def __str__(self):
        if self.name:
            name_list = self._dict['name']
            return str(name_list)
        else:
            return "Procedure has no name attribute."
