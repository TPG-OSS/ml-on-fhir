import requests
from fhir_objects.patient import Patient
from fhir_objects.condition import Condition
from fhir_objects.observation import Observation
from fhir_objects.procedure import Procedure

from os.path import join
import logging
from typing import Callable


class FHIRClient():

    def __init__(self, service_base_url: str):
        """
        Helper class to perform requests to a FHIR server.

        Attributes:
            server_url (str): Base url to be used for all requests (e.g. http://localhost:8080/baseR4)
        """
        self.server_url = service_base_url
        self.session = requests.Session()

    def _check_status(self, status_code: int):
        """
        Checks whether returned status code is 200

        Returns:
            True if status_code is OK (200), False otherwise
        """
        return status_code == requests.codes.ok

    def _build_url(self, path: str, **query_params):
        """
        Builds an url based on the class's server_url and query parameters

        Args:
            path (str): FHIR resource to be queried (e.g. Patient or Observation)
            **query_params: Dict of query parameters to build the query string
        """
        base_url = join(self.server_url, path)
        if query_params:
            base_url += '?'

        for param in query_params.keys():
            if query_params[param]:
                base_url += '{}={}&'.format(param, query_params[param])
        return base_url

    def _get(self, path: str, session: requests.Session=None, **query_params):
        """
        Builds the query string and submits a GET request

        Args:
            path (str): FHIR resource to be queried (e.g. Patient or Observation)
            session (requests.Session): Session to be used for query
            **query_params: Dict of query parameters to build the query string

        Returns:
            The requests.Response
        """
        url = self._build_url(path, **query_params)
        if session:
            return session.get(url)
        else:
            return requests.get(url)

    def _collect(self, result_json: dict, session: requests.Session, constructor: Callable):
        """
        A server might return a pageinated result due to its settings.
        This method collects all results recursively. 

        Args:
            result_json (dict): The json result from the initial query
            session (requests.Session): Session to be used for all requests
            constructor (Callable): The constructor with which to construct the result list

        Returns:
            A list of objects generated by the constructor. E.g. a list of Patient objects.
        """
        result = []
        for link in result_json['link']:
            if link['relation'] == 'next':
                r = session.get(link['url'])
                if self._check_status(r.status_code):
                    result = self._collect(r.json(), session, constructor)
                else:
                    r.raise_for_status()
            else:
                continue
        if 'entry' in result_json.keys():
            result += [constructor(resource_dict=d['resource'], fhir_client=self) for d in result_json['entry'] if d[
                'resource']['resourceType'] == constructor.__name__]
        return result

    def get_capability_statement(self):
        """
        Returns:
            The capability statement of the FHIR server. 
        """
        r = self._get('metadata')

        if self._check_status(r.status_code):
            return r.json()
        else:
            r.raise_for_status()

    def get_all_patients(self, max_count=1000):
        """
        Gets a all patients

        Returns:
            List of fhir_objects.Patient.patient
        """
        r = self._get('Patient', session=self.session)

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Patient)
        else:
            r.raise_for_status()

    def get_all_conditions(self):
        """
        Gets all conditions

        Returns:
            List of fhir_objects.Condition.condition
        """
        r = self._get('Condition', session=self.session)

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Condition)
        else:
            r.raise_for_status()

    def get_all_observations(self):
        """
        Gets all conditions

        Returns:
            List of fhir_objects.Condition.condition
        """
        r = self._get('Observation', session=self.session)

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Observation)
        else:
            r.raise_for_status()

    def get_all_procedures(self):
        """
        Gets all conditions

        Returns:
            List of fhir_objects.Condition.condition
        """
        r = self._get('Procedure', session=self.session)

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Procedure)
        else:
            r.raise_for_status()

    def get_patients_by_procedure_code(self, system: str, code: str):
        """
        Gets all patients with procedure of a certain system code

        Args: 
            system (str): System from which the code originates (e.g. 'http://snomed.info/sct')
            code (str): Code (e.g. 73761001)

        Returns:
            List of fhir_objects.Patient.patient
        """
        r = self._get('Patient', session=self.session, **
                      {'_has:Procedure:patient:code': '{}|{}'.format(system, code)})

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Patient)
        else:
            r.raise_for_status()

    def get_patients_by_procedure_text(self, text: str):
        """
        Gets all patients with procedure of a certain text (e.g. Colonoscopy)

        Args: 
            text (str): Text of CodeableConcept.text, Coding.display, or Identifier.type.text.

        Returns:
            List of fhir_objects.Patient.patient
        """
        r = self._get('Procedure', session=self.session, **
                      {'code:text': text, '_include': 'Procedure:patient'})

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Patient)
        else:
            r.raise_for_status()

    def get_patients_by_condition_code(self, system: str, code: str):
        """
        Gets all patients with condition of a certain system code

        Args: 
            system (str): System from which the code originates (e.g. 'http://snomed.info/sct')
            code (str): Code (e.g. 195662009)

        Returns:
            List of fhir_objects.Patient.patient
        """
        r = self._get(
            'Condition', **{'_has:Condition:patient:code': '{}|{}'.format(system, code)})

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Patient)
        else:
            r.raise_for_status()

    def get_patients_by_condition_text(self, text: str):
        """
        Gets all patients with condition of a certain text (e.g 'Acute viral pharyngitis')

        Args: 
            text (str): Text of CodeableConcept.text, Coding.display, or Identifier.type.text.

        Returns:
            List of fhir_objects.Patient.patient
        """
        r = self._get('Condition', session=self.session, **
                      {'code:text': text, '_include': 'Condition:patient'})

        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Patient)
        else:
            r.raise_for_status()

    def get_observation_by_patient(self, patient_id: str):
        """
        Gets all observations for a given patient.

        Args:
            patient_id (str): The patient resource identifier
        """
        r = self._get('Observation', session=self.session, patient=patient_id)
        if self._check_status(r.status_code):
            return self._collect(r.json(), self.session, Observation)
        else:
        	r.raise_for_status()
