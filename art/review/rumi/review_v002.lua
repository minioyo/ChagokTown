-- Derived review files only. Replaces the initial drawSprite-based previews.
local root = "D:/Project/Etc/ChagokTown/"
local review = root .. "art/review/rumi/"
local sprite = app.open(root .. "art/source/rumi/rumi_concept_v002.aseprite")
local pc = app.pixelColor
assert(sprite.colorMode == ColorMode.RGB)
local cel = sprite.cels[1]
for _, theme in ipairs({
  {name="light", color=pc.rgba(243, 240, 232, 255)},
  {name="dark", color=pc.rgba(32, 38, 48, 255)}
}) do
  local composite = Image(sprite.width, sprite.height, ColorMode.RGB)
  composite:clear(theme.color)
  composite:drawImage(cel.image, cel.position)
  assert(pc.rgbaA(composite:getPixel(0, 0)) == 255)
  assert(composite:getPixel(0, 0) == theme.color)
  composite:saveAs(review .. "rumi_" .. theme.name .. "_v002.png")
  composite:resize {width=256, height=384, method="bilinear"}
  composite:saveAs(review .. "rumi_" .. theme.name .. "_256_v002.png")
  composite:resize {width=128, height=192, method="bilinear"}
  composite:saveAs(review .. "rumi_" .. theme.name .. "_128_v002.png")
end
print("RGB source reopened. Created opaque review composites at 1024x1536, 256x384, 128x192.")
sprite:close()
