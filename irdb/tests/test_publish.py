# -*- coding: utf-8 -*-
"""
Control flow of publish script, pseudocode:
-c set:
    make_package for each pkg_name:
        -s not set:
            .dev suffix
        else:
            no suffix
        -k not set:
            version number from current date
        else:
            version number from yaml file
        zip_package_folder:
            stuff
-u set:
    push_to_server for each pkg_name:
        -u or -l not set:
            raise Error
        _get_local_path:
            -s not set:
                .dev suffix
            else:
                no suffix
        _get_server_path:
            stuff
        -s set and --no-confirm not set:
            Ask user confirmation
        attempt upload
-c not set and -u not set:
    warning
"""

from functools import partial
# from pathlib import Path
# from datetime import datetime as dt

from io import StringIO
from unittest import mock
import builtins

import pytest
# import yaml

from .. import publish as pub

# argv mock reference:
# https://stackoverflow.com/questions/48359957/pytest-with-argparse-how-to-test-user-is-prompted-for-confirmation


# PATH_TEST_PACKAGE_VERSION_YAML = pub.PKGS_DIR / "test_package" / "version.yaml"
# NOW = dt.now().strftime("%Y-%m-%d")


# @pytest.fixture(name="preserve_versions", scope="function")
# def fixture_preserve_versions():
#     """Preserve the versions of test packages."""

#     # Backup version information.
#     b_yaml_test_package = PATH_TEST_PACKAGE_VERSION_YAML.read_bytes()

#     # yield instead of return so the fixture can clean up afterwards
#     yield

#     # Put the original values back.
#     PATH_TEST_PACKAGE_VERSION_YAML.write_bytes(b_yaml_test_package)


