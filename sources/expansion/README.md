# Additional researched designs

The eight retained additions cover existing card types in China, Japan, France
and Singapore. They recreate documented physical card fronts rather
than invented recolors. `research.json` records issuer, operator, authorized
seller or physical marketplace evidence, source images and crop instructions.
Retained references are preserved in `references/`. Historical metadata remains
in the JSON reports; retired image files and the Sanrio PDF have been removed.

| Card | Design | Reference |
| --- | --- | --- |
| `cn/2900` | Interconnectivity 10th Anniversary | Official Shanghai card shop |
| `cn/1000` | I Love You China: Reform and Opening Up | Beijing Yikatong issue photographs |
| `cn/5810` | First National Issue: Five Rams | Guangzhou release announcement |
| `cn/5840` | Persimmons of Good Fortune | Shenzhen Tong issuer |
| `jp/suica` | Welcome Suica cherry blossoms | JR East issuer |
| `jp/icoca` | Wind and Thunder Gods | JR West issuer and physical retailer photo |
| `fr/la-carte` | Tour de France 2024 yellow jersey | Lignes d'Azur operator announcement and press photographs |
| `sg/ezlink` | Singapore Skyline | Physical-card retailer listing |

These are visual choices for existing card types. The Singapore listing titles
describe inspected physical cards; their issuer collection names and release
dates are not asserted. The initially researched Disney riverboat candidate
produced two native-tool rejections and no image; its unused reference images
have also been removed. Singapore Skyline remains available.

Native built-in ImageGen recreates each reference in a flat vector style, then
edits the recreation to remove ordinary lettering. The normal design ID is
the cleaned choice; `<design>-text` retains the main actual lettering. Card
serials, QR codes and legal microprint are omitted from both.

The Shanghai anniversary's large `10` and Shenzhen's central calligraphy are
integral decorative artwork.
Their normal variants retain those elements while removing ordinary labels.
Each also offers a `<design>-no-text` alternative with all lettering removed.

`generation.json` records the native prompts, output hashes and final exports.
The published PNGs and compact source inputs are the same validated files.
Denoising is disabled for these inputs so rebuilding preserves their pixels.
The repository's optimizer enforces the 30:19 aspect ratio, at most 24 colors
and fewer than 40,000 bytes per published face.

The [curation report](../curation/README.md) records the four retired expansion
families, the two earlier Korean character families, and removed reference
files. Retained artwork, including all defaults and Octopus, is unchanged.
