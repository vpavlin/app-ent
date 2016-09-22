from __future__ import absolute_import

import os

from .base import KubernetesProviderTestSuite


class TestWordpress(KubernetesProviderTestSuite):
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

    def _run(self):
        app_spec = self.image_name
        return self.deploy(app_spec, self.answers)

    def test_wordpress_lifecycle(self):
        app_spec = os.path.join(
            self.nulecule_lib, 'wordpress-centos7-atomicapp')
        workdir = self.deploy(app_spec, self.answers)

        self.assertPod('wordpress', status='Running', timeout=360)
        self.assertPod('mariadb', status='Running', timeout=360)

        self.assertService('wordpress', timeout=360)
        self.assertService('mariadb', timeout=360)

        self.undeploy(app_spec, workdir)

        self.assertPod('wordpress', exists=False, timeout=360)
        self.assertPod('mariadb', exists=False, timeout=360)
