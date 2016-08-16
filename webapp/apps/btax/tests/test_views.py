from django.test import TestCase
from django.test import Client
import mock

from ..models import BTaxSaveInputs, BTaxOutputUrl
from ..models import convert_to_floats
from ..compute import (DropqCompute, MockCompute, MockFailedCompute,
                       NodeDownCompute)
import taxcalc
from taxcalc import Policy


START_YEAR = 2016

OK_POST_DATA = {u'btax_betr_pass': 0.33,
                u'btax_depr_5yr': u'btax_depr_5yr_gds_Switch',
                u'btax_depr_27_5yr_exp': 0.4,
                u'has_errors': [u'False'],
                u'start_year': unicode(START_YEAR),
                u'csrfmiddlewaretoken': u'abc123'}

class BTaxViewsTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_btax_get(self):
        # Issue a GET request.
        response = self.client.get('/btax/')

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_btax_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.btax.views']
        webapp_views.dropq_compute = MockCompute()

        data = OK_POST_DATA.copy()

        response = self.client.post('/btax/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("btax/"))

    def test_btax_nodes_down(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.btax import views as webapp_views
        webapp_views.dropq_compute = NodeDownCompute()

        data = OK_POST_DATA.copy()

        response = self.client.post('/btax/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("btax/"))
        # One more redirect
        response = self.client.get(response.url)
        # Check that we successfully load the page
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)

    def test_btax_failed_job(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.btax import views as webapp_views
        webapp_views.dropq_compute = MockFailedCompute()
        data = OK_POST_DATA.copy()
        response = self.client.post('/btax/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("btax/"))
        response = self.client.get(response.url)
        # Make sure the failure message is in the response
        self.failUnless("Your calculation failed" in str(response))
