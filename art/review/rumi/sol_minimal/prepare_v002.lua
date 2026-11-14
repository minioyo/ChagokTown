-- Rumi only: trace the generated silhouette, flatten colors, separate the eyes.
local root = "D:/Project/Etc/ChagokTown/"
local source = root .. "art/source/rumi/sol_minimal_v002.aseprite"
local output = root .. "art/export/rumi/sol_minimal_v002.png"
local review = root .. "art/review/rumi/sol_minimal/"
assert(not app.fs.isFile(source) and not app.fs.isFile(output), "Version already exists")
local pc = app.pixelColor
local white = {255, 255, 255}
local charcoal = {41, 39, 51}
local size = 1254

-- y, left boundary, right boundary, measured from the new yellow original.
-- The white edit kept this silhouette; tracing removes generated alpha specks.
local outline = {
  {210.6,625.5,625.5}, {211,612,640}, {212,598,653},
  {215,574,675}, {220,550,699}, {230,517,731}, {250,473,773},
  {280,428,816}, {300,405,838}, {350,359,882}, {400,325,915},
  {450,298,941}, {500,275,961}, {550,258,977}, {600,244,989},
  {650,234,996}, {700,228,999}, {731,227,999}, {750,227,998},
  {800,230,992}, {850,240,980}, {900,258,960}, {950,286,932},
  {1000,327,892}, {1030,359,859}, {1070,420,797}, {1090,466,753},
  {1100,497,721}, {1110,545,673}, {1114,586,636}, {1115.5,611,611}
}
local function boundary(y, column)
  if y <= outline[1][1] or y >= outline[#outline][1] then return 611 end
  local i = 1
  while outline[i+1][1] < y do i = i + 1 end
  local a, b = outline[i], outline[i+1]
  local prev, nextPoint = outline[math.max(1,i-1)], outline[math.min(#outline,i+2)]
  local h = b[1] - a[1]
  local t = (y-a[1])/h
  local m0 = (b[column]-prev[column])/(b[1]-prev[1])
  local m1 = (nextPoint[column]-a[column])/(nextPoint[1]-a[1])
  return (2*t^3-3*t^2+1)*a[column] + (t^3-2*t^2+t)*h*m0
       + (-2*t^3+3*t^2)*b[column] + (t^3-t^2)*h*m1
end
local body = Image(size,size,ColorMode.RGB)
body:clear()
for y=210,1115 do
  local spans = {}
  local left, right = size, 0
  for sample=0,7 do
    local sy = y+(sample+0.5)/8
    if sy > outline[1][1] and sy < outline[#outline][1] then
      local l,r = boundary(sy,2),boundary(sy,3)
      spans[#spans+1] = {l,r}
      left,right = math.min(left,l),math.max(right,r)
    end
  end
  for x=math.floor(left),math.ceil(right)-1 do
    local coverage = 0
    for _,span in ipairs(spans) do
      coverage = coverage + math.max(0,math.min(x+1,span[2])-math.max(x,span[1]))
    end
    local alpha = math.floor(coverage/8*255+0.5)
    if alpha > 0 then body:drawPixel(x,y,pc.rgba(white[1],white[2],white[3],alpha)) end
  end
end

-- Two simple capsules retain the original eye bounds and unequal lengths.
local function eyeImage(x0,y0,width,height)
  local image = Image(size,size,ColorMode.RGB)
  image:clear()
  local radius = width/2
  local cx = x0+radius
  for y=y0,y0+height-1 do
    for x=x0,x0+width-1 do
      local coverage = 0
      for sample=0,7 do
        local sy = y+(sample+0.5)/8
        local cy = math.max(y0+radius,math.min(y0+height-radius,sy))
        local dx = math.sqrt(math.max(0,radius^2-(sy-cy)^2))
        coverage = coverage + math.max(0,math.min(x+1,cx+dx)-math.max(x,cx-dx))
      end
      local alpha = math.floor(coverage/8*255+0.5)
      if alpha > 0 then image:drawPixel(x,y,pc.rgba(charcoal[1],charcoal[2],charcoal[3],alpha)) end
    end
  end
  return image
end
local sprite = Sprite(size,size,ColorMode.RGB)
sprite:assignColorSpace(ColorSpace {sRGB=true})
sprite.layers[1].name = "Body - white FFFFFF"
sprite:newCel(sprite.layers[1],1,body,Point(0,0))
for _,eye in ipairs({{name="Eye left - 292733",x=453,y=496,w=79,h=162},
                     {name="Eye right - 292733",x=710,y=470,w=78,h=189}}) do
  local layer = sprite:newLayer()
  layer.name = eye.name
  sprite:newCel(layer,1,eyeImage(eye.x,eye.y,eye.w,eye.h),Point(0,0))
end
sprite:saveAs(source)
sprite:close()

sprite = app.open(source)
assert(sprite.colorMode == ColorMode.RGB and #sprite.layers == 3)
assert(sprite.colorSpace == ColorSpace {sRGB=true})
sprite:saveCopyAs(output)
local merged = Image(size,size,ColorMode.RGB)
merged:clear()
for _,layer in ipairs(sprite.layers) do
  local cel = layer:cel(1)
  merged:drawImage(cel.image,cel.position)
  cel.image:saveAs(review .. ({"sol_minimal_v002_body.png","sol_minimal_v002_eye_left.png","sol_minimal_v002_eye_right.png"})[layer.stackIndex])
end
assert(merged:isEqual(Image {fromFile=output}), "Layer composite differs from export")
local board = Image(640,320,ColorMode.RGB)
board:clear(pc.rgba(239,239,243,255))
for y=0,319 do for x=320,639 do board:drawPixel(x,y,pc.rgba(36,36,43,255)) end end
local small = merged:clone()
small:resize {width=256,height=256,method="bilinear"}
board:drawImage(small,Point(32,32))
board:drawImage(small,Point(352,32))
board:saveAs(review .. "sol_minimal_v002_light_dark.png")
local tiny = merged:clone()
tiny:resize {width=64,height=64,method="bilinear"}
tiny:saveAs(review .. "sol_minimal_v002_64.png")
sprite:close()
print("Saved and reopened RGB/sRGB source with three real layers; exported RGBA PNG and review images.")
