"""iOS Simulator smoke test.

Proof of concept for backlog 318's finding that iOS can be driven from a
GitHub-hosted macOS runner while the team works on Windows. It asserts only what
it can prove: a real XCUITest session starts, the reference app reaches the
foreground, and the UI tree comes back. Screen objects and the 5-layer structure
come later, in the build.
"""

import os
import pathlib

import pytest
from appium import webdriver
from appium.options.ios import XCUITestOptions

ARTIFACTS = pathlib.Path(__file__).resolve().parent.parent / "artifacts"
APP_STATE_RUNNING_IN_FOREGROUND = 4


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} is not set; the workflow must export it")
    return value


@pytest.fixture(scope="module")
def driver():
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.platform_version = _required("IOS_PLATFORM_VERSION")
    options.device_name = _required("IOS_DEVICE_NAME")
    options.udid = _required("IOS_UDID")
    options.app = _required("IOS_APP_PATH")
    options.set_capability("appium:newCommandTimeout", 180)

    drv = webdriver.Remote("http://127.0.0.1:4723", options=options)
    try:
        yield drv
    finally:
        ARTIFACTS.mkdir(exist_ok=True)
        try:
            drv.get_screenshot_as_file(str(ARTIFACTS / "ios-smoke.png"))
            (ARTIFACTS / "ios-smoke-page-source.xml").write_text(
                drv.page_source, encoding="utf-8"
            )
        finally:
            drv.quit()


def test_session_starts(driver):
    assert driver.session_id, "no session id returned"


def test_app_is_in_the_foreground(driver):
    bundle_id = _required("IOS_BUNDLE_ID")
    assert driver.query_app_state(bundle_id) == APP_STATE_RUNNING_IN_FOREGROUND


def test_ui_tree_is_returned(driver):
    source = driver.page_source
    assert source.strip(), "page source is empty"
    assert "XCUIElementType" in source, "page source is not an XCUITest tree"
