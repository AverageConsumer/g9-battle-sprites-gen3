-- Run from the mod root: luajit tests/back_framing_coverage_test.lua
-- Every back sprite the atlas packs has its body box (from the first frame of the kept
-- animation) and stands on its feet: its resting pose's bottom row (`bfr`, inside the frame)
-- and the player's feet line in its pic box (`bfl`, tools/build_atlas.py BACK_FEET_ROW less the
-- engine's offset for the slot). Female sheets and forms that reuse a base species' art share
-- its cells.
local index = dofile("data/atlas_index.lua").species

local passed, failed = 0, 0
local function check(cond, msg)
  if cond then passed = passed + 1 else failed = failed + 1; print("FAIL: " .. msg) end
end

local n = 0
for id, rec in pairs(index) do
  for _, variant in ipairs({ "back", "back_shiny" }) do
    local c = rec[variant]
    if c then
      n = n + 1
      check(c.cx0 and c.cx1 > c.cx0 and c.cy1 > c.cy0, id .. " " .. variant .. " has a body box")
      check(c.ux0 and c.ux0 <= c.cx0 and c.ux1 >= c.cx1 and c.uy0 <= c.cy0 and c.uy1 >= c.cy1,
        id .. " " .. variant .. ": the animation's box contains the body's")
      check(c.bfr and c.bfr > 0 and c.bfr <= c.fs, id .. " " .. variant .. " has its feet row in the frame")
      check(c.bfl and c.bfl >= 30 and c.bfl <= 80, id .. " " .. variant .. " has a feet line in the box, got "
        .. tostring(c.bfl))
      check(c.bt == nil and c.bs == nil, id .. " " .. variant .. " has no cart framing left")
      check(c.bn == nil or (c.bn >= 0.67 and c.bn <= 1.5), id .. " " .. variant .. " back/front match within limits")
    end
  end
end
check(n >= 2200, "a back and a shiny back for every species (" .. n .. ")")
-- realism scaling (gen3-hd-sprites): every species has its height, every front its feet row
for id, rec in pairs(index) do
  check(type(rec.ht) == "number" and rec.ht > 0, id .. " has a height")
  for _, variant in ipairs({ "front", "front_shiny" }) do
    local c = rec[variant]
    if c then check(c.ffr and c.ffr > 0 and c.ffr <= c.fs, id .. " " .. variant .. " has its feet row") end
  end
end
-- a shiny back stands where its normal sheet does
for id, rec in pairs(index) do
  if rec.back and rec.back_shiny then
    check(rec.back.bfl == rec.back_shiny.bfl, id .. ": shiny shares the feet line")
  end
end

print(string.format("%d/%d checks passed (g9-battle-sprites-gen3 back framing)", passed, passed + failed))
os.exit(failed == 0 and 0 or 1)
