// textpolyblock — internal implementation.
//
// Public entrypoint: `lib.typ` (re-exports only `polyblock`).
//
// How it works, roughly:
//  1. The polygon's corner points (given as fractions of `width`/`height`)
//     are converted to absolute lengths.
//  2. The text is tokenized into words, respecting explicit line/paragraph
//     breaks ("\n").
//  3. For a candidate font size, the polygon is scanned line by line
//     (scanline / even-odd rule, like classic point-in-polygon tests) to
//     find the widest horizontal segment inside the polygon at each text
//     line's vertical position. Words are greedily packed into that segment.
//  4. If all words fit within the polygon's vertical extent, that font size
//     is used. Otherwise the font size is reduced (down to `min-font-size`)
//     and layout is retried, shrinking the text until it fits.
//
// Notes / limitations:
//  - Only the single widest horizontal segment per line is used, so very
//    concave shapes (e.g. stars) that would need multiple separate text
//    fragments on the same line are not fully supported.
//  - Rich inline formatting (bold/italic/etc.) passed as `content` is
//    flattened to plain text, since re-flowed, size-shrunk text can't
//    reliably preserve per-run styling.
//  - `inset` shrinks the available horizontal segment and the vertical
//    range uniformly; it is an approximation of a true polygon offset,
//    but works well in practice for typical convex/star-ish shapes.

// Reference function value used to recognize space elements by comparing
// `.func()` output (there is no public global binding for `space`).
#let space-func = [ ].func()

// Flattens (simple) content into a plain string. Formatting is lost, but
// this lets users pass ordinary markup content, not just raw strings.
#let to-plain-text(it) = {
  if type(it) == str {
    it
  } else if type(it) == content {
    let f = it.func()
    if f == text {
      it.text
    } else if f == space-func {
      " "
    } else if f == linebreak {
      "\n"
    } else if f == parbreak {
      "\n\n"
    } else if it.has("children") {
      it.children.map(to-plain-text).join("")
    } else if it.has("body") {
      to-plain-text(it.body)
    } else if it.has("text") {
      let t = it.text
      if type(t) == str { t } else { to-plain-text(t) }
    } else {
      ""
    }
  } else {
    str(it)
  }
}

// Splits plain text into a stream of `word` and `break` tokens. A single
// "\n" acts as a forced line break, while a blank line ("\n\n") produces an
// empty output line, mirroring how paragraph breaks are usually expected
// to behave.
#let tokenize(s) = {
  let tokens = ()
  let paragraphs = s.split("\n")
  for (i, para) in paragraphs.enumerate() {
    if i > 0 {
      tokens.push((kind: "break"))
    }
    for w in para.split(regex("\s+")) {
      if w.len() > 0 {
        tokens.push((kind: "word", text: w))
      }
    }
  }
  tokens
}

// Computes the x-intervals where the horizontal line `y` is inside the
// polygon `pts`, using the standard scanline / even-odd edge-crossing rule.
#let scan-intervals(pts, y) = {
  let n = pts.len()
  let xs = ()
  for i in range(n) {
    let p1 = pts.at(i)
    let p2 = pts.at(calc.rem(i + 1, n))
    let y1 = p1.at(1)
    let y2 = p2.at(1)
    if (y1 <= y and y < y2) or (y2 <= y and y < y1) {
      let x1 = p1.at(0)
      let x2 = p2.at(0)
      let t = (y - y1) / (y2 - y1)
      xs.push(x1 + t * (x2 - x1))
    }
  }
  xs = xs.sorted()
  let intervals = ()
  let i = 0
  while i + 1 < xs.len() {
    intervals.push((xs.at(i), xs.at(i + 1)))
    i += 2
  }
  intervals
}

// Picks the widest of a set of (a, b) intervals, or `none` if there are none.
#let widest-interval(intervals) = {
  intervals.fold(none, (acc, iv) => {
    if acc == none {
      iv
    } else if (iv.at(1) - iv.at(0)) > (acc.at(1) - acc.at(0)) {
      iv
    } else {
      acc
    }
  })
}

