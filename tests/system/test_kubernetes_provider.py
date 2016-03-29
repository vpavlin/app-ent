import os

from base import KubernetesProviderTestSuite


class TestWordpress(KubernetesProviderTestSuite):
    """
    Test Wordpress Atomic App on Kubernetes Provider
    """
    answers = {
        'general': {
            'namespace': 'default'
        },
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
    }

    def _run(self):
        app_spec = os.path.join(
            self.nulecule_lib, 'wordpress-centos7-atomicapp')
        return self.deploy(app_spec, self.answers)

    def test_wordpress_run(self):
        self._run()

        self.assertPod('wordpress', status='Running', timeout=10)
        self.assertPod('mariadb', status='Running', timeout=10)

        self.assertService('wordpress')
        self.assertService('mariadb')

    def test_wordpress_stop(self):
        workdir = self._run()

        self.assertPod('wordpress', timeout=10)
        self.assertPod('mariadb', timeout=10)

        self.assertService('wordpress')
        self.assertService('mariadb')

        self.undeploy(workdir)

        self.assertPod('wordpress', exists=False)
        self.assertPod('mariadb', exists=False)
