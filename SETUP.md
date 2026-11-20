# Install

Copy README.md, cards/, assets/, data/, scripts/, and .github/workflows/update-profile.yml into the ahmadsyahani/ahmadsyahani repository. Keep existing unrelated files and workflows.

Commit and push, then run **Actions → Refresh profile cards → Run workflow**. The workflow refreshes the avatar, repository counts, project metadata, and contribution chart daily at 13:17 WIB. GitHub may delay scheduled runs. Scheduled workflows run on the default branch and can be disabled after extended repository inactivity.

If commits fail, enable read and write workflow permissions in repository Settings → Actions → General. Branch protection may require a pull request instead of a direct bot commit.

To regenerate locally:

```sh
pip install -r scripts/requirements.txt
python scripts/render.py --refresh
```

Use `python scripts/render.py` to regenerate from the saved data without network access. Edit the hero text and `selected` list in scripts/render.py to change the introduction and featured repositories.

The ASCII portrait uses the cat avatar from the public GitHub profile. The hero fade animation runs once and respects reduced motion. Layout direction follows the supplied Avi Vashishta README reference; SVGs and generator are newly authored. No assets or personal statistics from the reference are included.
