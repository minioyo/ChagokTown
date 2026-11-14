-- Run from the project root through tools/art/aseprite.ps1.
-- RGB import/export only; review compositions are separate from deliverables.
local raw = 'art/raw/taeo/taeo_neutral_v002.png'
local source = 'art/source/taeo/taeo_neutral_v002.aseprite'
local output = 'art/export/taeo/taeo_neutral_v002.png'
for _, path in ipairs({source, output}) do
  assert(not app.fs.isFile(path), 'Refusing to overwrite: ' .. path)
end

local sprite = app.open(raw)
assert(sprite and sprite.colorMode == ColorMode.RGB)
assert(sprite.width == 1024 and sprite.height == 1536)
sprite:assignColorSpace(ColorSpace{ sRGB=true })
sprite.layers[1].name = 'Taeo - original raster v002'
sprite.data = 'First concept candidate; single raster layer. Generated PNG preserved in art/raw/taeo. sRGB assigned to untagged input; no RGB conversion, palette mapping, indexed conversion or trimming.'
sprite:saveAs(source)
sprite:close()

local reopened = app.open(source)
assert(reopened.colorMode == ColorMode.RGB)
assert(reopened.width == 1024 and reopened.height == 1536)
assert(#reopened.layers == 1 and #reopened.frames == 1)
reopened:saveCopyAs(output)
print('SOURCE_REOPEN_OK RGB 1024x1536, 1 layer, 1 frame, sRGB assigned')

local light = Color{ r=246, g=243, b=234, a=255 }
local dark = Color{ r=31, g=36, b=48, a=255 }
local character = Image(reopened)
local half = character:clone()
half:resize{ width=512, height=768, method='bilinear' }
local sheet = Image(1024, 960, ColorMode.RGB)
sheet:clear(light)
sheet:clear(Rectangle(512, 0, 512, 960), dark)
sheet:drawImage(half, Point(0, 0))
sheet:drawImage(half, Point(512, 0))

local small = character:clone()
small:resize{ width=128, height=192, method='bilinear' }
local tiny = character:clone()
tiny:resize{ width=85, height=128, method='bilinear' }
sheet:drawImage(small, Point(128, 768))
sheet:drawImage(tiny, Point(300, 800))
sheet:drawImage(small, Point(640, 768))
sheet:drawImage(tiny, Point(812, 800))
sheet:saveAs('art/review/taeo/taeo_neutral_v002_background_check.png')

local preview = Image(512, 768, ColorMode.RGB)
preview:clear(light)
preview:drawImage(half)
preview:saveAs('art/review/taeo/taeo_neutral_v002_preview.png')
reopened:close()
print('REVIEW_SAVED light/dark at canvas heights 768, 192, 128')
