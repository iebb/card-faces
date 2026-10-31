# Text-free card artwork

The text-free collection derives from the real-card recreations already in this
repository. Native built-in ImageGen edits remove ordinary lettering, numerals
and wordmarks while preserving the original palette, background shapes,
illustrations and non-letter symbols. Each source is edited separately.

The generation and preservation records below describe the historical
text-removal migration. Later [curation](../curation/README.md) retires dominant
licensed character and contemporary artist variants. Their published faces,
source images and reference images are no longer in the current tree, and the
current previews are regenerated only from retained manifest entries.
The later coupon/promotion pass also retires two EZL text alternatives and
replaces their cleaned artwork with original generic SVG color blocks.

Defaults prefer the text-free version unless the lettering itself is decorative
artwork. PASMO is an explicit exception: its letters complete the train and bus
motif, so its original artwork is the default again. The previous cleaned face
is preserved as `jp/pasmo/no-text`; the original `jp/pasmo/text` token remains
available unchanged. The other narrow exceptions preserve Edy's background R,
the Climate Card GO ribbon, Changsha's background brushwork and the geometric
JS emblems on Suzhou and Nanjing cards. Each has a `no-text` alternative retaining
the previous cleaned PNG byte for byte. Ordinary brand labels, city names,
service descriptions and small print stay removed.

[`decorative-exceptions.json`](decorative-exceptions.json) records the policy,
the six decisions, preservation hashes and selective edit prompts. These
decisions supersede the blanket-removal prompts in the original worker reports.

For retained designs, the original source and published PNG were copied without modification to
`text.*` / `text.png` for defaults, or `<design>-text.*` /
`<design>-text.png` for named designs. Designs that already have no lettering
remain unchanged: OKICA, the abstract T-money default and U-Money.

`edits.json` records each card, its stable design ID, the text alternative,
original source and PNG hashes, research references and the exact edit prompt.
The original PNG hashes refer to collection commit `44d5728`.

The text-free exports use the same optimizer as the rest of the collection:
30:19 PNGs, at most 24 colors and strictly less than 40,000 bytes. Only the
edited designs are rebuilt during this migration, preserving the original
published PNGs exactly.

The current text-free build inputs are byte-identical copies of those validated
exports and use `denoise: false`. This keeps the Git package below the 50 MB
limit enforced by some jsDelivr edges. Full-resolution generated masters are
archived in commit `8b9168c2c65fd50b738c32459e8d9fb42284dd5b`, at the paths
listed under `generatedMasterArchive` in `edits.json`. The worker reports
describe the generation stage before this compaction. Original text masters
for retained designs remain unchanged in the current tree.
