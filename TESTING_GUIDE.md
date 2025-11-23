# Regional Conditioning - Systematic Testing Guide

**Date:** November 23, 2025
**Current Status:** All regions appearing, bird too small - needs calibration
**User Workflow:** 1344x768, Flux model, 3 regions (car, giraffe, bird)

---

## Current User-Tested Values (Baseline)

Based on your testing, these values produce all three regions:

```
Background: 1.0
Region 1 (car, left):      0.7
Region 2 (giraffe, center): 0.8
Region 3 (bird, upper-right): 1.5
```

**Results:**
- ✅ Car appears (good size)
- ✅ Giraffe appears (good size)
- ⚠️ Bird appears but TINY (needs improvement)

---

## 4 Systematic Test Scenarios

### Scenario 1: **Boost Bird Strength** (Fix tiny bird)
**Hypothesis:** Bird is too small because strength 1.5 isn't high enough for the smallest region

**Settings:**
```
Background: 1.0
Region 1 (car):     0.7
Region 2 (giraffe): 0.8
Region 3 (bird):    2.5  ← INCREASED from 1.5
```

**Expected Result:** Bird becomes larger and more prominent

**What to observe:**
- Is bird now visible and appropriately sized?
- Does it maintain correct position (upper-right)?
- Any artifacts or over-saturation?
- Do car and giraffe still look good?

---

### Scenario 2: **Lower Background for More Regional Dominance**
**Hypothesis:** Background at 1.0 might be competing with regions, keeping them subtle

**Settings:**
```
Background: 0.6  ← DECREASED from 1.0
Region 1 (car):     0.7
Region 2 (giraffe): 0.8
Region 3 (bird):    2.5
```

**Expected Result:** All regions become more prominent, bird especially

**What to observe:**
- Are all regions more vivid/clear?
- Does background scene context (city street at night) still visible?
- Does lowering background help bird without needing to boost its strength as high?

---

### Scenario 3: **Balanced Mid-Range Strengths**
**Hypothesis:** Keep all regions in similar strength range for balanced composition

**Settings:**
```
Background: 0.8
Region 1 (car):     1.0  ← INCREASED from 0.7
Region 2 (giraffe): 1.2  ← INCREASED from 0.8
Region 3 (bird):    1.8  ← INCREASED from 1.5
```

**Expected Result:** All regions at moderate, balanced strengths

**What to observe:**
- Do all regions appear with similar prominence?
- Is bird now appropriately sized?
- Better overall composition balance?
- Any regions overpowering others?

---

### Scenario 4: **Aggressive Bird Emphasis** (If bird still tiny)
**Hypothesis:** Smallest region might need much higher strength due to limited pixel area

**Settings:**
```
Background: 0.5  ← Very low to minimize interference
Region 1 (car):     0.7
Region 2 (giraffe): 0.8
Region 3 (bird):    4.0  ← VERY HIGH to compensate for small area
```

**Expected Result:** Bird becomes prominent despite small region size

**What to observe:**
- Is bird finally appropriately sized?
- Any artifacts at strength 4.0?
- Does very low background (0.5) make scene less cohesive?
- Are car and giraffe still good?

---

## Prompt Improvements for Size Control

### Current Prompts (from your workflow):
```
Background: "photo of empty city street at night, high quality"
Region 1:   "red sports car"
Region 2:   "closeup full body giraffe wearing sunglasses"
Region 3:   "blue bird flying"
```

### Issue Analysis

**Region 3 (bird) is too small because:**
1. ✅ Attention masking is working (bird appears in correct location)
2. ✅ Region box is reasonably sized (378x256 px = 97,728 pixels)
3. ❌ Prompt lacks size/scale keywords
4. ❌ "flying" might imply distant/small bird in sky

**Region 2 (giraffe) works well because:**
- Has "closeup full body" keywords that enforce scale
- Larger region area (384x704 = 270,336 pixels)
- Higher strength (0.8 vs bird's 1.5... wait, bird is higher but still tiny!)

### Recommended Prompt Tweaks

#### Option A: Add Size/Scale Keywords
```
Region 3: "large blue bird flying, closeup view, prominent"
```
**Why:** "large", "closeup", "prominent" tell model to make bird bigger

#### Option B: Change Action/Context
```
Region 3: "blue parrot perched prominently, closeup, full body"
```
**Why:** "perched" removes distant-flight implication, "parrot" is inherently larger than generic "bird"

#### Option C: Extreme Emphasis
```
Region 3: "giant blue bird flying close to camera, large wingspan, prominent in frame"
```
**Why:** Multiple size keywords stack to force larger generation

#### Option D: Specific Bird Species (Size Control)
```
Region 3: "blue macaw flying, closeup full body view, large wingspan"
```
**Why:** "macaw" implies large parrot species, "full body" + "closeup" enforce scale

---

## Recommended Testing Order

### Test 1: **Quick Fix (Prompt Only)**
1. Keep current strengths (bg=1.0, r1=0.7, r2=0.8, r3=1.5)
2. Change Region 3 prompt to: **"large blue bird flying close to camera, closeup view, prominent"**
3. Run generation

**If bird still tiny → Test 2**

### Test 2: **Strength Boost (Scenario 1)**
1. Keep new prompt from Test 1
2. Increase bird strength: **1.5 → 2.5**
3. Run generation

**If bird good but overall balance off → Test 3**

### Test 3: **Balanced Adjustment (Scenario 3)**
1. Keep new prompt
2. Try balanced strengths: bg=0.8, r1=1.0, r2=1.2, r3=1.8
3. Run generation

**If still issues → Test 4**

### Test 4: **Aggressive Fix (Scenario 4)**
1. Keep new prompt with maximum size keywords
2. Try aggressive settings: bg=0.5, r3=4.0
3. Run generation

---

## Additional Prompt Engineering Tips

### For ALL Regions (Not Placement-Related)

**Size/Scale Keywords:**
- `closeup` / `close-up view` / `close to camera`
- `full body` / `full figure`
- `large` / `giant` / `prominent`
- `detailed` / `highly detailed`

**Viewing Distance:**
- `closeup shot` = close, large
- `medium shot` = moderate distance
- `distant view` = far, small
- `extreme closeup` = very close, fills frame

**For Small Objects (like your bird):**
- Add species that's larger (macaw > sparrow)
- Add "prominent" or "dominant"
- Add "in foreground" vs "in background"
- Add "large wingspan" or size-specific details

**For Backgrounds:**
- Keep general scene description
- Avoid specific objects (let regions handle that)
- Include lighting/atmosphere: "at night", "foggy", "sunset"
- Include quality keywords: "high quality", "photorealistic"

---

## Current Hypothesis

Based on your image, the **bird is tiny** likely because:

1. **Prompt issue (most likely):**
   - "blue bird flying" lacks size keywords
   - "flying" implies distant/sky context
   - Need: "large blue bird" or "closeup blue macaw"

2. **Strength too low (less likely):**
   - Your 1.5 is higher than car (0.7) and giraffe (0.8)
   - But might need 2.0-2.5 for smallest region

3. **Region size (unlikely):**
   - 378x256 is reasonable size
   - Giraffe region isn't that much bigger

**Recommendation:** Start with Test 1 (prompt change only), then adjust strength if needed.

---

## What to Document After Each Test

Please record for each test:
- Strength values used
- Prompts used
- Execution time
- Results:
  - Car appearance (good/bad/missing)
  - Giraffe appearance (good/bad/missing)
  - Bird appearance (good/bad/missing, SIZE!)
  - Overall composition quality
  - Any artifacts or issues

This will help us find the optimal configuration!
