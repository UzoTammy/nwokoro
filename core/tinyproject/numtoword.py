"""Convert a whole number (0 to 999 trillion) into English words.

Style: British English, as used in Nigeria and Canada.

    21          -> Twenty-One
    101         -> One Hundred and One
    1001        -> One Thousand and One
    1100        -> One Thousand, One Hundred
    1000099     -> One Million and Ninety-Nine
    123456      -> One Hundred and Twenty-Three Thousand, Four Hundred and Fifty-Six

Rules:
  * Tens and units are hyphenated (Twenty-One).
  * "and" follows Hundred when something comes after it (One Hundred and Five).
  * Scale groups (Thousand, Million, ...) are separated by commas, except that the
    final group is joined with "and" when it is below one hundred.

The algorithm is recursive: a number is split at its largest scale into
`head x scale + rest`, and both parts are converted by the same function until
every piece is a word in the 28-entry lookup table below.
"""

LIMIT = 10 ** 15  # exclusive: the largest supported value is 999,999,999,999,999

UNIQUE = {
    0: 'Zero', 1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six',
    7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', 11: 'Eleven', 12: 'Twelve',
    13: 'Thirteen', 14: 'Fourteen', 15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen',
    18: 'Eighteen', 19: 'Nineteen', 20: 'Twenty', 30: 'Thirty', 40: 'Forty',
    50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', 90: 'Ninety',
}

# largest first, so the split always happens at the biggest scale present
SCALES = [
    (10 ** 12, 'Trillion'),
    (10 ** 9, 'Billion'),
    (10 ** 6, 'Million'),
    (10 ** 3, 'Thousand'),
]


def _words(n: int) -> str:
    """Words for 0 <= n < LIMIT. Recursive on the largest scale present."""
    if n in UNIQUE:
        return UNIQUE[n]

    if n < 100:
        tens, units = divmod(n, 10)
        return f'{UNIQUE[tens * 10]}-{UNIQUE[units]}'

    if n < 1000:
        hundreds, rest = divmod(n, 100)
        head = f'{UNIQUE[hundreds]} Hundred'
        return f'{head} and {_words(rest)}' if rest else head

    for size, name in SCALES:
        if n >= size:
            head, rest = divmod(n, size)
            text = f'{_words(head)} {name}'
            if not rest:
                return text
            joiner = ' and ' if rest < 100 else ', '
            return f'{text}{joiner}{_words(rest)}'

    raise AssertionError('unreachable')  # every n >= 1000 matches a scale


def normalise(figure) -> int:
    """Turn user input into an int, or raise.

    Accepts an int, or a string of ASCII digits with optional commas, spaces and
    leading zeros ("1,000", " 007 "). Raises ValueError for anything else (signs,
    decimals, letters, non-ASCII digits) and OverflowError at or above LIMIT.
    """
    if isinstance(figure, bool):
        raise ValueError('Whole numbers only.')
    if isinstance(figure, int):
        number = figure
    elif isinstance(figure, str):
        digits = figure.replace(',', '').replace(' ', '')
        if not digits:
            raise ValueError('Please enter a number.')
        digits = digits.lstrip('0') or '0'
        if not digits.isascii() or not digits.isdigit():
            raise ValueError('Whole numbers only: use the digits 0-9, optionally with commas.')
        if len(digits) > len(str(LIMIT - 1)):  # checked before int() so huge input stays cheap
            raise OverflowError('Limit exceeded: the largest supported number is 999 trillion.')
        number = int(digits)
    else:
        raise ValueError('Whole numbers only.')

    if number < 0:
        raise ValueError('Negative numbers are not supported.')
    if number >= LIMIT:
        raise OverflowError('Limit exceeded: the largest supported number is 999 trillion.')
    return number


def convert(figure) -> str:
    """Return `figure` in British English words, e.g. convert('1,001') -> 'One Thousand and One'.

    :param figure: an int, or a string of digits (commas, spaces and leading zeros allowed)
    :return: the number in words, Title Case
    :raises ValueError: if the input is not a non-negative whole number
    :raises OverflowError: if the number is 1,000 trillion or more
    """
    return _words(normalise(figure))
