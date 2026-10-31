# Text-free card artwork

The text-free collection derives from the real-card recreations already in this
repository. Native built-in ImageGen edits remove lettering, numerals and
wordmarks while preserving the original palette, background shapes,
illustrations and non-letter symbols. Each source is edited separately.

The original source and published PNG are copied without modification to
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
remain unchanged in the current tree.