// Attempts to lay out `tokens` inside polygon `pts` (with bounding box
// `bbox`) at font size `fs`. If `enforce-bound` is true, layout stops (and
// reports failure) as soon as it would spill past the bottom of the
// polygon; otherwise it keeps going regardless (used as a last-resort
// fallback so no text silently disappears). `y-offset` shifts the starting
// vertical position, used for vertical centering.
#let attempt-layout(tokens, pts, bbox, inset, fs, leading, enforce-bound, y-offset) = {
  let space-w = measure(text(size: fs, " ")).width
  let probe-h = measure(text(size: fs, "Hg")).height
  let lead = if leading == auto { 0.65 * fs } else { leading }
  let step = probe-h + lead
  // Half of the leading, kept clear above and below the glyph box within
  // each line's row (see below).
  let margin = lead / 2

  let widths = (:)
  for tok in tokens {
    if tok.kind == "word" and tok.text not in widths {
      widths.insert(tok.text, measure(text(size: fs, tok.text)).width)
    }
  }

  let y-min = bbox.y-min + inset + y-offset
  let y-max = bbox.y-max - inset

  let lines = ()
  let idx = 0
  let cur-y = y-min
  let ok = true
  let guard = 0

  while idx < tokens.len() {
    guard += 1
    if guard > 500 {
      ok = false
      break
    }
    if enforce-bound and (cur-y + step) > y-max {
      ok = false
      break
    }

    // Sample both the top and bottom of this line's actual glyph box
    // (i.e. excluding the leading/gap towards neighboring lines) and use
    // their intersection, not just the vertical middle. This avoids text
    // spilling past steeply slanted polygon edges (e.g. narrow triangles),
    // without being overly pessimistic about the leading itself, which no
    // glyph ink ever reaches anyway.
    let top-best = widest-interval(scan-intervals(pts, cur-y + margin))
    let bot-best = widest-interval(scan-intervals(pts, cur-y + margin + probe-h))

    if top-best == none or bot-best == none {
      cur-y += step
      continue
    }

    let a = calc.max(top-best.at(0), bot-best.at(0)) + inset
    let b = calc.min(top-best.at(1), bot-best.at(1)) - inset

    if b <= a {
      cur-y += step
      continue
    }

    let avail = b - a
    let line-words = ()
    let w = 0pt

    while idx < tokens.len() {
      let tok = tokens.at(idx)
      if tok.kind == "break" {
        idx += 1
        break
      }
      let ww = widths.at(tok.text)
      let extra = if line-words.len() == 0 { ww } else { w + space-w + ww }
      if line-words.len() > 0 and extra > avail {
        break
      }
      line-words.push(tok.text)
      w = extra
      idx += 1
    }

    lines.push((y: cur-y, x-start: a, x-end: b, width: w, text: line-words.join(" ")))

    // A single unsplittable word can be wider than the available segment
    // (this is the only way `w` can exceed `avail`, since additional words
    // are only ever added while they still fit). Treat that as "doesn't
    // fit" too, so the caller tries a smaller font size instead of letting
    // the word visibly spill past the polygon's outline.
    if enforce-bound and w > avail {
      ok = false
      break
    }

    cur-y += step
  }

  (ok: ok and idx >= tokens.len(), lines: lines, step: step)
}

// Searches for the largest font size (from `max-fs` down to `min-fs`, in
// `step-fs` decrements) for which all tokens fit inside the polygon. Falls
// back to `min-fs` (allowing vertical overflow) if nothing fits.
#let fit-text(tokens, pts, bbox, inset, max-fs, min-fs, step-fs, leading) = {
  let fs = max-fs
  let found = none

  while fs >= min-fs {
    let attempt = attempt-layout(tokens, pts, bbox, inset, fs, leading, true, 0pt)
    if attempt.ok {
      found = (fs: fs, attempt: attempt)
      break
    }
    fs -= step-fs
  }

  if found == none {
    let attempt = attempt-layout(tokens, pts, bbox, inset, min-fs, leading, false, 0pt)
    found = (fs: min-fs, attempt: attempt)
  }

  found
}

