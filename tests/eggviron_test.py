from __future__ import annotations

import os

import pytest

from eggviron import Eggviron


class MockLoader:
    name = "MockLoader"

    def __init__(self, mock_values: dict[str, str]) -> None:
        self._values = mock_values

    def run(self) -> dict[str, str]:
        return self._values


SIMPLE_VALUES = {
    "foo": "bar",
    "biz": "baz",
    "answer": "42",
    "funny_number": "69.420",
    "we_are_so_back": "1",
}


@pytest.fixture
def carton() -> Eggviron:
    # Create a Eggviron with a simple value loaded for testing
    sb = Eggviron()

    for key, value in SIMPLE_VALUES.items():
        sb[key] = value

    return sb


def test_dict_views_methods(carton: Eggviron) -> None:
    # Ensure the KeysView, ValuesView, and ItemsView methods exists

    keys_view = carton.keys()
    values_view = carton.values()
    items_view = carton.items()

    assert keys_view == SIMPLE_VALUES.keys()
    assert sorted(values_view) == sorted(SIMPLE_VALUES.values())
    assert items_view == SIMPLE_VALUES.items()


def test_loaded_value_property_is_copy(carton: Eggviron) -> None:
    # Ensure the property is not returning a reference to the internal dict
    first_values = carton.loaded_values
    first_values["foo"] = "baz"

    second_values = carton.loaded_values

    assert first_values != second_values


def test_init_is_empty_when_created() -> None:
    # Creating a Eggviron instance should yield an empty box
    sb = Eggviron()

    loaded_values = sb.loaded_values

    assert loaded_values == {}


def test_get_item_returns_expected(carton: Eggviron) -> None:
    # Eggviron should behave like a dictionary when needed
    expected_key = "foo"
    expected_value = "bar"

    value = carton[expected_key]

    assert value == expected_value


def test_get_item_is_case_sensitive(carton: Eggviron) -> None:
    # Always raise a KeyError if the key is not found
    invalid_key = "FOO"

    with pytest.raises(KeyError):
        carton[invalid_key]


def test_set_item_accepts_valid_values(carton: Eggviron) -> None:
    # Eggviron should behave like a dictionary when needed
    # Keys should be normalized to upper-case
    expected_value = "flapjack"

    carton["redbird"] = expected_value

    updated_value = carton["redbird"]
    assert updated_value == expected_value


def test_set_item_raises_with_invalid_value(carton: Eggviron) -> None:
    # Eggviron should only accept strings as values
    with pytest.raises(TypeError):
        carton["FOO"] = 1  # type: ignore


def test_set_item_raises_with_invalid_key(carton: Eggviron) -> None:
    # Eggviron should only accept strings as keys
    with pytest.raises(TypeError):
        carton[1] = "flapjack"  # type: ignore


def test_set_item_raises_key_error_on_overwrite(carton: Eggviron) -> None:
    # Raises a key error if the key being set already exists
    with pytest.raises(KeyError):
        carton["foo"] = "baz"


def test_setitem_mutates_environ() -> None:
    """By default, Eggviron will mutate the os.environ as it changes"""
    carton = Eggviron()

    carton["owl"] = "lady"

    assert os.getenv("owl") == "lady"


def test_setitem_does_not_mutate_environ() -> None:
    """Eggviron will not mutate the os.environ when flag is flipped"""
    carton = Eggviron(mutate_environ=False)

    carton["owl"] = "lady"

    assert "owl" not in os.environ


def test_del_item(carton: Eggviron) -> None:
    """Remove an existing item on del keyword use."""
    del carton["foo"]

    assert "foo" not in carton


def test_delitem_mutates_environ() -> None:
    """By default, Eggviron will mutate the os.environ as it changes"""
    carton = Eggviron()
    carton["owl"] = "lady"

    del carton["owl"]

    assert "owl" not in os.environ


def test_delitem_does_not_mutate_environ() -> None:
    """Eggviron will not mutate the os.environ when flag is flipped"""
    carton = Eggviron(mutate_environ=False)
    os.environ["owl"] = "lady"
    carton["owl"] = "lady"

    del carton["owl"]

    assert "owl" not in carton
    assert "owl" in os.environ


def test_load_with_multiple_loaders_strict_raises(carton: Eggviron) -> None:
    # In strict mode (default) conflicting keys should raise
    loader_one = MockLoader({"luz": "human"})
    loader_two = MockLoader({"luz": "good witch"})

    with pytest.raises(KeyError):
        carton.load(loader_one, loader_two)


