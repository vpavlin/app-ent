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

    def test_wordpress_lifecycle(self):
        app_spec = self.image_name
        workdir = self.deploy(app_spec, self.answers)

        self.assertContainerRunning('wordpress-atomicapp', timeout=10)
        self.assertContainerRunning('mariadb-atomicapp-app', timeout=10)

        self.undeploy(self.image_name, workdir)

        self.assertContainerNotRunning('wordpress-atomicapp', timeout=10)
        self.assertContainerNotRunning('mariadb-atomicapp-app', timeout=10)
