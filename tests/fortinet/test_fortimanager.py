"""
Test the FortiManager class
"""

# pylint: disable=no-member
from unittest.mock import MagicMock

import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch

from fotoobo.exceptions import APIError
from fotoobo.fortinet.fortimanager import FortiManager
from tests.helper import ResponseMock


class TestFortiManager:
    """Test the FortiManager class"""

    @staticmethod
    def test_assign_all_objects(monkeypatch: MonkeyPatch) -> None:
        """Test assign_all_objects"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "result": [
                            {
                                "data": {"task": 111},
                                "status": {"code": 0, "message": "OK"},
                                "url": "/securityconsole/assign/package",
                            }
                        ]
                    },
                    status_code=200,
                )
            ),
        )
        assert FortiManager("host", "", "").assign_all_objects("dummy_adom", "dummy_policy") == 111
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [
                    {
                        "data": {
                            "flags": ["cp_all_objs"],
                            "pkg": "dummy_policy",
                            "target": [{"adom": "dummy_adom", "excluded": "disable"}],
                        },
                        "url": "/securityconsole/assign/package",
                    }
                ],
                "session": "",
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_assign_all_objects_http_404(monkeypatch: MonkeyPatch) -> None:
        """Test assign_all_objects with http error 404"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(return_value=ResponseMock(json={}, status_code=404)),
        )
        with pytest.raises(APIError) as err:
            FortiManager("host", "", "").assign_all_objects("dummy_adom", "dummy_policy")
        assert "HTTP/404 Resource Not Found" in str(err.value)
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [
                    {
                        "data": {
                            "flags": ["cp_all_objs"],
                            "pkg": "dummy_policy",
                            "target": [{"adom": "dummy_adom", "excluded": "disable"}],
                        },
                        "url": "/securityconsole/assign/package",
                    }
                ],
                "session": "",
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_assign_all_objects_status_not_ok(monkeypatch: MonkeyPatch) -> None:
        """Test assign_all_objects with status code != 0"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "result": [
                            {
                                "data": {},
                                "status": {"code": 22, "message": "NOT-OK"},
                                "url": "/securityconsole/assign/package",
                            }
                        ]
                    },
                    status_code=200,
                )
            ),
        )
        assert FortiManager("host", "", "").assign_all_objects("adom1,adom2", "policy1") == 0
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [
                    {
                        "data": {
                            "flags": ["cp_all_objs"],
                            "pkg": "policy1",
                            "target": [
                                {"adom": "adom1", "excluded": "disable"},
                                {"adom": "adom2", "excluded": "disable"},
                            ],
                        },
                        "url": "/securityconsole/assign/package",
                    }
                ],
                "session": "",
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_get_adoms(monkeypatch: MonkeyPatch) -> None:
        """Test fmg get adoms"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={"result": [{"data": [{"name": "dummy"}]}]}, status_code=200
                )
            ),
        )
        assert FortiManager("host", "", "").get_adoms() == [{"name": "dummy"}]
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"method": "get", "params": [{"url": "/dvmdb/adom"}], "session": ""},
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_get_adoms_http_error(monkeypatch: MonkeyPatch) -> None:
        """Test fmg get adoms with a status != 200"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(return_value=ResponseMock(json={}, status_code=400)),
        )
        with pytest.raises(APIError) as err:
            FortiManager("", "", "").get_adoms()
        assert "HTTP/400 Bad Request" in str(err.value)

    @staticmethod
    @pytest.mark.parametrize(
        "response, expected",
        (
            pytest.param({"result": [{"data": {"Version": "v1.1.1-xyz"}}]}, "v1.1.1", id="ok"),
            pytest.param({"result": [{"data": {"Version": "dummy"}}]}, "", id="dummy"),
            pytest.param({"result": [{"data": {"Version": ""}}]}, "", id="empty version field"),
            pytest.param({"result": [{"data": {}}]}, "", id="empty data"),
            pytest.param({"result": []}, "", id="empty result"),
            pytest.param({}, "", id="empty return_value"),
        ),
    )
    def test_get_version(response: MagicMock, expected: str, monkeypatch: MonkeyPatch) -> None:
        """Test FortiManager get version"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(return_value=ResponseMock(json=response, status_code=200)),
        )
        assert FortiManager("host", "", "").get_version() == expected
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"method": "get", "params": [{"url": "/sys/status"}], "session": ""},
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_login(monkeypatch: MonkeyPatch) -> None:
        """Test the login to a FortiManager"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "id": 1,
                        "result": [
                            {"status": {"code": 0, "message": "OK"}, "url": "/sys/login/user"}
                        ],
                        "session": "dummy_session_key",
                    },
                    status_code=200,
                )
            ),
        )
        fmg = FortiManager("host", "user", "pass")
        assert fmg.login() == 200
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [{"data": {"passwd": "pass", "user": "user"}, "url": "/sys/login/user"}],
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_login_with_session_path(monkeypatch: MonkeyPatch) -> None:
        """Test the login to a FortiManager when a session_path is given"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "id": 1,
                        "result": [
                            {
                                "status": {"code": 0, "message": "dummy"},
                                "url": "/sys/status",
                            }
                        ],
                        "session": "dummy_session_key",
                    },
                    status_code=200,
                )
            ),
        )
        fmg = FortiManager("host", "user", "pass")
        fmg.hostname = "test_fmg"
        fmg.session_path = "tests/data"
        assert fmg.login() == 200
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "get",
                "params": [{"url": "/sys/status"}],
                "session": "dummy_session_key",
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_login_with_session_path_invalid_key(monkeypatch: MonkeyPatch) -> None:
        """
        Test the login to a FortiManager when a session_path is given but the session key is invalid
        """
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "id": 1,
                        "result": [
                            {
                                "status": {"code": -11, "message": "dummy"},
                                "url": "/sys/status",
                            }
                        ],
                        "session": "dummy_session_key",
                    },
                    status_code=200,
                )
            ),
        )
        fmg = FortiManager("host", "user", "pass")
        fmg.hostname = "test_fmg"
        fmg.session_path = "tests/data"
        assert fmg.login() == 200
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [{"data": {"passwd": "pass", "user": "user"}, "url": "/sys/login/user"}],
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_login_with_session_path_not_found(temp_dir: str, monkeypatch: MonkeyPatch) -> None:
        """
        Test the login to a FortiManager when a session_path is given but the session key is invalid
        """
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "id": 1,
                        "result": [
                            {
                                "status": {"code": 0, "message": "dummy"},
                                "url": "/sys/status",
                            }
                        ],
                        "session": "dummy_session_key",
                    },
                    status_code=200,
                )
            ),
        )
        fmg = FortiManager("host", "user", "pass")
        fmg.hostname = "test_fmg_dummy"
        fmg.session_path = temp_dir
        assert fmg.login() == 200
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [{"data": {"passwd": "pass", "user": "user"}, "url": "/sys/login/user"}],
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_logout(monkeypatch: MonkeyPatch) -> None:
        """Test the logout of a FortiManager"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "method": "exec",
                        "params": [{"url": "/sys/logout"}],
                        "session": "dummy_session_key",
                    },
                    status_code=200,
                )
            ),
        )
        fortimanager = FortiManager("host", "user", "pass")
        assert fortimanager.logout() == 200
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={
                "method": "exec",
                "params": [{"url": "/sys/logout"}],
                "session": "dummy_session_key",
            },
            params=None,
            timeout=3,
            verify=True,
        )

    @staticmethod
    def test_post_single(monkeypatch: MonkeyPatch) -> None:
        """Test fmg post with a single dict"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={"result": [{"status": {"code": 0}}]}, status_code=200
                )
            ),
        )
        assert not FortiManager("host", "", "").post("ADOM", {"params": [{"url": "{adom}"}]})
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"params": [{"url": "adom/ADOM"}], "session": ""},
            params=None,
            timeout=10,
            verify=True,
        )

    @staticmethod
    def test_post_multiple(monkeypatch: MonkeyPatch) -> None:
        """Test fmg post with a list of dicts"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={"result": [{"status": {"code": 0}}]}, status_code=200
                )
            ),
        )
        assert not FortiManager("host", "", "").post("ADOM", [{"params": [{"url": "{adom}"}]}])
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"params": [{"url": "adom/ADOM"}], "session": ""},
            params=None,
            timeout=10,
            verify=True,
        )

    @staticmethod
    def test_post_single_global(monkeypatch: MonkeyPatch) -> None:
        """Test fmg post with a single dict"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={"result": [{"status": {"code": 0}}]}, status_code=200
                )
            ),
        )
        assert not FortiManager("host", "", "").post("global", {"params": [{"url": "{adom}"}]})
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"params": [{"url": "global"}], "session": ""},
            params=None,
            timeout=10,
            verify=True,
        )

    @staticmethod
    def test_post_response_error(monkeypatch: MonkeyPatch) -> None:
        """Test post set with en error in the response"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "result": [{"status": {"code": 444, "message": "dummy"}, "url": "dummy"}]
                    },
                    status_code=200,
                )
            ),
        )
        assert FortiManager("host", "", "").post("ADOM", [{"params": [{"url": "{adom}"}]}]) == [
            "dummy: dummy (code: 444)"
        ]
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"params": [{"url": "adom/ADOM"}], "session": ""},
            params=None,
            timeout=10,
            verify=True,
        )

    @staticmethod
    def test_post_http_error(monkeypatch: MonkeyPatch) -> None:
        """Test fmg post with an error in the response"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(return_value=ResponseMock(json={}, status_code=444)),
        )
        with pytest.raises(APIError) as err:
            FortiManager("host", "", "").post("ADOM", [{"params": [{"url": "{adom}"}]}])
        assert "HTTP/444 general API Error" in str(err.value)
        requests.Session.post.assert_called_with(  # type:ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"params": [{"url": "adom/ADOM"}], "session": ""},
            params=None,
            timeout=10,
            verify=True,
        )

    @staticmethod
    def test_wait_for_task(monkeypatch: MonkeyPatch) -> None:
        """Test wait_for_task"""
        monkeypatch.setattr(
            "fotoobo.fortinet.fortinet.requests.Session.post",
            MagicMock(
                return_value=ResponseMock(
                    json={
                        "result": [
                            {
                                "data": [
                                    {
                                        "history": [
                                            {"detail": "detail 1", "percent": 10},
                                            {"detail": "detail 2", "percent": 20},
                                        ],
                                        "state": 4,
                                        "percent": 100,
                                        "detail": "main detail",
                                        "task_id": 222,
                                    },
                                ],
                                "status": {"code": 0, "message": "OK"},
                                "url": "/task/task/222/line",
                            }
                        ]
                    },
                    status_code=200,
                )
            ),
        )
        messages = FortiManager("host", "", "").wait_for_task(222, 0)
        assert isinstance(messages, list)
        assert messages[0]["task_id"] == 222
        requests.Session.post.assert_called_with(  # type: ignore
            "https://host:443/jsonrpc",
            headers=None,
            json={"method": "get", "params": [{"url": "/task/task/222/line"}], "session": ""},
            params=None,
            timeout=3,
            verify=True,
        )
