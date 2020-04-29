# Copyright 2008 Mike Wakerly <opensource@hoho.com>
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

"""Various unit conversion routines."""

from past.builtins import cmp
from builtins import object
from future.utils import raise_
import types

from . import util
from future.utils import with_metaclass

UNITS = util.Enum(*(
  'Liter',
  'Milliliter',
  'Microliter',
  'Ounce',
  'Pint',
  'USGallon',
  'ImperialGallon',
  'TwelveOunceBeer',
  'HalfBarrelKeg',
  'KbMeterTick', # aka Vision2000 (2200 pulses/liter)
  'PonyKeg',
  'Cup',
  'Quart',
  'Hogshead',
))

# This constant defines the unit type used for the database "volume" field
RECORD_UNIT = UNITS.Milliliter

CONVERSIONS = {
    (UNITS.Milliliter, UNITS.KbMeterTick) : 2.2,
    (UNITS.Liter, UNITS.Milliliter) : 1e3,
    (UNITS.Liter, UNITS.Microliter) : 1e6,
    (UNITS.Liter, UNITS.Ounce) : 33.8140227,
    (UNITS.USGallon, UNITS.Ounce) : 128.0,
    (UNITS.Cup, UNITS.Ounce) : 8.0,
    (UNITS.HalfBarrelKeg, UNITS.USGallon) : 15.5,
    (UNITS.HalfBarrelKeg, UNITS.PonyKeg) : 2.0,
    (UNITS.Pint, UNITS.Ounce) : 16.0,
    (UNITS.TwelveOunceBeer, UNITS.Ounce) : 12.0,
    (UNITS.Hogshead, UNITS.USGallon) : 63.0,
    (UNITS.Quart, UNITS.Ounce) : 32.0,
    (UNITS.ImperialGallon, UNITS.Liter) : 4.54609,
}

class ConversionError(Exception):
  """Raised if a conversion is not possible"""

class _UnitConverter(object):
  def __init__(self, table):
    self._table = {}
    self._table.update(table)

    all_units = set()
    for unit_from, unit_to in list(table.keys()):
      all_units.add(unit_from)
      all_units.add(unit_to)

    # Generate reverse conversion factors for those given
    for k, v in table.items():
      unit_from, unit_to = k
      reverse_value = 1.0/v
      reverse_key = (unit_to, unit_from)
      # TODO: Should we assert if any existing value in the table does not match
      # computed value? For now, just skipping.
      if reverse_key not in self._table:
        self._table[reverse_key] = reverse_value

    unit_graph = util.SimpleGraph(list(self._table.keys()))

    # Generate all possible conversion factors
    for unit_from in all_units:
      for unit_to in all_units:
        if unit_from == unit_to:
          continue
        new_key = (unit_from, unit_to)
        if new_key in self._table:
          continue

        # Attempt to find a path to these units
        path = unit_graph.ShortestPath(unit_from, unit_to)
        if not path:
          # Not possible, just continue
          continue
        value = 1.0
        prev_unit = path[0]
        for unit in path[1:]:
          value = self.Convert(value, prev_unit, unit)
          prev_unit = unit
        self._table[new_key] = value

  def CanConvert(self, from_unit, to_unit):
    return (from_unit, to_unit) in self._table

  def Convert(self, amt, from_unit, to_unit):
    if from_unit == to_unit:
      return amt
    k = (from_unit, to_unit)
    if k not in self._table:
      raise_(ConversionError, "Don't know how to convert %s to %s" % (from_unit,
                                                                     to_unit))
    return float(amt) * self._table[k]

UnitConverter = _UnitConverter(CONVERSIONS)


class _QuantityMeta(type):
  def __init__(cls, name, bases, attr):
    super(_QuantityMeta, cls).__init__(name, bases, attr)
    for unit_name in UNITS.get_names():
      unit = getattr(UNITS, unit_name)
      prop_name = 'In' + unit_name + 's'
      def convert_fn(self, to_units=unit):
        return self.Amount(to_units)
      setattr(cls, prop_name, convert_fn)

class Quantity(with_metaclass(_QuantityMeta, object)):
  DEFAULT_UNITS = UNITS.Milliliter

  def __init__(self, amount, units=None, from_units=None):
    if units is None:
      units = self.DEFAULT_UNITS
    self._units = units
    if from_units is None:
      from_units = self._units
    self._amount = UnitConverter.Convert(amount, from_units, self.units())

  def __add__(self, other, subtract=False):
    val = 0
    if isinstance(other, (int, float)):
      val += other
    elif isinstance(other, Quantity):
      val += other.Amount(self.units())
    else:
      raise TypeError
    if subtract:
      val = self.Amount() - val
    else:
      val += self.Amount()
    return Quantity(val, self.units())

  def __sub__(self, other):
    return self.__add__(other, subtract=True)

  def __cmp__(self, other):
    if isinstance(other, (int, float)):
      return cmp(self.Amount(), other)
    elif isinstance(other, Quantity):
      return cmp(self.Amount(), other.Amount(in_units=self.units()))
    else:
      raise TypeError

  # TODO: should have just subclassed float
  def __int__(self):
    return int(self.Amount())

  def __long__(self):
    return int(self.Amount())

  def __float__(self):
    return float(self.Amount())

  def units(self):
    return self._units

  def IncAmount(self, amt, units=None):
    if units is None:
      self._amount += amt
    else:
      self._amount += UnitConverter.Convert(amt, units, self.units())

  def SetAmount(self, amt, units=None):
    self._amount= 0
    self.IncAmount(amt, units)

  def Clear(self):
    self.SetAmount(0)

  def Amount(self, in_units=None):
    if in_units is None:
      in_units = self.units()
    return UnitConverter.Convert(self._amount, self.units(), in_units)
