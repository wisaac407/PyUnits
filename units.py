# Base dimensions
TIME        = 1
LENGTH      = 2
MASS        = 3
SUBSTANCE   = 4
LUMINOUS    = 5
CURRENT     = 6
TEMPERATURE = 7

DIM_NAMES = {
    TIME:        'time',
    LENGTH:      'length',
    MASS:        'mass',
    SUBSTANCE:   'substance',
    LUMINOUS:    'luminous',
    CURRENT:     'current',
    TEMPERATURE: 'temperature'
}

USE_UNICODE = True

DIMENSIONLESS = {
    TIME:        0,
    LENGTH:      0,
    MASS:        0,
    SUBSTANCE:   0,
    LUMINOUS:    0,
    CURRENT:     0,
    TEMPERATURE: 0,
}


def _dimensions(dims):
    dim = DIMENSIONLESS.copy()
    dim.update(dims)
    return dim


DIMENSION_NAMES = {
    # Start with the base units
    'time': _dimensions({TIME: 1}),
    'length': _dimensions({LENGTH: 1}),
    'mass': _dimensions({MASS: 1}),
    'substance': _dimensions({SUBSTANCE: 1}),
    'luminous intensity': _dimensions({LUMINOUS: 1}),
    'electrical current': _dimensions({CURRENT: 1}),
    'temperature': _dimensions({TEMPERATURE: 1}),

    # Common units of measure
    'velocity': _dimensions({LENGTH: 1, TIME: -1}),
    'acceleration': _dimensions({LENGTH: 1, TIME: -2}),
    'momentum': _dimensions({LENGTH: 1, TIME: -1, MASS: 1}),
    'force': _dimensions({LENGTH: 1, TIME: -2, MASS: 1}),
    'energy': _dimensions({LENGTH: 2, TIME: -2, MASS: 1}),
}


def get_unicode_exp(exp):
    """Format the exponent as a unicode string"""
    char_map = {
        '1': '\u00B9',
        '2': '\u00B2',
        '3': '\u00B3',
        '4': '\u2074',
        '5': '\u2075',
        '6': '\u2076',
        '7': '\u2077',
        '8': '\u2078',
        '9': '\u2079',
        '0': '\u2070',
        '-': '\u207B'
    }
    s = ''
    chars = list(str(exp))
    for c in chars:
        s += char_map[c]
    return s


def format_unit_str(units):
    """Format the units as a string"""
    if USE_UNICODE:
        s = ''
        for unit, exp in units:
            s += unit
            s += get_unicode_exp(exp)
        return s
    else:
        return '*'.join(unit + '^%s' % exp for unit, exp in units)


class IncompatibleUnitsError(TypeError):
    """Raised when trying to convert a unit to another that is not dimentionally equivilant"""


class UnitMeta(type):
    def __new__(cls, name, bases, attrs):
        # Dict of dimensions and their corresponding exponents
        dim = DIMENSIONLESS.copy()
        dim.update(attrs.get('_dimensions', {}))

        attrs['_dimensions'] = dim

        return type.__new__(cls, name, bases, attrs)


