# Tweakable, painless automatic banning of music traders for Nicotine+

> disclaimer: This plugin is vibe coded asf, use at your own peril. (it does work though)

This plugin:
- Detects and bans users whose music shares are predominantly private (ie: music traders)
- Focuses specifically on music files using file extension detection
- Configurable ban thresholds (default: ≥95% private music files)
- Optional custom messages to banned users
- Can ban users from uploads and/or search responses
- Automatically whitelists buddies

If you have suggestions or ideas, open a pull request or issue.

## Testimonals
A collection of some of the testimonials this plugin has received over a few days from professional Soulseek users!

`"just looked through your collection, absolute garbage most of it. So funny because that track you were sooooo precious about about 5 other people had it in wav you absolute chief. You're defo an old moody gitty that ain't getting none, pussy"` - Bruhyoumad

`"damn he hittin p or something"` - anon

## How It Works

The plugin uses two detection methods:

1. **Upload Detection**: When someone uploads from you, their share list is analyzed for music file ratios
2. **Search Detection**: Users with completely private search results are flagged as traders

**Music File Detection**: The plugin specifically counts music files (MP3, FLAC, WAV, OGG, etc.) rather than all files, making detection more accurate for music traders.

**Ban Criteria**:
- Users with ≥X% private music files (configurable threshold, default 95%)
- Users with completely private search results (search detection only)
- Minimum 1 public music file required to avoid false positives

## Settings

- **Ban Uploads**: Enable/disable banning from upload detection (default: enabled)
- **Ban Searches**: Enable/disable banning from search detection (default: enabled)
- **Send Messages**: Send ban message for upload-detected users (default: disabled)
- **Send Search Messages**: Send ban message for search-detected users (default: disabled)
- **Upload Message**: Custom message sent to traders banned from uploads
- **Search Message**: Custom message sent to traders banned from searches
- **Open Private Chat**: Open chat tabs when messaging (default: enabled)
- **Debug Logging**: Enable verbose logging for troubleshooting (default: disabled)
- **Private Threshold**: Percentage threshold for private music files (0-100, default: 95)

## Installation & Setup

You can either download a clone of the repository above, or use git to always fetch the latest changes if you know what you are doing.

To install open Nicotine+ settings, go to General > Plugins and click + Add Plugins. Then extract the folder to the opened ``nicotine\plugins`` as ``nicotine\plugins\trader_beamer``.
