from __future__ import absolute_import

import logging

from .base import OpenshiftProviderTestSuite

logger = logging.getLogger()


class TestWordpress(OpenshiftProviderTestSuite):
    """
    Test Wordpress Atomic App on Kubernetes Provider
    """
    APP_DIR_NAME = 'wordpress-centos7-atomicapp'

    def setUp(self):
        super(TestWordpress, self).setUp()
        self.answers.update({
            'mariadb-centos7-atomicapp:mariadb-atomicapp': {
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

    def test_wordpress_lifecycle(self):
        app_spec = self.image_name
        workdir = self.deploy(app_spec, self.answers)

        self.assertPod('wordpress', status='ContainerCreating', timeout=120)
        self.assertPod('mariadb', status='Running', timeout=120)

        self.assertService('wpfrontend', timeout=120)
        self.assertService('mariadb', timeout=120)

        self.undeploy(app_spec, workdir)

        self.assertPod('wordpress', exists=False, timeout=120)
        self.assertPod('mariadb', exists=False, timeout=120)
