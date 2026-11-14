-- Latest user direction: black hair, pink-violet irises, very pale skin.
-- Preserve all generated RGBA pixels; no palette remapping or indexing.
local root = "D:/Project/Etc/ChagokTown/"
local source = root .. "art/source/rumi/rumi_concept_v004.aseprite"
local output = root .. "art/export/rumi/rumi_concept_v004.png"
local review = root .. "art/review/rumi/"
assert(not app.fs.isFile(source), "Refusing to overwrite " .. source)
assert(not app.fs.isFile(output), "Refusing to overwrite " .. output)
local sprite = app.open(root .. "art/raw/rumi/rumi_concept_v004.png")
assert(sprite.colorMode == ColorMode.RGB)
assert(sprite.width == 1024 and sprite.height == 1536)
sprite:assignColorSpace(ColorSpace { sRGB=true })
sprite.layers[1].name = "Rumi black hair pink-violet eyes v004 - original RGBA"
sprite:saveAs(source)
sprite:close()

sprite = app.open(source)
assert(sprite.colorMode == ColorMode.RGB)
assert(sprite.colorSpace == ColorSpace { sRGB=true })
sprite:saveCopyAs(output)
local pc = app.pixelColor
local cel = sprite.cels[1]
for _, theme in ipairs({
  {name="light", color=pc.rgba(243, 240, 232, 255)},
  {name="dark", color=pc.rgba(32, 38, 48, 255)}
}) do
  local composite = Image(sprite.width, sprite.height, ColorMode.RGB)
  composite:clear(theme.color)
  composite:drawImage(cel.image, cel.position)
  assert(composite:getPixel(0, 0) == theme.color)
  composite:saveAs(review .. "rumi_" .. theme.name .. "_v004.png")
  for _, width in ipairs({512, 256, 128}) do
    local small = composite:clone()
    small:resize {width=width, height=width*3/2, method="bilinear"}
    small:saveAs(review .. "rumi_" .. theme.name .. "_" .. width .. "_v004.png")
  end
end
print("v004: 1024x1536 RGB/RGBA, source reopened, transparent PNG exported; light/dark review composites created.")
sprite:close()
