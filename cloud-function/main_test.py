from main import create_app
from flask import json
from test.support import EnvironmentVarGuard
import os
import pytest

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("MAX_EXECUTABLE", "1000000")
    monkeypatch.setenv("MAX_CALLDATA", "1000000")
    monkeypatch.setenv("MAX_TIMEOUT", "3000")
    monkeypatch.setenv("MAX_STDOUT", "1000000")
    monkeypatch.setenv("MAX_STDERR", "1000000")

def test_error_invalid_json_request(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data="{'executable': '123', 'calldata':}",
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "invalid JSON request format"


def test_error_missing_executable(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"calldata": "bitcoin", "timeout": 123456}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "executable field is missing from JSON request"


def test_error_executable_empty(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"executable": "", "calldata": "bitcoin", "timeout": 1000}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 126
    assert data["stdout"] == ""
    assert data["stderr"] == ""
    assert data["err"] == "Execution fail"


def test_error_missing_calldata(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"executable": "123", "timeout": 123456}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "calldata field is missing from JSON request"


def test_error_calldata_empty(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwpwcmludCgnaGVsbG8nKQ==",
                "calldata": "123",
                "timeout": 1000,
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 0
    assert data["stdout"] == "hello\n"
    assert data["stderr"] == ""
    assert data["err"] == ""


def test_error_missing_timeout(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"executable": "123", "calldata": "bitcoin"}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "timeout field is missing from JSON request"


def test_error_timeout_empty(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"executable": "123", "calldata": "bitcoin", "timeout": ""}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "timeout field is empty"


def test_error_timeout_less_than_0(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps({"executable": "123", "calldata": "bitcoin", "timeout": -5}),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "Runtime must more than 0"


def test_error_timeout_more_than_max_timeout(mock_env):
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "executable": "123",
                "calldata": "bitcoin",
                "timeout": 1111111111111111111111111111111111111111,
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 400
    assert data["error"] == "Runtime exceeded max size"


def test_success_execution(mock_env):
    """#!/usr/bin/env python3
      print('hello')
  """
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "123",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwpwcmludCgnaGVsbG8nKQ==",
                "timeout": 1000,
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 0
    assert data["stdout"] == "hello\n"
    assert data["stderr"] == ""
    assert data["err"] == ""


def test_error_execution_fail(mock_env):
    """#!/usr/bin/enveeeeeeeee python3
      print('hello')
  """
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnZlZWVlZWVlZWUKcHl0aG9uM1xucHJpbnQoJ2hlbGxvJyk=",
                "timeout": 1000,
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 126
    assert data["stdout"] == ""
    assert data["stderr"] == ""
    assert data["err"] == "Execution fail"


def test_error_execution_timeout(mock_env):
    """#!/usr/bin/env python3
      import time

      time.sleep(1)
  """
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwppbXBvcnQgdGltZQoKdGltZS5zbGVlcCgxKQ==",
                "timeout": 100,  # 100 millisec
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 111
    assert data["stdout"] == ""
    assert data["stderr"] == ""
    assert data["err"] == "Execution time limit exceeded"


def test_success_execution_timeout(mock_env):
    """#!/usr/bin/env python3
      import time

      time.sleep(1) # 1000 millisec
  """
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwppbXBvcnQgdGltZQoKdGltZS5zbGVlcCgxKQpwcmludCgiaGVsbG8iKQ==",
                "timeout": 2000,  # 2000 millisec
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 0
    assert data["stdout"] == "hello\n"
    assert data["stderr"] == ""
    assert data["err"] == ""


def test_error_infinite_loop_execution(mock_env):
    """#!/usr/bin/env python3
      import time

      while True:
          print("hello")
  """
    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwppbXBvcnQgdGltZQp3aGlsZSBUcnVlOgogICAgcHJpbnQoImhlbGxvIik=",
                "timeout": 1000,  # 1000 millisec
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 111
    assert data["stdout"] == ""
    assert data["stderr"] == ""
    assert data["err"] == "Execution time limit exceeded"

@pytest.fixture
def mock_out_and_error_env(monkeypatch):
    monkeypatch.setenv("MAX_STDOUT", "10")
    monkeypatch.setenv("MAX_STDERR", "10")


def test_error_stdout_exceed(mock_out_and_error_env):
    """#!/usr/bin/env python3
      import time

      for i in range(10):
          print (i)
  """

    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwppbXBvcnQgdGltZQoKZm9yIGkgaW4gcmFuZ2UoMTApOgogICAgcHJpbnQgKGkp",
                "timeout": 1000,  # 1000 millisec
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 0
    assert data["stdout"] == "0\n1\n2\n3\n4\n"
    assert data["stderr"] == ""
    assert data["err"] == ""


def test_error_stderr_exceed(mock_out_and_error_env):
    """#!/usr/bin/env python3
      import time

      print (1/0)
  """

    app = create_app()
    response = app.test_client().post(
        "/execute",
        data=json.dumps(
            {
                "calldata": "",
                "executable": "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwppbXBvcnQgdGltZQoKcHJpbnQgKDEvMCk=",
                "timeout": 1000,  # 1000 millisec
            }
        ),
        content_type="application/json",
    )

    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["returncode"] == 1
    assert data["stdout"] == ""
    assert data["stderr"] == "Traceback "
    assert data["err"] == ""
