# UI Fix TODO

## Issues Fixed
1. `.card { overflow: hidden }` clips content - removed
2. Missing `</div>` closing tag for `.brand` - fixed
3. No scroll handling for long content - added `max-height` + `overflow-y` per card
4. Preview card content may overflow - added scroll support

## Steps
- [x] Plan approval
- [x] Fix CSS: Remove `overflow:hidden` from `.card`, add scroll handling
- [x] Fix HTML: Close `.brand` div properly
- [x] Verify all sections visible

