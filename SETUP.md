# Install

Copy README.md, cards/, assets/, data/, fonts/, scripts/, and .github/workflows/update-profile.yml into the ahmadsyahani/ahmadsyahani repository. Keep existing unrelated files and workflows.

Commit and push, then run **Actions → Refresh profile cards → Run workflow**. The workflow refreshes the avatar, repository counts, project metadata, and contribution chart daily at 13:17 WIB. GitHub may delay scheduled runs. Scheduled workflows run on the default branch and can be disabled after extended repository inactivity.

If commits fail, enable read and write workflow permissions in repository Settings → Actions → General. Branch protection may require a pull request instead of a direct bot commit.

To regenerate locally:

```sh
pip install -r scripts/requirements.txt
python scripts/render.py --refresh
```

Use `python scripts/render.py` to regenerate from the saved data without network access. Edit the hero text and `selected` list in scripts/render.py to change the introduction and featured repositories.

Catfolio uses warm white, moss green, and the cat avatar from the public GitHub profile. Card padding is 56 px on desktop and 32 px on mobile, with 28 px transparent separation between rows. Narrow screens use dedicated mobile SVGs through picture/source.

Headings and body text use the official Google Sans Flex font, converted into vector outlines with FontTools. This preserves the typeface without remote fonts or an installed font on the visitor's computer. The ASCII portrait retains a monospace font so character columns stay aligned. The hero fade runs once and respects reduced motion.

The font is bundled under the SIL Open Font License in fonts/OFL.txt. Source: https://github.com/google/fonts/tree/main/ofl/googlesansflex. No personal statistics or visual assets from Avi's profile are included.
