from execra_sdk import ExecraError, ExecraConnectionError, ExecraAuthError

def test_exceptions_init():
    err = ExecraError("General error", status_code=500)
    assert str(err) == "General error"
    assert err.status_code == 500

    conn_err = ExecraConnectionError("Connection failed")
    assert isinstance(conn_err, ExecraError)
    assert conn_err.message == "Connection failed"

    auth_err = ExecraAuthError("Unauthorized", status_code=401)
    assert isinstance(auth_err, ExecraError)
    assert auth_err.status_code == 401
