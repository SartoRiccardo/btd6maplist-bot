# Changelog

## 2025-05-08 - 1.8.1

### Fixed
- `TypeError` in rejecting a submission due to not checking if webhooks are not `None`
- `await`ed a `Interaction.send_message`

## 2025-04-20 - 1.8.0

### Added
- Added `/best-of-the-best`, `/nostalgia-pack`
- Added BotB + NP information in every map-related command

### Changed
- Submitting completions to a map with multiple formats now asks which one you're submitting to

## 2025-02-27 - 1.7.1

### Changed
- File size increased to 5MB per image

### Fixed
- Bot actually removes Achivement Roles when it needs to

## 2025-02-25 - 1.7.0

### Added
- Bot syncs Achievement Roles

## 2024-11-11 - 1.6.0

### Added
- Added `CHANGELOG.md`
- Fuzzy search for all commands which take a `map` parameter

### Changed
- No longer checks perms through Discord roles, always checks either response `error` objects or `user.roles` arrays from `GET /users/{id}`