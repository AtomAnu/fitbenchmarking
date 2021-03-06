.. _options:

#######################
FitBenchmarking Options
#######################

FitBenchmarking is controlled by a set of options that are set in 2 places.
In order from lowest priority to highest these are:

- The default options.
- An options file.

The default options are a complete set of options with sensible values.
These will be used when no other values are given for any of the options,
the values for these can be seen at the end of this document.

The options file must be a `.ini` formatted file
(`see here <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`__),
and a good reference for this can be
found in the examples, as well as at the bottom of this document.

----------------
Options template
----------------
This is a template you can use which contains information on each option
available, as well as the defaults.



.. include:: ../../../fitbenchmarking/utils/default_options.ini
   :literal:
