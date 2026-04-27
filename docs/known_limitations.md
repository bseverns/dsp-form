# Known Limitations

This starter repo is intentionally modest.

## Current limits

- The Python generators are first-pass grammars, not final sculpture systems.
- STL/3MF export is planned but not yet wired into the CLI.
- Mesh repair is optional and conservative.
- Blender rendering is provided as a script, not as a fully polished preview system.
- Processing sketch is a teaching stub, not a full audio input system.
- Control trace input is documented but not yet implemented.

## Design choice

The repo starts with plain, inspectable code instead of a clever abstraction layer. That is intentional. The first goal is to make the pipeline understandable enough to teach, debug, and extend.
