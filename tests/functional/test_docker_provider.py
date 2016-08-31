from base import DockerProviderTestSuite


class TestWordpress(DockerProviderTestSuite):
    """
    Test Wordpress Atomic App on Kubernetes Provider
    """
    APP_DIR_NAME = 'wordpress-centos7-atomicapp'
    answers = {
        'general': {
            'namespace': 'default'
        },
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
    }

    def _run(self):
        app_spec = self.image_name
        return self.deploy(app_spec, self.answers)

    def test_wordpress_run(self):
        self._run()
        self.assertContainerRunning('wordpress-atomicapp')
        self.assertContainerRunning('mariadb-atomicapp-app')

    def test_wordpress_stop(self):
        workdir = self._run()

        self.undeploy(workdir)

        self.assertContainerNotRunning('wordpress-atomicapp')
        self.assertContainerNotRunning('mariadb-atomicapp-app')
