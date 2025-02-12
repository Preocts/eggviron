from __future__ import annotations

import contextlib
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol

    class Loader(Protocol):
        @property
        def name(self) -> str: ...
        def run(self) -> dict[str, str]: ...


_BOOLEAN_CONVERTION = {
    "true": True,
    "1": True,
    True: True,
    "false": False,
    "0": False,
    False: False,
}


@contextlib.contextmanager
def _handle_exception(_type: type) -> Generator[None, None, None]:
    """
    Handle KeyError and ValueError as expected while getting values from loaded_values.

    Args:
        _type: The expected final type of the value being fetched

    Returns:
        None

    Raises:
        TypeError: If default is provided but is not an bool
        KeyError: If the key is not present and the default value is None
    """
    try:
        yield None

    except KeyError as err:
        msg = f"Requested key '{err}' does not exist and no default was provided."
        raise KeyError(msg) from None

    except ValueError:
        msg = f"Failed to convert value to a '{_type.__name__}'"
        raise ValueError(msg) from None


def _validate_default_type(obj: object | None, _type: type) -> None:
    """
    Validate that the given obj is an instance of the given type. This check is skipped if obj is None.

    Args:
        obj: Any object
        _type: Any single type to check for isinstance()

    Returns:
        None

    Raises:
        TypeError: When obj is not an instance of _type
    """
    if obj is not None and not isinstance(obj, _type):
        msg = f"Expected a {_type.__name__} for 'default', given {type(obj).__name__}."
        raise TypeError(msg)


class Eggviron:
    """A key-value store optionally loaded from the local environment and other sources."""

    def __init__(self, *, raise_on_overwrite: bool = True) -> None:
        """
        Create an empty Eggviron.

        Keyword Args:
            raise_on_overwrite: If True a KeyError will be raised when an existing key
            is overwritten by an assignment or load() action.
        """
        self._strict = raise_on_overwrite
        self._loaded_values: dict[str, str] = {}

    @property
    def loaded_values(self) -> dict[str, str]:
        return self._loaded_values.copy()

    def __getitem__(self, key: str) -> str:
        """
        Get a loaded value by key.

        Args:
            key: Key to lookup for requested value

        Returns:
            str

        Raises:
            KeyError
        """
        return self._loaded_values[key]

    def __setitem__(self, key: str, value: str) -> None:
        """
        Set a value assigned to a key. The key and value must be a string.

        Args:
            key: Key index of the value
            value: Value stored at the provided key index

        Returns:
            None

        Raises:
            ValueError: If the key or value are not a string
            KeyError: If key already exists and raise_on_overwrite is True
        """
        if key in self._loaded_values:
            msg = f"Key '{key}' already exists."
            raise KeyError(msg)

        _validate_default_type(key, str)
        _validate_default_type(value, str)

        self._loaded_values[key] = value

    def load(self, *loader: Loader) -> None:
        """
        Use a loader to update the loaded values. Loaders are used in the order provided.

        Args:
            loader: The loader classes to use. More than one can be provided.
        """
        for _loader in loader:
            if self._strict:
                results = _loader.run()
                conflicts = [key for key in results if key in self._loaded_values]
                if conflicts:
                    msg = f"Key '{conflicts[0]}' already exists. Offending loader: '{_loader.name}'"
                    raise KeyError(msg)

            self._loaded_values.update(_loader.run())

    @_handle_exception(str)
    def get(self, key: str, default: str | None = None) -> str:
        """
        Get a value from the Eggviron.

        If default is provided and the key is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be a string

        Raises:
            TypeError: If default is provided but not as a string
            KeyError: If the key is not present and the default value is None
        """
        _validate_default_type(default, str)

        value = self._loaded_values.get(key, default)
        if value is None:
            raise KeyError(key)

        return value

    @_handle_exception(int)
    def get_int(self, key: str, default: int | None = None) -> int:
        """
        Get a value from Eggviron, converting it to an int.

        If default is provided and the key is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be an int

        Raises:
            ValueError: If the discovered value cannot be converted to an int
            TypeError: If default is provided but is not an int
            KeyError: If the key is not present and the default value is None
        """
        _validate_default_type(default, int)

        value = self._loaded_values.get(key, default)
        if value is None:
            raise KeyError(key)

        return int(value)

    @_handle_exception(float)
    def get_float(self, key: str, default: float | None = None) -> float:
        """
        Get a value from Eggviron, converting it to an float.

        If default is provided and the key is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be a float

        Raises:
            ValueError: If the discovered value is not a float
            TypeError: If default is provided but is not a float
            KeyError: If the key is not present and the default value is None
        """
        _validate_default_type(default, float)

        fetch_value = self._loaded_values.get(key)

        if fetch_value is None and default is not None:
            return default

        elif fetch_value is None:
            raise KeyError(key)

        elif fetch_value.isdigit():
            raise ValueError()

        return float(fetch_value)

    @_handle_exception(bool)
    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """
        Get a value from Eggviron, converting it to an bool.

        Valid boolean values are "true", "false", "1", "0" (case insensitive)

        If default is provided and the key is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be an bool

        Raises:
            ValueError: If the discovered value cannot be converted to an bool
            TypeError: If default is provided but is not an bool
            KeyError: If the key is not present and the default value is None
        """
        _validate_default_type(default, bool)

        _value = self._loaded_values.get(key, default)
        if _value is None:
            raise KeyError(key)

        value = _BOOLEAN_CONVERTION.get(_value)
        if value is None:
            raise ValueError()

        return value
