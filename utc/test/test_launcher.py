import unittest
import cases.primary
import cases

# Ref: https://www.internalpointers.com/post/run-painless-test-suites-python-unittest

if __name__ == "__main__":
    # initialize the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # First test imports & requirements
    suite.addTests(loader.loadTestsFromModule(cases.primary))
    suite.addTests(loader.loadTestsFromModule(cases))

    # initialize a runner, pass it your suite and run it
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)