def test_load_with_multiple_loaders_not_strict() -> None:
    # Multiple loaders should overwrite the loaded values of the prior
    carton = Eggviron(raise_on_overwrite=False)
    loader_one = MockLoader({"luz": "human", "owl": "lady"})
    loader_two = MockLoader({"luz": "good witch", "boiling": "sea"})

    carton.load(loader_one, loader_two)
    values = carton.loaded_values

    assert values["luz"] == "good witch"
    assert values["owl"] == "lady"
    assert values["boiling"] == "sea"


def test_loader_mutates_environ() -> None:
    """By default, Eggviron will mutate the os.environ as it changes"""
    carton = Eggviron()
    loader = MockLoader({"luz": "human"})

    carton.load(loader)

    assert os.getenv("luz") == "human"


def test_loader_does_not_mutate_environ() -> None:
    """Eggviron will not mutate the os.environ when flag is flipped"""
    carton = Eggviron(mutate_environ=False)
    loader = MockLoader({"luz": "human"})

    carton.load(loader)

    assert "luz" not in os.environ


def test_loader_debug_logging(caplog: pytest.LogCaptureFixture) -> None:
    # Ensure when logging is DEBUG the masked loaded values are logged
    carton = Eggviron()
    loader_one = MockLoader({"owl": "lady"})
    loader_two = MockLoader({"luz": "good witch", "boiling": "sea"})

    with caplog.at_level("DEBUG"):

        carton.load(loader_one, loader_two)

    assert "MockLoader loaded, owl : ****" in caplog.text
    assert "MockLoader loaded, luz : ****itch" in caplog.text
    assert "MockLoader loaded, boiling : ****" in caplog.text


@pytest.mark.parametrize(
    "method, key, expected",
    (
        ("get", "foo", "bar"),
        ("get_int", "answer", 42),
        ("get_float", "funny_number", 69.420),
        ("get_bool", "we_are_so_back", True),
    ),
)
def test_get_methods_return_expected_value(
    method: str,
    key: str,
    expected: str | int | float | bool,
    carton: Eggviron,
) -> None:
    # Paramaterized to test all get methods
    # .get("foo") should work the same as ["foo"] when the key exists
    value = getattr(carton, method)(key)

    assert value == expected


@pytest.mark.parametrize(
    "method, expected",
    (
        ("get", "goblins"),
        ("get_int", 37337),
        ("get_float", 3.14),
        ("get_bool", False),
    ),
)
def test_get_methods_return_default_when_key_not_exists(
    method: str,
    expected: str,
    carton: Eggviron,
) -> None:
    # Like .get() on dictionaries, return the default if provided
    # when the key doens't exist.
    value = getattr(carton, method)("missing_key", expected)

    assert value == expected


@pytest.mark.parametrize(
    "method",
    (
        ("get"),
        ("get_int"),
        ("get_float"),
        ("get_bool"),
    ),
)
def test_get_methods_raise_keyerror_when_key_not_exists(
    method: str,
    carton: Eggviron,
) -> None:
    # Unlike dictionaries, if the default value is not provided None will not
    # be returned. Eggviron enforces a string return value.
    with pytest.raises(KeyError):
        getattr(carton, method)("missing_key")


@pytest.mark.parametrize(
    "method, default",
    (
        ("get", 42),
        ("get_int", 3.13),
        ("get_float", 0),
        ("get_bool", "true"),
    ),
)
def test_get_methods_raise_typeerror_on_invalid_default(
    method: str,
    default: str,
    carton: Eggviron,
) -> None:
    # Type guarding the default value to ensure .get() always returns correct type
    with pytest.raises(TypeError):
        getattr(carton, method)("foo", default)


@pytest.mark.parametrize(
    "method, key",
    (
        ("get_int", "foo"),
        ("get_float", "foo"),
        ("get_bool", "foo"),
    ),
)
def test_get_methods_raise_valueerror_on_convert_error(
    method: str,
    key: str,
    carton: Eggviron,
) -> None:
    # If the value cannot be converted to the requested type, raise ValueError
    with pytest.raises(ValueError):
        getattr(carton, method)(key)


def test_get_int_fails_when_value_is_float(carton: Eggviron) -> None:
    # We do not want type coercion to happen
    with pytest.raises(ValueError):
        carton.get_int("funny_number")


def test_get_float_fails_when_value_is_ing(carton: Eggviron) -> None:
    # We do not want type coercion to happen
    with pytest.raises(ValueError):
        carton.get_float("answer")
