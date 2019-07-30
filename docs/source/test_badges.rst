Test Badges
===========
For every test run to check the consistency of files in the package, an entry
should be added to the ``badges.yaml`` file. This file is then read when the
docs are created an a reports page is built, showing the status of all the tests

Badges yaml structure
---------------------
The badges nested dictionary follows the following structure::

    <INSTRUMENT> :
        <test_category> :
            <test_name> : True/False

Badges can be added to the ``BADGES`` object (see below) using the "bang-key"
format::

    BADGES["!MICADO.structure.yaml_test"] = False

Adding Badge entries to tests
-----------------------------
At the beginning of a ``test_file.py`` the following line should be included::

    from .utils import load_badge_yaml
    BADGES = load_badge_yaml()

``BADGES`` is a ``SystemDict``, much like the one used in ``ScopeSim``. Hence
any nested yaml dict entry can be accessed with the "bang-key" format::

    BADGES["!MICADO.structure.yaml_test"] = False

Each ``test_file.py`` should also contain the following function to write the
``BADGES`` dictionary back to disk::

    def teardown_module():
        from utils import write_badge_yaml
        write_badge_yaml(BADGES)




