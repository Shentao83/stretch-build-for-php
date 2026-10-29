# Third-party notices and license scope

This source repository contains original scripts, tests, configuration examples
and documentation under the MIT license in LICENSE. It contains no vendored
upstream source, patch contents, binary dependencies or third-party license files.

The build downloads the unchanged PHP upstream mitigation and other inputs into
an ignored local cache, verifies their pinned checksums, and applies the patch
locally. The upstream commit's attribution remains in the downloaded original.
The mitigation is by Arnaud Le Blanc and Ilija Tovilo; see docs/PROVENANCE.md.

Downloaded PHP and Zend Engine sources retain their original licenses and
per-file notices. Other downloaded dependencies retain their respective licenses.
The MIT license for this repository does not relicense any downloaded input.
Any later redistribution of generated source or binaries requires retaining
the applicable notices and fulfilling the corresponding license obligations.

The source-only repository makes no binary redistribution claim. A separate
review is required before publishing any generated runtime or dependency archive.
This recipe is independent of the PHP Group, Zend and Debian.
