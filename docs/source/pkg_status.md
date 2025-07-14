# Definition of status keyword

This can be added optionally to both the top-level of an instrument's `default.yaml` or to a mode section therein. By convention, it usually goes after the "description" key.

## Permitted values and their meaning:

- concept: The package or mode is not yet implemented and exists merely as a placeholder or to collect resource needed to actually implement it. Selecting this mode will result in a `NotImplementedError`.
- experimental: Initial implementation of the package or mode is functional, but may still contain placeholders. Simulation results might not be representative of physical instrument.
- development: Mostly stable working prototype, using best-guess values for effect definitions and data. Simulation results should be relatively close to physical instrument.
- production: The package or mode is fully functional and stable and not expected to change substantially in the future. Simulation results are validated with reference documents.
- deprecated: No longer supported, selecting this mode or package will result in a `DeprecationWarning`.

The following values are currently under consideration to be added, but their role is not yet defined:

- engineering

## Combining package and mode statuses

Basically, a package should only be marked as being in "production" status if all modes also have this status (except deprecated modes). A package in "development" status can contain modes of all statuses. In a "deprecated" package, all modes are implicitly considered deprecated. A package still in "concept" status should only contain modes of the same status. Once one mode is at least "experimental" (and thus functional), the whole package should be marked with the same status (otherwise it cannot be used), but other modes may very well still be in "concept" stage.
