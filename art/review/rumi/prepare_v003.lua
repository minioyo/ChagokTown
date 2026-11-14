-- Rumi user-reference proposal. Preserve all source RGBA channels exactly.
local root = "D:/Project/Etc/ChagokTown/"
local source = root .. "art/source/rumi/rumi_concept_v003.aseprite"
local output = root .. "art/export/rumi/rumi_concept_v003.png"
local review = root .. "art/review/rumi/"
assert(not app.fs.isFile(source), "Refusing to overwrite " .. source)
assert(not app.fs.isFile(output), "Refusing to overwrite " .. output)
local sprite = app.open(root .. "art/raw/rumi/rumi_concept_v003.png")
assert(sprite.colorMode == ColorMode.RGB)
assert(sprite.width == 1024 and sprite.height == 1536)
sprite:assignColorSpace(ColorSpace { sRGB=true })
sprite.layers[1].name = "Rumi reference-style v003 - original RGBA"
sprite:saveAs(source)
sprite:close()

-- Export after reopening the actual Aseprite working file.
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
  composite:saveAs(review .. "rumi_" .. theme.name .. "_v003.png")
  for _, width in ipairs({512, 256, 128}) do
    local small = composite:clone()
    small:resize {width=width, height=width*3/2, method="bilinear"}
    small:saveAs(review .. "rumi_" .. theme.name .. "_" .. width .. "_v003.png")
  end
end
print("v003: 1024x1536 RGB/RGBA, sRGB assigned without color conversion, source reopened and PNG exported. Review composites created.")
sprite:close()
