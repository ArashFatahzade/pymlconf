import unittest

from pymlconf import Root


class MyWriter:
    pass


class Test(unittest.TestCase):

    def setUp(self):
        self._builtin = '''
    app:
        name: MyApp
        listen:
            sock1:
                addr: 192.168.0.1
                port: 8080
            sock2:
                addr: 127.0.0.1
                port: "89"
        languages:
            - english
            - {language: persian, country: iran}


    logging:
        logfile: /var/log/myapp.log
        formatter: !!python/name:str
        writer: !!python/object:%s.MyWriter {}
    ''' % __name__

    def test_simple_syntax(self):
        """
        Testing simple Yaml syntax
        """

        cm = Root(self._builtin)
        self.assertEqual(cm.app.name, "MyApp")
        self.assertEqual(len(cm.app.listen), 2)
        self.assertEqual(cm.app.listen.sock1.addr, "192.168.0.1")
        self.assertEqual(cm.app.listen.sock1.port, 8080)
        self.assertEqual(cm.app.listen.sock2.addr, "127.0.0.1")
        self.assertEqual(cm.app.listen.sock2.port, '89')
        self.assertEqual(cm.logging.logfile, "/var/log/myapp.log")

        self.assertEqual(len(cm.app.languages), 2)
        self.assertEqual(cm.app.languages[0], 'english')
        self.assertEqual(cm.app.languages[1].language, 'persian')
        self.assertEqual(cm.app.languages[1].country, 'iran')
        self.assertEqual(cm.logging.formatter, str)
        self.assertTrue(isinstance(cm.logging.writer, MyWriter))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
