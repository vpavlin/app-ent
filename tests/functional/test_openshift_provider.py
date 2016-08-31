from __future__ import absolute_import

import logging
import os

from .base import OpenshiftProviderTestSuite

logger = logging.getLogger()


class TestWordpress(OpenshiftProviderTestSuite):
    """
    Test Wordpress Atomic App on Kubernetes Provider
    """

    def setUp(self):
        super(TestWordpress, self).setUp()
        self.answers.update({
            'mariadb-atomicapp': {
                'db_user': 'foo',
                'db_pass': 'foo',
                'db_name': 'foo'
            },
            'wordpress': {
                'db_user': 'foo',
                'db_pass': 'foo',
                'db_name': 'foo'
            }
        })

    def _run(self):
        app_spec = os.path.join(
            self.nulecule_lib, 'wordpress-centos7-atomicapp')
        return self.deploy(app_spec, self.answers)

    def test_wordpress_lifecycle(self):
        workdir = self._run()

        self.assertPod('wordpress', status='ContainerCreating', timeout=120)
        self.assertPod('mariadb', status='Running', timeout=120)

        self.assertService('wpfrontend', timeout=120)
        self.assertService('mariadb', timeout=120)

        self.undeploy(workdir)

        self.assertPod('wordpress', exists=False, timeout=120)
        self.assertPod('mariadb', exists=False, timeout=120)
