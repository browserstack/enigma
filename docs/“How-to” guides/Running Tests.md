# Running Unit Tests

To run all tests in the code-base, run the following on the root directory for `enigma-public-central`

```bash
make test
```

This will also clone the access modules repo added in config.json and run tests within them.

## How it works

It first ensures that the `web` container running the enigma webserver is up and running.
Then the `make` script will run the `pytest` command as a subshell in the running container.

In case the `web` container is not up, it will first start it.

## Running specific tests

To run specific subset of `pytest` tests, you can add a pass a test filter to the make command, which forwards the filter to `pytest` cli.

Example,

```bash
make test TESTS="test_aws_access"
```

OR

```bash
make test TESTS="test_aws_access or test_grant_gcp_access"
```

Please check this [link](https://docs.pytest.org/en/7.3.x/example/markers.html#using-k-expr-to-select-tests-based-on-their-name) to understand what expressions are supported
