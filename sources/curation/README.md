# Artwork curation

On November 1, 2026 the collection retired six dominant licensed character or
contemporary artist design families, including every text and no-text variant.
Two shop-promotion text alternatives are also retired, and their cleaned designs
are replaced with original generic SVG color blocks. The downloadable collection
now contains **40 card types and 121 faces** with **15 retirement redirects**.
Removal was chosen instead of generating recognizable character silhouettes.
Standard issuer transit artwork, including all six Octopus exports, is retained.

| Card | Retired design IDs | Faces | Replacement |
| --- | --- | ---: | --- |
| PASMO | `passport-sanrio`, `passport-sanrio-text`, `passport-sanrio-no-text` | 3 | PASMO default |
| T-money | `ryan`, `ryan-text` | 2 | T-money default |
| T-money | `apeach`, `apeach-text` | 2 | T-money default |
| T-money | `kpass-line-friends`, `kpass-line-friends-text` | 2 | T-money default |
| U-Money | `britto-einstein`, `britto-einstein-text` | 2 | U-Money default |
| EZ-Link | `hello-kitty-merlion`, `hello-kitty-merlion-text` | 2 | EZ-Link default |
| EZL | `duty-free-text` | 1 | EZL default |
| EZL | `myeongdong-text` | 1 | EZL default |

All 15 published faces and 15 build sources were removed. Cleanup also removes
13 reference images and one PDF containing retired characters or artwork.
These include two unused Disney riverboat references from a rejected candidate.
Historical URLs, text prompts, hashes and generation reports remain as records;
their old preservation counts describe those historical operations. They are
not an inventory of the current downloadable collection.

## Generic replacements and coupon audit

The stable ID `kr/ezl/duty-free` now displays **Graphite and lime**, using two
solid rectangles. `kr/ezl/myeongdong` now displays **Navy and citron**, using
solid vertical color bands. Both use original SVG geometry with no text,
embedded images, external assets, logos, coupon ribbons, redemption values,
benefits or promotions. Their compact source and published PNGs are identical,
1200 x 760, exactly two colors and 551/554 bytes respectively. Their original
promotional `-text` faces and high-resolution image masters are deleted.

The two generic SVG masters are in `sources/kr/ezl/`. Re-export them with:

```
python3 tools/generic_blocks.py
```

This uses `rsvg-convert` (librsvg) and the existing optimizer, with denoising
disabled. No image model or coupon recreation is involved.

POP Cashbee and Jeonju's two-day transit pass were visually inspected and
retained. POP contains ordinary card-family branding; Jeonju contains the
Cashbee logo, a city illustration/name and the ordinary `2 Days` pass category.
Neither active face contains coupon redemption, shop benefits or discount
content. No separate stored shop-coupon reference images were found; the two
promotional source masters and their published alternatives were the embedded
coupon/store-promotion images in the current tree.

## Previews and board

Four previews are regenerated exclusively from current, validated manifest
entries: `text-free-all.png`, `text-free-comparison.png`, `korean-designs.png`
and `expansion-designs.png`. They show 59 cleaned choices, 54 text pairs,
11 Korean choices and eight retained expansion choices respectively. The
decorative-exception and Octopus previews remain unchanged.

The existing Creative Production board was reused without reopening it. Nine
character/artist/unused-Disney items were deleted at revision 198, and two
original shop-promotion items at revision 201. The two retained generic items
were refreshed with final optimized PNGs and color-only titles at revisions
203 and 204. The board retains 66 items. Exact IDs and mutation receipts are
in `report.json`.

## Selection compatibility

Both `catalog.json` and the emitted schema-2 `manifest.json` contain an optional
top-level `retiredDesigns` map with 15 entries. For example:

```json
{
  "retiredDesigns": {
    "remote.kr.tmoney.ryan.png": "remote.kr.tmoney.default.png",
    "remote.kr.ezl.duty-free-text.png": "remote.kr.ezl.default.png"
  }
}
```

The canonical token grammar is
`remote.<lowercase region>.<card ID>.<design ID>.png`. Card and design IDs use
lowercase ASCII letters, digits and hyphens after the first character, matching
the existing catalog ID grammar. Every target must be an existing published
`default` on the same card. Retired origins must be absent from the published
designs. Paths, URLs, percent escapes, query strings, extra suffixes, whitespace,
cross-card replacements, missing targets, chains and resurrected entries are
rejected during manifest generation, validation and local publication.

Schema version 2 is unchanged. The map is optional for older collections.
Updated app consumers can resolve old tokens to the safe default before
downloading. Consumers that ignore the optional field retain their missing-art
fallback behavior. App implementations are handled separately by the coordinator.
Pages publication also emits redirects from withdrawn file paths to the
corresponding standard default, covering requests with old version query strings.
The app fallback hostnames are the native Pages hostname and raw GitHub;
jsDelivr is no longer used because stale branch content survived a purge.

## Audit boundaries and verification

The name and image audit found no additional dominant licensed character or
contemporary artist variants in the remaining active designs. Standard issuer
mascots remain under the requested transit-design exception. Retained co-brand
labels include Tour de France/LCL on the Nice event card and POP card-family
branding. The event co-branding is flagged for coordinator review; this curation
does not claim clearance of every retained brand or artwork.

To regenerate the four current previews on this macOS workspace:

```
python3 tools/previews.py
```

The script uses Pillow and the system Helvetica font. It reads only validated
published PNGs, and never imports historical source/reference images.
`tools/build.py` can regenerate the manifest without rebuilding retained faces
through `build.write_manifest(catalog)`. Tests cover legacy schema-2 metadata,
map propagation, unsafe tokens, valid targets, resurrection, generic rectangle
invariants, and refusal to replace an existing local publication when retirement
metadata is invalid. `report.json` lists exact changed paths, deleted hashes,
replacement SVG/export hashes, preservation checks, budgets and test results.

No native image generation, app edits, commit, push or remote deployment is part
of this curation.