@pytest.fixture(scope="module")
def temp_zipfiles(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("_ZIPPED_PACKAGES")
    with mock.patch("irdb.publish.ZIPPED_DIR", tmpdir):
        pub.zip_package_folder("test_package",
                               "test_package.2023-07-19.zip")
        pub.zip_package_folder("test_package",
                               "test_package.2023-07-20.dev.zip")
    return tmpdir


@pytest.mark.usefixtures("temp_zipfiles")
class TestGetLocalPath:
    def test_stable(self, temp_zipfiles):
        with mock.patch("irdb.publish.ZIPPED_DIR", temp_zipfiles):
            response = str(pub._get_local_path("test_package", True))
            assert response.endswith(".zip")
            assert "test_package" in response
            assert "dev" not in response
            assert "test_package.2023-07-19.zip" in response

    def test_dev(self, temp_zipfiles):
        with mock.patch("irdb.publish.ZIPPED_DIR", temp_zipfiles):
            response = str(pub._get_local_path("test_package", False))
            assert response.endswith(".dev.zip")
            assert "test_package" in response
            assert "test_package.2023-07-20.dev.zip" in response


class TestGetServerPath:
    def test_normal(self):
        assert pub._get_server_path("test_package", "foo") == "instruments/foo"

    def test_missing_called(self):
        fake_folder_dict = {"bogus": "bar"}
        mock_obj = mock.Mock(return_value=fake_folder_dict)
        with mock.patch("irdb.publish._handle_missing_folder",
                        mock_obj) as mock_missing:
            assert pub._get_server_path("bogus", "foo") == "bar/foo"
            mock_missing.assert_called_once_with("bogus")


def _fake_input(prompt: str, from_user: str) -> str:
    """Used to mock the builtin input function"""
    print(prompt)
    return from_user


@pytest.mark.webtest
@pytest.mark.parametrize("from_user, result", [
    ("y", True),
    ("Y", True),
    ("n", False),
    ("N", False),
    ("bogus", False),
    ("foo bar baz", False),
    ("y bar baz", False),
    ("foo y baz", False),
])
def test_confirm(from_user, result):
    pkg_name = "test_package"
    current_stable = "2023-07-10"
    prompt = ("This will supersede the current STABLE version "
              f"({current_stable}) of '{pkg_name}' on the IRDB server. "
              "The uploaded package will be set as the new default for "
              f"'{pkg_name}'.\nAre you sure you want to continue?    (y)/n:  ")
    with mock.patch.object(builtins, "input",
                           partial(_fake_input, from_user=from_user)):
        with mock.patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            assert result == pub.confirm(pkg_name)
            assert prompt == mock_stdout.getvalue().strip("\n")


@pytest.fixture(name="default_argv", scope="function")
def fixture_default_argv():
    return ["", "-l", "fake_username", "-p", "fake_password", "test_package"]


@pytest.mark.webtest
@pytest.mark.usefixtures("default_argv", "temp_zipfiles")
@pytest.mark.parametrize("argv, called, response", [
    (["-u"], False, None),
    (["-u", "-s", "--no-confirm"], False, None),
    (["-u", "-s"], True, False),
    (["-u", "-s"], True, True),
])
def test_call_confirm(default_argv, temp_zipfiles, argv, called, response):
    with mock.patch("sys.argv", default_argv + argv):
        with mock.patch("irdb.publish.confirm",
                        mock.Mock(return_value=response)) as mock_confirm:
            with mock.patch("irdb.publish.ZIPPED_DIR", temp_zipfiles):
                # Catch exception raised by fake login credentials
                authex = pub.pysftp.paramiko.ssh_exception.AuthenticationException

                if called and not response:
                    # Should abort -> no authex raised
                    pub.main()
                else:
                    # Should continue and attempt upload -> authex raised
                    with pytest.raises(authex):
                        pub.main()

                assert mock_confirm.called == called


@pytest.mark.usefixtures("default_argv")
@pytest.mark.parametrize("argv, called, args", [
    ([], False, {}),
    (["-c"], True, {"stable": False, "keep_version": False}),
    (["-c", "-s"], True, {"stable": True, "keep_version": False}),
    (["-c", "-k"], True, {"stable": False, "keep_version": True}),
    (["-c", "-s", "-k"], True, {"stable": True, "keep_version": True}),
])
def test_make_package_called(default_argv, argv, called, args):
    with mock.patch("sys.argv", default_argv + argv):
        with mock.patch("irdb.publish.make_package") as mock_mkpkg:
            pub.main()
            if called:
                mock_mkpkg.assert_called_once_with("test_package",
                                                   args["stable"],
                                                   args["keep_version"])
            else:
                mock_mkpkg.assert_not_called()


@pytest.mark.usefixtures("default_argv")
@pytest.mark.parametrize("argv, called, args", [
    ([], False, {}),
    (["-u"], True, {"stable": False, "no_confirm": False}),
    (["-u", "-s"], True, {"stable": True, "no_confirm": False}),
    (["-u", "--no-confirm"], True, {"stable": False, "no_confirm": True}),
    (["-u", "-s", "--no-confirm"], True, {"stable": True, "no_confirm": True}),
])
def test_push_to_server_called(default_argv, argv, called, args):
    pwd = pub.Password("fake_password")
    with mock.patch("sys.argv", default_argv + argv):
        with mock.patch("irdb.publish.push_to_server") as mock_phsvr:
            pub.main()
            if called:
                mock_phsvr.assert_called_once_with("test_package",
                                                   args["stable"],
                                                   "fake_username", pwd,
                                                   args["no_confirm"])
            else:
                mock_phsvr.assert_not_called()


@pytest.mark.usefixtures("default_argv")
def test_multiple_packages(default_argv):
    argv = ["foo_package", "bar_package", "-c", "-u"]
    with mock.patch("sys.argv", default_argv + argv):
        with mock.patch("irdb.publish.make_package") as mock_mkpkg:
            with mock.patch("irdb.publish.push_to_server") as mock_phsvr:
                pub.main()
                assert mock_mkpkg.call_count == 3
                assert mock_phsvr.call_count == 3
                assert "bar_package" in mock_mkpkg.call_args[0]
                assert "bar_package" in mock_phsvr.call_args[0]


@pytest.mark.usefixtures("default_argv", "caplog")
def test_warning_no_action(default_argv, caplog):
    warnmsg = ("Neither `compile` nor `upload` was set. "
               "No action will be performed.")
    with mock.patch("sys.argv", default_argv):
        pub.main()
        assert warnmsg in caplog.text
