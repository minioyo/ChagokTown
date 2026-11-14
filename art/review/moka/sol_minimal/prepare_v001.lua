-- One-off Aseprite cleanup of the generated Moka concept, not a generic pipeline.
local root = "D:/Project/Etc/ChagokTown/"
local name = "sol_minimal_neutral_v001"
local review = root .. "art/review/moka/sol_minimal/"
local sourcePath = root .. "art/source/moka/" .. name .. ".aseprite"
local exportPath = root .. "art/export/moka/" .. name .. ".png"
for _, path in ipairs({sourcePath, exportPath}) do
  local file = io.open(path, "rb")
  if file then file:close(); error("Refusing to overwrite " .. path) end
end

local raw = app.open(root .. "art/raw/moka/" .. name .. ".png")
assert(raw and raw.colorMode == ColorMode.RGB)
local w, h = raw.width, raw.height
assert(w == 1254 and h == 1254, "Generated canvas changed")
raw:close()

local body = Image(w, h, ColorMode.RGB)
local eyes = Image(w, h, ColorMode.RGB)
body:clear()
eyes:clear()
local rgba = app.pixelColor.rgba
local function coverage(distance)
  return math.floor(math.max(0, math.min(1, 0.5 - distance)) * 255 + 0.5)
end

-- Fit the generated alpha>=128 silhouette to one clean rounded rectangle.
-- Same canvas and measured body bounds: [221,313,1021,983], radius 210 px.
for y = 312, 983 do
  for x = 220, 1021 do
    local qx = math.abs(x + 0.5 - 621) - 190
    local qy = math.abs(y + 0.5 - 648) - 125
    local dx, dy = math.max(qx, 0), math.max(qy, 0)
    local distance = math.sqrt(dx * dx + dy * dy) + math.min(math.max(qx, qy), 0) - 210
    local alpha = coverage(distance)
    if alpha > 0 then body:drawPixel(x, y, rgba(217, 117, 101, alpha)) end
  end
end

-- Fit the two generated capsule silhouettes; retain their position and tilt.
for _, eye in ipairs({{495, 548, 478.5, 627}, {758.5, 548, 775, 627}}) do
  local ax, ay, bx, by = table.unpack(eye)
  local vx, vy = bx - ax, by - ay
  local lengthSquared = vx * vx + vy * vy
  for y = 518, 656 do
    for x = math.floor(math.min(ax, bx) - 30), math.ceil(math.max(ax, bx) + 30) do
      local px, py = x + 0.5 - ax, y + 0.5 - ay
      local t = math.max(0, math.min(1, (px * vx + py * vy) / lengthSquared))
      local dx, dy = px - t * vx, py - t * vy
      local alpha = coverage(math.sqrt(dx * dx + dy * dy) - 28.5)
      if alpha > 0 then eyes:drawPixel(x, y, rgba(49, 38, 41, alpha)) end
    end
  end
end

local sprite = Sprite(w, h, ColorMode.RGB)
sprite:assignColorSpace(ColorSpace{sRGB=true})
local bodyLayer = sprite.layers[1]
bodyLayer.name = "Body"
if sprite.cels[1] then
  sprite.cels[1].image = body
else
  sprite:newCel(bodyLayer, 1, body, Point(0, 0))
end
local eyeLayer = sprite:newLayer()
eyeLayer.name = "Eyes"
sprite:newCel(eyeLayer, 1, eyes, Point(0, 0))
local palette = Palette(2)
palette:setColor(0, Color{r=217, g=117, b=101, a=255})
palette:setColor(1, Color{r=49, g=38, b=41, a=255})
sprite:setPalette(palette)
sprite:saveAs(sourcePath)
sprite:saveCopyAs(exportPath)

-- Export isolated layers as evidence that the source is actually separated.
eyeLayer.isVisible = false
sprite:saveCopyAs(review .. name .. "_body.png")
eyeLayer.isVisible = true
bodyLayer.isVisible = false
sprite:saveCopyAs(review .. name .. "_eyes.png")
bodyLayer.isVisible = true
sprite:close()

-- Reopen the saved source and export again to verify the real file on disk.
sprite = app.open(sourcePath)
assert(sprite.colorMode == ColorMode.RGB and sprite.width == w and sprite.height == h)
assert(#sprite.frames == 1 and #sprite.layers == 2)
assert(sprite.layers[1].name == "Body" and sprite.layers[2].name == "Eyes")
assert(sprite.layers[1].isVisible and sprite.layers[2].isVisible)
sprite:saveCopyAs(review .. name .. "_roundtrip.png")
local metadata = assert(io.open(review .. "structure_v001.json", "w"))
metadata:write('{"width":1254,"height":1254,"mode":"RGB/RGBA","color_space":"sRGB","frames":1,"layers":["Body","Eyes"],"palette":["#D97565","#312629"],"source_reopened":true}\n')
metadata:close()

-- Review only: 256, 128, 64 px canvases on light and dark backgrounds.
local flat = Image(w, h, ColorMode.RGB)
flat:clear()
flat:drawSprite(sprite, 1, Point(0, 0))
local sheet = Sprite(1024, 320, ColorMode.RGB)
sheet:assignColorSpace(ColorSpace{sRGB=true})
local sheetImage = Image(1024, 320, ColorMode.RGB)
sheetImage:clear(Color{r=244, g=240, b=232, a=255})
local dark = Image(512, 320, ColorMode.RGB)
dark:clear(Color{r=36, g=40, b=48, a=255})
sheetImage:drawImage(dark, Point(512, 0))
for _, item in ipairs({{256, 16}, {128, 288}, {64, 432}}) do
  local size, x = table.unpack(item)
  local small = Sprite(w, h, ColorMode.RGB)
  if small.cels[1] then small.cels[1].image = flat else small:newCel(small.layers[1], 1, flat, Point(0, 0)) end
  app.activeSprite = small
  app.command.SpriteSize{ui=false, width=size, height=size, method="bilinear"}
  local cel = small.cels[1]
  local y = 32 + (256 - size) / 2
  sheetImage:drawImage(cel.image, Point(x + cel.position.x, y + cel.position.y))
  sheetImage:drawImage(cel.image, Point(512 + x + cel.position.x, y + cel.position.y))
  small:close()
end
if sheet.cels[1] then sheet.cels[1].image = sheetImage else sheet:newCel(sheet.layers[1], 1, sheetImage, Point(0, 0)) end
sheet:saveCopyAs(review .. "review_v001.png")
sheet:close()
sprite:close()
print("Moka sol_minimal v001: RGB/RGBA sRGB, 1254x1254, Body + Eyes layers; source reopened and PNGs exported.")
