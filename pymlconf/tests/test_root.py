import re
import unittest
from os import path

from pymlconf import MergableDict, MergableList, Root


class TestConfigManager(unittest.TestCase):
    def test_constructor(self):
        context = dict(
            c=3
        )

        builtin = '''
          a:
            a1: 1

          b:
          - 1
          - 2
          - %(c)s
        '''

        root = Root(builtin, context)
        self.assertEqual(root.a.a1, 1)
        self.assertEqual(root.b[0], 1)
        self.assertEqual(root.b[1], 2)
        self.assertEqual(root.b[2], 3)

        root.merge('''
          a:
            a2: 2
        ''')
        self.assertEqual(root.a.a2, 2)

        root.a.a3 = 3
        self.assertEqual(root.a.a1, 1)
        self.assertEqual(root.a.a2, 2)
        self.assertEqual(root.a.a3, 3)

        root.merge('''
          b:
            - 4
        ''')
        self.assertEqual(root.b[0], 4)
        self.assertEqual(1, len(root.b))

    def test_dot_in_key(self):
        root = Root('''
            server.token.salt: 1345
        ''')

        self.assertEqual(root['server.token.salt'], 1345)
        self.assertFalse(hasattr(root, 'server'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
