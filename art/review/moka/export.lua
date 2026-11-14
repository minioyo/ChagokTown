-- Preserve the generated RGBA pixels and canvas. Previews are separate files.
local root = "D:/Project/Etc/ChagokTown/"
local input = root .. "art/raw/moka/moka_concept_v002.png"
local source = root .. "art/source/moka/moka_concept_v002.aseprite"
local output = root .. "art/export/moka/moka_concept_v002.png"
local sprite = app.open(input)
assert(sprite and sprite.colorMode == ColorMode.RGB, "Expected RGBA input")
assert(sprite.width == 1024 and sprite.height == 1536, "Unexpected canvas")
sprite.layers[1].name = "Moka concept v002 - generated artwork"
sprite:saveAs(source)
sprite:saveCopyAs(output)
print("Aseprite source and PNG saved in RGB mode, 1024 x 1536")

local backgrounds = {
  {name="light", r=244, g=240, b=232},
  {name="dark", r=36, g=40, b=48},
}
for _, background in ipairs(backgrounds) do
  local preview = Sprite(sprite.width, sprite.height, ColorMode.RGB)
  local composite = Image(sprite.width, sprite.height, ColorMode.RGB)
  composite:clear(Color{r=background.r, g=background.g, b=background.b, a=255})
  for _, cel in ipairs(sprite.cels) do
    composite:drawImage(cel.image, cel.position)
  end
  if #preview.cels == 0 then
    preview:newCel(preview.layers[1], 1, composite, Point(0,0))
  else
    preview.cels[1].image = composite
  end
  preview:saveCopyAs(root .. "art/review/moka/moka_v002_" .. background.name .. "_1024.png")
  app.activeSprite = preview
  app.command.SpriteSize{ui=false, width=256, height=384, method="bilinear"}
  preview:saveCopyAs(root .. "art/review/moka/moka_v002_" .. background.name .. "_256.png")
  app.command.SpriteSize{ui=false, width=128, height=192, method="bilinear"}
  preview:saveCopyAs(root .. "art/review/moka/moka_v002_" .. background.name .. "_128.png")
  preview:close()
end
sprite:close()
