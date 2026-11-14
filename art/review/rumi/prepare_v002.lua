-- Preserve the generated RGBA pixels and canvas; use Aseprite for authoring/export.
local root = "D:/Project/Etc/ChagokTown/"
local raw = root .. "art/raw/rumi/rumi_concept_v002.png"
local source = root .. "art/source/rumi/rumi_concept_v002.aseprite"
local output = root .. "art/export/rumi/rumi_concept_v002.png"
local review = root .. "art/review/rumi/"
for _, path in ipairs({source, output, review .. "rumi_light_v002.png", review .. "rumi_dark_v002.png"}) do
  assert(not app.fs.isFile(path), "Refusing to overwrite " .. path)
end

local sprite = app.open(raw)
assert(sprite.colorMode == ColorMode.RGB)
assert(sprite.width == 1024 and sprite.height == 1536)
sprite:assignColorSpace(ColorSpace { sRGB=true })
sprite.layers[1].name = "Rumi concept v002 - original RGBA"
sprite:saveAs(source)
sprite:saveCopyAs(output)

-- Opaque review composites show actual alpha blending, including any edge halos.
local pc = app.pixelColor
for _, theme in ipairs({
  {name="light", color=pc.rgba(243, 240, 232, 255)},
  {name="dark", color=pc.rgba(32, 38, 48, 255)}
}) do
  local composite = Image(sprite.width, sprite.height, ColorMode.RGB)
  composite:clear(theme.color)
  -- drawSprite replaces the whole canvas; drawImage alpha-composites the cel.
  composite:drawImage(sprite.cels[1].image, sprite.cels[1].position)
  composite:saveAs(review .. "rumi_" .. theme.name .. "_v002.png")
end
print("Saved original RGBA, sRGB assigned without pixel conversion; full-size light/dark review composites created.")
sprite:close()