/// A block-like container whose outline is an arbitrary polygon instead of
/// a rectangle. The given `body` text is automatically wrapped to fit the
/// polygon's shape at each line, and the font size is automatically
/// shrunk (down to `min-font-size`) if the text would otherwise overflow.
///
/// - points (array): Corner points of the polygon, each as `(x, y)` with
///   both components given as plain numbers (fractions of `width`/
///   `height`; `(0, 0)` is the top-left corner, `(1, 1)` the bottom-right
///   corner). At least 3 points are required.
/// - width (length): Fixed width of the block.
/// - height (length): Fixed height of the block.
/// - fill (none, color, gradient, tiling): Fill for the polygon, forwarded
///   to the underlying `polygon`.
/// - stroke (stroke): Stroke for the polygon's outline.
/// - fill-rule (str): Fill rule forwarded to `polygon` ("non-zero" or
///   "even-odd").
/// - inset (length): Empty space kept between the polygon's outline and
///   the text.
/// - align (alignment): Horizontal alignment (`left`, `center`, `right`)
///   of each line within the polygon's available width at that height.
/// - valign (alignment): Vertical distribution (`top`, `horizon`,
///   `bottom`) of the whole text block within the polygon's height.
/// - font-size (length): Largest font size to try.
/// - min-font-size (length): Smallest font size to shrink down to.
/// - font-step (length): Decrement used while searching for a fitting
///   font size.
/// - leading (auto, length): Space between lines. `auto` uses `0.65em`
///   (Typst's default paragraph leading) for the chosen font size.
/// -> content
#let polyblock(
  points: ((0, 0), (1, 0), (1, 1), (0, 1)),
  width: 8cm,
  height: 5cm,
  fill: none,
  stroke: 1pt + black,
  fill-rule: "non-zero",
  inset: 8pt,
  justify: true,
  valign: horizon,
  font-size: 14pt,
  min-font-size: 6pt,
  font-step: 0.5pt,
  leading: auto,
  body,
) = {
  assert(points.len() >= 3, message: "polyblock: `points` needs at least 3 points.")
  assert(min-font-size <= font-size, message: "polyblock: `min-font-size` must not exceed `font-size`.")
  assert(font-step > 0pt, message: "polyblock: `font-step` must be greater than zero.")

  let pts = points.map(p => (p.at(0) * width, p.at(1) * height))
  let bbox = (
    x-min: calc.min(..pts.map(p => p.at(0))),
    x-max: calc.max(..pts.map(p => p.at(0))),
    y-min: calc.min(..pts.map(p => p.at(1))),
    y-max: calc.max(..pts.map(p => p.at(1))),
  )

  assert(
    bbox.y-max - bbox.y-min > 2 * inset,
    message: "polyblock: `inset` is too large for the polygon's height.",
  )
  assert(
    bbox.x-max - bbox.x-min > 2 * inset,
    message: "polyblock: `inset` is too large for the polygon's width.",
  )

  let plain = if type(body) == str { body } else { to-plain-text(body) }
  let tokens = tokenize(plain)

  context {
    let result = fit-text(tokens, pts, bbox, inset, font-size, min-font-size, font-step, leading)
    let fs = result.fs
    let attempt = result.attempt

    let avail-h = (bbox.y-max - inset) - (bbox.y-min + inset)
    let used-h = attempt.lines.len() * attempt.step
    let extra = calc.max(0pt, avail-h - used-h)
    let y-offset = if valign == top { 0pt } else if valign == bottom { extra } else { extra / 2 }

    // Re-validate with the bound enforced again: shifting down can change
    // which polygon segments are sampled, so re-check that everything
    // still fits before committing to the shifted (vertically centered or
    // bottom-aligned) version; otherwise keep the guaranteed-fitting,
    // top-aligned attempt.
    let final = if y-offset > 0pt {
      let shifted = attempt-layout(tokens, pts, bbox, inset, fs, leading, true, y-offset)
      if shifted.ok { shifted } else { attempt }
    } else {
      attempt
    }

    block(width: width, height: height, fill: none, stroke: none, inset: 0pt, breakable: false)[
      #polygon(fill: fill, stroke: stroke, fill-rule: fill-rule, ..pts)
      #for line in final.lines {
        if line.text != "" {
          let slot = line.x-end - line.x-start
          let x = if justify == true {
            line.x-start
          } else {
            line.x-start + (slot - line.width) / 2
          }
          place(top + left, dx: x, dy: line.y, 
            block(width: slot, [
            #text(size: fs, line.text)
            #if justify {
              linebreak(justify: true)
            }
            ])
            )
        }
      }
    ]
  }
}
