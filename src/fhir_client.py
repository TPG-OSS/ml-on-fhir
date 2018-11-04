import requests
from fhir_objects.patient import Patient
from fhir_objects.condition import Condition
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

        result += [constructor(d['resource']) for d in result_json['entry']]
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
        with requests.Session() as s:
            r = self._get('Patient', session=s)

            if self._check_status(r.status_code):
                return self._collect(r.json(), s, Patient)
            else:
                r.raise_for_status()

    def get_all_conditions(self):
        """
        Gets all conditions

        Returns:
            List of fhir_objects.Condition.condition
        """
        with requests.Session() as s:
            r = self._get('Condition', session=s)

            if self._check_status(r.status_code):
                return self._collect(r.json(), s, Condition)
            else:
                r.raise_for_status()
