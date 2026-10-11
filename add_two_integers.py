def add_two_integers(a: int, b: int) -> int:
    """
    Add two integers and return the result.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of the two integers

    Examples:
        >>> add_two_integers(2, 3)
        5
        >>> add_two_integers(-1, 1)
        0
    """
    return a + b


if __name__ == "__main__":
    import doctest
    doctest.testmod()
