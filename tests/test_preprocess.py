"""Unit tests for preprocess.py."""

import sys

sys.path.append("src")

import os
import shutil

import git
import pytest

from src.preprocess import (_clone_or_copy_repository, _get_codebase_remote,
                            _get_file_contents, _get_file_extensions,
                            _get_file_parsers, get_codebase,
                            get_project_dependencies, get_repo_name)

# Define test constants
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(TEST_DIR, "temp_dir")
TEST_REPO = "https://github.com/example/test_repo.git"
TEST_FILE_EXT = [".py", ".txt"]
TEST_FILE_NAMES = ["requirements.txt", "Pipfile"]


# Fixture to create a temporary directory
@pytest.fixture(scope="module")
def temp_directory():
    os.makedirs(TEMP_DIR)
    yield
    shutil.rmtree(TEMP_DIR)


# Tests for helper functions


def test_clone_or_copy_repository_remote(temp_directory):
    # Test cloning a remote repository
    _clone_or_copy_repository(TEST_REPO, TEMP_DIR)
    assert os.path.exists(os.path.join(TEMP_DIR, ".git"))


def test_clone_or_copy_repository_local(temp_directory):
    # Test copying a local directory
    local_dir = os.path.join(TEST_DIR, "test_local_dir")
    os.makedirs(local_dir)
    with open(os.path.join(local_dir, "test_file.txt"), "w") as f:
        f.write("Test file")
    _clone_or_copy_repository(local_dir, TEMP_DIR)
    assert os.path.exists(os.path.join(TEMP_DIR, "test_file.txt"))


def test_get_codebase_remote(temp_directory, monkeypatch):
    # Test getting codebase from a remote repository
    def mock_clone_from(url, temp_dir, depth=1):
        os.makedirs(os.path.join(temp_dir, "subdir"))
        with open(os.path.join(temp_dir, "subdir", "file.txt"), "w") as f:
            f.write("Test file")

    monkeypatch.setattr(git.Repo, "clone_from", mock_clone_from)

    codebase = _get_codebase_remote(TEST_REPO)
    assert "subdir/file.txt" in str(codebase)
    assert codebase["subdir/file.txt"] == "Test file"


def test_get_codebase_local(temp_directory):
    # Test getting codebase from a local directory
    local_dir = os.path.join(TEST_DIR, "test_local_dir")
    os.makedirs(local_dir)
    with open(os.path.join(local_dir, "test_file.txt"), "w") as f:
        f.write("Test file")

    codebase = get_codebase(local_dir)
    assert "test_file.txt" in codebase
    assert codebase["test_file.txt"] == "Test file"


def test_get_file_contents(temp_directory):
    # Test getting file contents from a directory
    os.makedirs(os.path.join(TEMP_DIR, "subdir"))
    with open(os.path.join(TEMP_DIR, "subdir", "file.txt"), "w") as f:
        f.write("Test file")

    contents = _get_file_contents(TEMP_DIR)
    assert "subdir/file.txt" in contents
    assert contents["subdir/file.txt"] == "Test file"


def test_get_file_extensions():
    # Test getting file extensions
    all_files = ["file1.py", "file2.txt", "file3.js"]
    file_ext = {".py": ".py", ".js": ".js"}

    file_extensions = _get_file_extensions(all_files, file_ext)
    assert file_extensions == [".py", ".txt", ".js"]


def test_get_file_parsers():
    # Test getting file parsers
    file_parsers = _get_file_parsers()
    assert callable(file_parsers["requirements.txt"])
    assert callable(file_parsers["Pipfile"])


# Tests for main functions


def test_get_codebase_invalid_repo(temp_directory):
    # Test getting codebase from an invalid repository
    codebase = get_codebase("invalid_repo")
    assert codebase == {}


def test_get_project_dependencies(temp_directory, monkeypatch):
    # Test getting project dependencies
    def mock_clone_or_copy_repository(repo, temp_dir):
        # Create dummy dependency files
        for file_name in TEST_FILE_NAMES:
            with open(os.path.join(temp_dir, file_name), "w") as f:
                f.write("Test dependency")

    monkeypatch.setattr(
        "preprocess._clone_or_copy_repository", mock_clone_or_copy_repository
    )
    dependencies = get_project_dependencies(TEST_REPO, TEST_FILE_EXT, TEST_FILE_NAMES)
    assert dependencies == ["Test dependency"] * 2 + TEST_FILE_EXT


def test_get_repo_name_remote():
    # Test getting repository name from a remote URL
    repo_name = get_repo_name(TEST_REPO)
    assert repo_name == "test_repo"


def test_get_repo_name_local():
    # Test getting repository name from a local path
    local_path = os.path.join(TEST_DIR, "local_dir")
    os.makedirs(local_path)
    repo_name = get_repo_name(local_path)
    assert repo_name == "local_dir"