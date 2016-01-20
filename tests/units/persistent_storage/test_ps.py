import unittest
import tempfile
from atomicapp.requirements import Requirements, RequirementFailedException


class TestPersistentStorage(unittest.TestCase):

    # Create a tmp dir and add graph and config information

    def setUp(self):
        config = {'helloapache-app': {'image': 'centos/httpd', 'hostport': 80},
                  'general': {'namespace': 'default', 'provider': 'kubernetes'}}
        graph = [{'persistentVolume': {'accessMode': 'ReadWrite', 'name': 'var-lib-mongodb-data', 'size': 4}},
                 {'persistentVolume': {'accessMode': 'ReadWrite', 'name': 'var-log-mongodb', 'size': 4}}]
        self.tmpdir = tempfile.mkdtemp(prefix="atomicapp-test", dir="/tmp")
        self.test = Requirements(
            config=config, basepath=self.tmpdir, graph=graph, provider="kubernetes", dryrun=True)

    def tearDown(self):
        pass

    def test_missing_requirement(self):
        with self.assertRaises(RequirementFailedException) as context:
            self.test._find_requirement_function_name('foo')

        self.assertTrue("Requirement foo does not exist." in context.exception)

    # Rest of these tests checks to see if dryrunning the provider passes correctly
    def test_run(self):
        self.test.run()

    def test_stop(self):
        self.test.stop()