class Unit(object, metaclass=UnitMeta):
    """Base class for all units"""

    def __init__(self, value):
        if isinstance(value, (int, float)):
            self._set_value(value)
        elif isinstance(value, Unit):
            if value._dimensions == self._dimensions:
                self._value = value._value
            else:
                raise IncompatibleUnitsError("Units %s and %s are not compatible" %
                                             (self.__class__, value.__class__))
        else:
            raise TypeError("Type %s is not a value" % value.__class__)

    def __repr__(self):
        if USE_UNICODE:
            return '%s%s' % (self._get_value(), self._get_symbol())
        return '%s%s' % (self._get_value(), self._get_symbol())

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(self._get_value() * other)
        elif isinstance(other, Unit):
            valSI = self._value * other._value
            dimensions = self._dimensions.copy()
            for dim, exp in dimensions.items():
                dimensions[dim] = exp + other._dimensions[dim]

            if not any(list(zip(*dimensions.items()))[1]):
                return valSI

            return CompoundUnit(valSI, dimensions)
        else:
            return TypeError("Cannot multiply unit by type %s" % other.__class__)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(self._get_value() / other)
        elif isinstance(other, Unit):
            valSI = self._value / other._value
            dimensions = self._dimensions.copy()
            for dim, exp in dimensions.items():
                dimensions[dim] = exp - other._dimensions[dim]

            if not any(list(zip(*dimensions.items()))[1]):
                return valSI

            return CompoundUnit(valSI, dimensions)
        else:
            return TypeError("Cannot divide unit by type %s" % other.__class__)

    def __rtruediv__(self, other):
        # rdiv will not be called with another unit
        if isinstance(other, (int, float)):
            valSI = self._convert_to_SI(other / self._get_value())
            dimensions = self._dimensions.copy()
            for dim, exp in dimensions.items():
                dimensions[dim] = -exp

            return CompoundUnit(valSI, dimensions)
        else:
            return TypeError("Type %s cannot divide unit" % other.__class__)

    def __add__(self, other):
        if isinstance(other, Unit):
            if other._dimensions == self._dimensions:
                # Add the SI values, convert to this unit and create a new instance
                return self.__class__(self._convert_from_SI(self._value + other._value))
            else:
                raise IncompatibleUnitError("Cannot add %s and %s" %
                                            (self.__class__, other.__class__))
        else:
            raise TypeError("Type %s is not a unit" % other.__class__)

    def __sub__(self, other):
        if isinstance(other, Unit):
            if other._dimensions == self._dimensions:
                # Add the SI values, convert to this unit and create a new instance
                return self.__class__(self._convert_from_SI(self._value - other._value))
            else:
                raise IncompatibleUnitError("Cannot add %s and %s" %
                                            (self.__class__, other.__class__))
        else:
            raise TypeError("Type %s is not a unit" % other.__class__)

    def _get_value(self):
        return self._convert_from_SI(self._value)

    def _set_value(self, value):
        self._value = self._convert_to_SI(value)

    def _get_symbol(self):
        return self._symbol

    # Convert the input value to the SI equivalent for internal storage
    def _convert_to_SI(self, value):
        return value

    # Convert the SI value to the output value
    def _convert_from_SI(self, value):
        return value

    def get_dimensions(self):
        units = []
        for dim, exp in self._dimensions.items():
            if exp != 0:
                units.append((DIM_NAMES[dim], exp))
        return format_unit_str(units)

    def get_unit_type(self):
        for typ, dim in DIMENSION_NAMES.items():
            if self._dimensions == dim:
                return typ
        return "complex type"


# Base SI units
class Second(Unit):
    _symbol = 's'
    _dimensions = {TIME: 1}


class Meter(Unit):
    _symbol = 'm'
    _dimensions = {LENGTH: 1}


class Kilogram(Unit):
    _symbol = 'kg'
    _dimensions = {MASS: 1}


class Mole(Unit):
    _symbol = 'mol'
    _dimensions = {SUBSTANCE: 1}


class Candela(Unit):
    _symbol = 'cd'
    _dimensions = {LUMINOUS: 1}


class Ampere(Unit):
    _symbol = 'A'
    _dimensions = {CURRENT: 1}


class Kelvin(Unit):
    _symbol = 'K'
    _dimensions = {TEMPERATURE: 1}


SI_BASE_UNITS = {
    TIME:        Second,
    LENGTH:      Meter,
    MASS:        Kilogram,
    SUBSTANCE:   Mole,
    LUMINOUS:    Candela,
    CURRENT:     Ampere,
    TEMPERATURE: Kelvin
}


class CompoundUnit(Unit):
    """Mixed unnamed unit"""

    def __init__(self, value, dimensions):
        self._dimensions = dimensions

        Unit.__init__(self, value)

        units = []
        for dim, exp in dimensions.items():
            if exp != 0:
                units.append((SI_BASE_UNITS[dim]._symbol, exp))
        self._symbol = format_unit_str(units)


# Derived SI units
class Newton(Unit):
    _symbol = 'N'
    _dimensions = {
        MASS: 1,
        LENGTH: 1,
        TIME: -2
    }


class Joule(Unit):
    _symbol = 'J'
    _dimensions = {
        MASS: 1,
        LENGTH: 2,
        TIME: -2
    }


class Kilometer(Unit):
    _symbol = 'km'
    _dimensions = {LENGTH: 1}

    def _convert_to_SI(self, value):
        return value * 1000.0

    def _convert_from_SI(self, value):
        return value / 1000.0


class Gram(Unit):
    _symbol = 'g'
    _dimensions = {MASS: 1}

    def _convert_to_SI(self, value):
        return value / 1000.0

    def _convert_from_SI(self, value):
        return value * 1000.0


class DegreesCelsius(Unit):
    _symbol = 'C'
    _dimensions = {TEMPERATURE: 1}

    def _convert_to_SI(self, value):
        return value + 273.15

    def _convert_from_SI(self, value):
        return value - 273.15
