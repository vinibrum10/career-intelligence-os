// Linear comparison preserves every character, including whitespace.
export function compareText(before, after) {
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let endBefore = before.length, endAfter = after.length;
  while (endBefore > start && endAfter > start && before[endBefore - 1] === after[endAfter - 1]) {
    endBefore--; endAfter--;
  }
  // Do not split a UTF-16 surrogate pair at the highlight boundary.
  if (start > 0 && /[\uDC00-\uDFFF]/.test(before[start] || after[start] || '')) start--;
  if (endBefore < before.length && /[\uDC00-\uDFFF]/.test(before[endBefore])) { endBefore++; endAfter++; }
  return {changed: before !== after, prefix: before.slice(0, start),
    removed: before.slice(start, endBefore), added: after.slice(start, endAfter), suffix: before.slice(endBefore)};
}
