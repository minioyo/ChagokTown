local root = "D:/Project/Etc/ChagokTown/"
local sprite = app.open(root .. "art/source/moka/moka_concept_v002.aseprite")
assert(sprite and sprite.colorMode == ColorMode.RGB, "Source must remain RGB/RGBA")
assert(sprite.width == 1024 and sprite.height == 1536, "Source canvas changed")
assert(#sprite.frames == 1 and #sprite.layers == 1, "Unexpected source structure")
sprite:saveCopyAs(root .. "art/review/moka/moka_v002_roundtrip.png")
print("Reopened Aseprite source: RGB, 1024 x 1536, 1 frame, 1 artwork layer")
sprite:close()
