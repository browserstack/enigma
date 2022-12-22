import pytest
from Access import helpers
from Access.helpers import getAvailableAccessModules, getAccessModules
import glob
from os.path import dirname, basename, isfile, join

class MockAccessModule:
    def __init__(self, name = ""):
        self.name = name
        self.available = True

@pytest.mark.parametrize("testName, available_accesses, expectedModuleList",[
                        ("available_accesses has values", [MockAccessModule(name = "name1"), MockAccessModule(name = "name2")], [MockAccessModule(name = "name1"), MockAccessModule(name = "name2")]),
                        ("available_accesses has no values", [], [MockAccessModule(name = "name3"), MockAccessModule(name = "name4")]),
])
def test_getAvailableAccessModules(mocker, testName, available_accesses,expectedModuleList):
    mocker.patch("Access.helpers.getAccessModules", return_value=expectedModuleList)

    helpers.available_accesses = available_accesses
    modules = getAvailableAccessModules()
    assert len(modules)  == len(expectedModuleList)
    for i in range(len(modules)):
        assert modules[i].name == expectedModuleList[i].name

@pytest.mark.parametrize("testName, cached_accesses, expectedModuleList",[
                        ("cached_accesses has values", [MockAccessModule(name = "name1"), MockAccessModule(name = "name2")], [MockAccessModule(name = "name1"), MockAccessModule(name = "name2")]),
])
def test_getAccessModules(mocker,testName, cached_accesses, expectedModuleList):
    mocker.patch("glob.glob", return_value=["dir1","dir2"] + ["base_somedir","__pycache__"])
    mocker.patch("os.path.isfile", return_value=False)
    helpers.cached_accesses = cached_accesses
    modules = getAccessModules()
    assert len(modules)  == len(expectedModuleList)
    for i in range(len(modules)):
        assert modules[i].name == expectedModuleList[i].name

