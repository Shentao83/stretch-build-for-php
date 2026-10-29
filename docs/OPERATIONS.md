# Manual integration and rollback

The repository deliberately stops at building and synthetic testing. A target
host's users, paths, web-server configuration, cron jobs and service management
must be assessed separately. There is no universal production installer here.

## Staging integration

Build at the final absolute work path on a compatible staging VM. Record the
build report and package inventory. Verify CLI extensions, effective INI,
dynamic libraries and actual application behavior under both CLI and FPM.

Use a dedicated service identity and private writable paths for sockets, PID,
logs, sessions, uploads and temporary files. The included FPM template is a
short-lived unprivileged smoke-test configuration, not a production pool.
Run only `run-php`/`run-fpm` launchers to select the intended private runtime.

Do not point the synthetic test pool at a production application or give it
production credentials. Choose an explicit timezone and review session,
upload, disabled-function, OPcache and ImageMagick policies for the application.

## Rollback plan

Before a separately planned cutover, save the original service/pool/web-server
configuration and record the original executable paths. Confirm a restore of
the application and database backups independently of this runtime change.

If staging or a later authorized cutover fails:

1. Stop the dedicated candidate service and confirm its workers have exited.
2. Restore the recorded original routing and executable configuration.
3. Start/reload the original services as required by the reviewed change plan.
4. Recheck health, login, background tasks and integrations with the original runtime.
5. Preserve failure logs privately for diagnosis before removing candidate files.

Do not delete a runtime used by live processes. This repository provides no
automatic service switch, `dpkg-divert`, rollback timer or deletion command.
The smoke test stops its own child process before cleaning its temporary paths.
Removing a private build does not undo separately made service changes.
