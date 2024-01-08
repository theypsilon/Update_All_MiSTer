# Manual Testing

To manual test Update All, there are a couple of helpers, depending on what you want to do.

Here I guide you through the different methods. We'll always assume that you start at the root folder of this repository

- If you want to test it on MiSTer:
  - a. Write your MiSTer ip on *mister.ip*
  - b. Optionally, ff you have a different password, write it on *mister.pw*
  - c. Run `./src/debug.sh` to send a runnable copy of Update All to */media/fat/update_all.sh*
  - d. Access your MiSTer via ssh, and run */media/fat/update_all.sh*
  - e. Optionally, if you want to run specific routines add the specific environment variable that is defined in the *_test_routine* of the *UpdateAllService* class.
  - f. Optionally, you may also export `DEBUG=true` or `BENCH=true` to get a more verbose output.
  - g. Alternativelly, instead of the step (c), you may run `./src/debug.sh run` to run the new build on MiSTer without having to ssh into it manually, thus skipping step (d).

- If you want to test it on your development machine: Just run `./src/run_on_delme_folder.sh` and everything will be installed on a new *delme* folder.
