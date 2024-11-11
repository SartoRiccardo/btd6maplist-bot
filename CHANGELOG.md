# Changelog

## 2024-11-11 - 1.6.0

### Added
- Added `CHANGELOG.md`
- Fuzzy search for all commands which take a `map` parameter

### Changed
- No longer checks perms through Discord roles, always checks either response `error` objects or `user.roles` arrays from `GET /users/{id}`