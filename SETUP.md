# Install

Copy README.md, STATIC.md, .gitattributes, cards/, assets/, data/, fonts/, scripts/, and .github/workflows/update-profile.yml into the ahmadsyahani/ahmadsyahani repository. Keep existing unrelated files and workflows.

Commit and push, then run **Actions → Refresh profile cards → Run workflow**. The workflow refreshes the avatar, repository counts, project metadata, and contribution chart daily at 13:17 WIB. GitHub may delay scheduled runs. Scheduled workflows run on the default branch and can be disabled after extended repository inactivity.

If commits fail, enable read and write workflow permissions in repository Settings → Actions → General. Branch protection may require a pull request instead of a direct bot commit.

To regenerate locally:

```sh
pip install -r scripts/requirements.txt
python scripts/render.py --refresh
```

Use `python scripts/render.py` to regenerate from the saved data without network access. Edit the hero text and `selected` list in scripts/render.py to change the introduction and featured repositories.

Catfolio uses warm white, moss green, and the cat avatar from the public GitHub profile. Its compact composition follows the original reference: hero, contribution calendar, monthly activity, three specialty tiles, and three repository cards. Full-width sections use 44 px padding on desktop and 28 px on mobile. SVG canvases include 20 px row separation and desktop column gutters of 15 px. Narrow screens use dedicated mobile SVGs through picture/source, including a compact side-by-side name and cat portrait.

Headings and body text use the official Google Sans Flex font, converted into vector outlines with FontTools. This preserves the typeface without remote fonts or an installed font on the visitor's computer. The ASCII portrait retains a monospace font so character columns stay aligned. ASCII and sibling-card entrances play once. Heatmap and monthly-chart animations repeat on seven-second cycles, with a completed hold between reveals. Reduced motion disables all animation. The top Pause animations link opens STATIC.md, whose SVGs have no animation rules. SVGs require no JavaScript. Hashed filenames in cards/versions and cards/static/versions refresh when generated artwork changes. Old generated versions are replaced on regeneration. Versions are in the filename because GitHub raw redirects discard query parameters.

The generator is Python. HTML in README.md only arranges the resulting SVG images. The cached GitHub contribution page is HTML and is larger than the Python source; .gitattributes marks cached inputs and generated artwork so GitHub Linguist can exclude them from source language statistics. GitHub recalculates those statistics asynchronously.

The font is bundled under the SIL Open Font License in fonts/OFL.txt. Source: https://github.com/google/fonts/tree/main/ofl/googlesansflex. No personal statistics or visual assets from Avi's profile are included.
