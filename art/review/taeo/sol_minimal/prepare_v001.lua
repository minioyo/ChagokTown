-- One-asset Aseprite cleanup. Uses the newly generated raster, no prior artwork.
local stem = 'sol_minimal_neutral_v001'
local review = 'art/review/taeo/sol_minimal/'
local source = 'art/source/taeo/' .. stem .. '.aseprite'
local output = 'art/export/taeo/' .. stem .. '.png'
assert(not app.fs.isFile(source) and not app.fs.isFile(output), 'Version already exists')
local raw = Image{ fromFile='art/raw/taeo/' .. stem .. '.png' }
assert(raw.colorMode == ColorMode.RGB)
local w, h = raw.width, raw.height
local pc = app.pixelColor
local function clamp(v) return math.max(0, math.min(255, math.floor(v + 0.5))) end
local bodyColor, eyeColor = {91,134,175}, {23,45,66}
local function rgba(c, a) return pc.rgba(c[1], c[2], c[3], a) end

-- Row spans of the main opaque silhouette reject the source's distant alpha dust.
local bodyRows, eyeRows = {}, {{}, {}}
for y=0,h-1 do
  local lo, hi
  for x=0,w-1 do
    local p = raw:getPixel(x,y)
    if pc.rgbaA(p) >= 128 then lo=lo or x; hi=x end
  end
  if lo then bodyRows[y]={lo,hi} end
  if y>=570 and y<=625 then
    for i,range in ipairs({{430,590},{670,820}}) do
      local el, eh
      for x=range[1],range[2] do
        local p = raw:getPixel(x,y)
        if pc.rgbaA(p)>240 and pc.rgbaR(p)<57 then el=el or x; eh=x end
      end
      if el then eyeRows[i][y]={el,eh} end
    end
  end
end
local function nearSpan(rows,x,y)
  for yy=y-1,y+1 do
    local span=rows[yy]
    if span and x>=span[1]-2 and x<=span[2]+2 then return true end
  end
  return false
end
local body, eyes = Image(w,h,ColorMode.RGB), Image(w,h,ColorMode.RGB)
local minX,minY,maxX,maxY=w,h,-1,-1
local bodyPixels, eyePixels=0,0
for y=0,h-1 do
  for x=0,w-1 do
    local p=raw:getPixel(x,y)
    local a=pc.rgbaA(p)
    if a>0 and nearSpan(bodyRows,x,y) then
      -- The generated interior is mostly alpha 254. Make solid regions opaque;
      -- keep partial edge coverage, normalized from the source's 254 baseline.
      local ba=a>=240 and 255 or clamp(a*255/254)
      body:drawPixel(x,y,rgba(bodyColor,ba))
      bodyPixels=bodyPixels+1
      minX=math.min(minX,x); minY=math.min(minY,y)
      maxX=math.max(maxX,x); maxY=math.max(maxY,y)
      if nearSpan(eyeRows[1],x,y) or nearSpan(eyeRows[2],x,y) then
        -- Unmix the generated eye/body edge, then use the two candidate colors.
        local coverage=((93-pc.rgbaR(p))*72+(127-pc.rgbaG(p))*85+(166-pc.rgbaB(p))*103)/23018
        if coverage<0.05 then coverage=0 elseif coverage>0.94 then coverage=1 end
        local ea=clamp(coverage*255)
        if ea>0 then eyes:drawPixel(x,y,rgba(eyeColor,ea)); eyePixels=eyePixels+1 end
      end
    end
  end
end
assert(bodyPixels>300000 and eyePixels>3000, 'Unexpected masks')
local dx=math.floor((w-(maxX-minX+1))/2)-minX
local dy=math.floor((h-(maxY-minY+1))/2)-minY
local sprite=Sprite(w,h,ColorMode.RGB)
sprite:assignColorSpace(ColorSpace{ sRGB=true })
local bodyLayer=sprite.layers[1]
bodyLayer.name='Body'
sprite:newCel(bodyLayer,1,body,Point(dx,dy))
local eyeLayer=sprite:newLayer()
eyeLayer.name='Eyes'
sprite:newCel(eyeLayer,1,eyes,Point(dx,dy))
sprite.data='Taeo sol_minimal v001 candidate. Built-in image_gen raster, flat-color cleanup in Aseprite. Body #5B86AF, Eyes #172D42. Actual Body/Eyes layers. Same canvas, integer translation only. No Indexed conversion.'
local before=Image(sprite)
sprite:saveAs(source)
sprite:close()
local reopened=app.open(source)
assert(reopened.colorMode==ColorMode.RGB and #reopened.frames==1 and #reopened.layers==2)
assert(reopened.layers[1].name=='Body' and reopened.layers[2].name=='Eyes')
assert(reopened.width==w and reopened.height==h)
assert(before:isEqual(Image(reopened)), 'Save/reopen changed RGBA pixels')
reopened:saveCopyAs(output)
local final=Image{ fromFile=output }
assert(final:isEqual(before), 'PNG export changed RGBA pixels')
-- Export actual separated layer pixels for independent checks.
for _,layer in ipairs(reopened.layers) do
  local cel=layer:cel(1)
  local layerImage=Image(w,h,ColorMode.RGB)
  layerImage:drawImage(cel.image,cel.position)
  layerImage:saveAs(review .. stem .. '_' .. string.lower(layer.name) .. '.png')
end
local light=Color{r=247,g=245,b=239,a=255}
local dark=Color{r=27,g=33,b=43,a=255}
local preview=Image(512,512,ColorMode.RGB)
preview:clear(light)
local half=final:clone()
half:resize{width=512,height=512,method='bilinear'}
preview:drawImage(half)
preview:saveAs(review .. stem .. '_preview.png')
local sheet=Image(1024,704,ColorMode.RGB)
sheet:clear(light)
sheet:clear(Rectangle(512,0,512,704),dark)
sheet:drawImage(half)
sheet:drawImage(half,Point(512,0))
for _,size in ipairs({64,128}) do
  local small=final:clone()
  small:resize{width=size,height=size,method='bilinear'}
  local x=size==64 and 128 or 256
  sheet:drawImage(small,Point(x,544))
  sheet:drawImage(small,Point(x+512,544))
end
sheet:saveAs(review .. stem .. '_background_check.png')
local log=assert(io.open(review .. 'aseprite_v001_checks.txt','w'))
log:write('Aseprite ' .. tostring(app.version) .. '\n')
log:write(string.format('RGB/RGBA, sRGB assigned to untagged source, %dx%d, 2 layers (Body, Eyes), 1 frame\n',w,h))
log:write(string.format('Integer translation: (%d,%d); no rescaling/cropping of delivery canvas\n',dx,dy))
log:write(string.format('Body pixels: %d; eye pixels: %d\n',bodyPixels,eyePixels))
log:write('Cleaned composite = reopened Aseprite = exported PNG RGBA: PASS\n')
log:write('No Indexed conversion. Distant alpha dust removed; opaque interiors normalized; edge partial alpha retained.\n')
log:close()
reopened:close()
print('PASS: Taeo sol_minimal v001, actual Body/Eyes layers, RGBA round trip identical')
