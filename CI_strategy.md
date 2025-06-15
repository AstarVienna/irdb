# CI strategy for IRDB

A brief guide to how the CI works here, because it's getting rather complex already.

## Pull requests

### Into dev_master

* Run normal tests
* Run notebook tests when ready for review

Both using corresponding branches (with the same name) in ScopeSim and ScopeSim_Templates if available.

### Into master

* Run normal tests
* Run notebook tests

Both using released version of ScopeSim and ScopeSim_Templates, because once it's in master, it can and should become a new IRDB package release and those need to work with the released versions of the software.
For anything that requires changes in more than one place, please release the IRDB part last.
This means that e.g. the new version of ScopeSim should be compatible with both the old and the new version of the IRDB.

## Pushes

### To dev_master

* Run normal tests
* Run notebook tests

Both using main branches in ScopeSim and ScopeSim_Templates.
Useful to catch cases where PR base was out-of-date and PR CI passed but now might fail after merge.
Also useful to have up-to-date badge, see also schedule.

### To master

Tests?? Why actually?

Maybe at this point also re-run notebooks with output (the ones too long for RTD) and commit the changes, so that RTD shows the current state?

## Schedule

Do we want to run tests on schedule??
Might be useful to see if any change in Scopesim or ScopeSim_Templates (perhaps use main and release?) broke anything?
But maybe (only?) do that for master?
Or maybe a master + releases Sim&TP and dev_master + main Sim&TP??

For now, run dev_master + main Sim&TP nightly...

## Manually run tests

Notebook tests (currently METIS and MICADO) can be triggered manually with custom branches to use for ScopeSim and ScopeSim_Templates.
This allows to easily check a new branch there if it will destroy the notebooks, without the need to create a branch with the same name here, if there are no corresponding changes required.

## Ideas for badges

* Should be updated whenever something's changed in the yamls or dat files (anything else??).
* Ideally don't create a spam of commits with just badges.
* Perhaps notify in PRs (i.e. comment with changes, somehow), but only commit on push?
* Would be good to have commit corresponding to a PR in that PR, but only one in the end. Merge queue???

## Ideas for tags

* Maybe one day we can automate the creation and push of instrument package versions to the server.
* It's unclear where the tag itself would come from, perhaps still manually?
* The CI should get the instrument name from the tag, as well as dev/stable.
* In principle it should be able to just run the publish script, with non-personalized credentials stored in a GitHub secret.

## CI Badge?

Currently, the test status badge is created from dev_master.
Does this convey the right kind of information?
Or do we want to report on the status of master instead?
If yes, then we should perhaps add a scheduled run (if not anyway), otherwise this will just show the status of the last dev_master -> master merge.
