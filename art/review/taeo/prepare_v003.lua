-- New shared anime style candidate. Raw v003 and all earlier art remain untouched.
local stem = 'taeo_neutral_v003'
local source = 'art/source/taeo/' .. stem .. '.aseprite'
local output = 'art/export/taeo/' .. stem .. '.png'
assert(not app.fs.isFile(source) and not app.fs.isFile(output), 'Output already exists')

local original = Image{ fromFile='art/raw/taeo/' .. stem .. '.png' }
assert(original.colorMode == ColorMode.RGB and original.width == 1024 and original.height == 1536)
-- Uniform 7/8 scale inside the original canvas; no crop, palette mapping or alpha threshold.
local artwork = original:clone()
artwork:resize{ width=896, height=1344, method='bilinear' }
local sprite = Sprite(1024, 1536, ColorMode.RGB)
sprite:assignColorSpace(ColorSpace{ sRGB=true })
sprite.layers[1].name = 'Taeo v003 - framed raster'
sprite:newCel(sprite.layers[1], 1, artwork, Point(64, 96))
sprite.data = 'Shared user anime reference style. Generated raw v003 preserved separately. Uniform bilinear scale 0.875, placed at (64,96) in unchanged 1024x1536 canvas to add margins. sRGB assigned, not converted. No palette remap, indexed mode, alpha threshold, or semantic layer separation.'
local beforeSave = Image(sprite)
sprite:saveAs(source)
sprite:close()

local reopened = app.open(source)
assert(reopened.colorMode == ColorMode.RGB and #reopened.frames == 1 and #reopened.layers == 1)
assert(reopened.width == 1024 and reopened.height == 1536)
local afterSave = Image(reopened)
assert(beforeSave:isEqual(afterSave), 'ASEPRITE_SAVE_CHANGED_PIXELS')
reopened:saveCopyAs(output)
local exported = Image{ fromFile=output }
assert(afterSave:isEqual(exported), 'PNG_EXPORT_CHANGED_PIXELS')

local light = Color{ r=246, g=243, b=234, a=255 }
local dark = Color{ r=31, g=36, b=48, a=255 }
local half = afterSave:clone()
half:resize{ width=512, height=768, method='bilinear' }
local preview = Image(512, 768, ColorMode.RGB)
preview:clear(light)
preview:drawImage(half)
preview:saveAs('art/review/taeo/' .. stem .. '_preview.png')

local sheet = Image(1024, 960, ColorMode.RGB)
sheet:clear(light)
sheet:clear(Rectangle(512, 0, 512, 960), dark)
sheet:drawImage(half)
sheet:drawImage(half, Point(512, 0))
local small = afterSave:clone()
small:resize{ width=128, height=192, method='bilinear' }
local tiny = afterSave:clone()
tiny:resize{ width=85, height=128, method='bilinear' }
sheet:drawImage(small, Point(128, 768))
sheet:drawImage(tiny, Point(300, 800))
sheet:drawImage(small, Point(640, 768))
sheet:drawImage(tiny, Point(812, 800))
sheet:saveAs('art/review/taeo/' .. stem .. '_background_check.png')

local face = Image(afterSave, Rectangle(320, 110, 384, 384))
local facePreview = Image(384, 384, ColorMode.RGB)
facePreview:clear(light)
facePreview:drawImage(face)
facePreview:saveAs('art/review/taeo/' .. stem .. '_face.png')
local log = assert(io.open('art/review/taeo/aseprite_v003_checks.txt', 'w'))
log:write('Aseprite ' .. tostring(app.version) .. '\nRGB, 1024x1536, 1 layer, 1 frame\n')
log:write('sRGB assigned to untagged source, no color conversion\n')
log:write('Uniform bilinear scale: 0.875; offset: (64,96)\n')
log:write('RGBA after framing = reopened Aseprite = exported PNG: PASS\n')
log:close()
reopened:close()
print('PASS v003: framed RGBA pixels unchanged through ASEPRITE save/reopen and PNG export')
