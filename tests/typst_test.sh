#!/usr/bin/env bash
#
# Standalone test for the KPE flyer template (flyer.typ).
# Verifies that `typst compile flyer.typ` produces valid output, independent of
# the FastHTML app and the Python test-suite. Mirrors how main.py compiles:
#   * fonts are loaded via --font-path <flyer>/fonts
#   * TYPST__SANDBOX is disabled (container-safe)
#   * --pages stands BEFORE the input path
#
# Usage:
#   bash tests/typst_test.sh            # run once
#   bash tests/typst_test.sh --check    # exit non-zero on failure (default)
#   bash tests/typst_test.sh --list     # list checks and exit
#
# Must be run from the project root (the directory containing flyer/).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

FLYER_DIR="flyer"
FLYER_TPL="${FLYER_DIR}/flyer.typ"
FONTS_DIR="${FLYER_DIR}/fonts"
OUT_DIR="tests/.typst-out"

# Valid metadata that defines every #let the template references. Without these,
# Typst errors out (which is exactly what we want to catch).
read -r -d '' VALID_METADATA <<'EOF' || true
#let WOELFLINGE_PHOTO = ""
#let PFADI_PHOTO = ""
#let RAADER_PHOTO = ""
#let WOELFLINGE_X = 0mm
#let WOELFLINGE_Y = 0mm
#let WOELFLINGE_ZOOM = 1.0
#let PFADI_X = 0mm
#let PFADI_Y = 0mm
#let PFADI_ZOOM = 1.0
#let RAIDER_X = 0mm
#let RAIDER_Y = 0mm
#let RAIDER_ZOOM = 1.0
#let STAMM = "München"
#let PLZ = "81739 München"
#let ADDRESS = "Maximilian-Kolbe-Allee 18"
#let GROUPTIME = "Freitag, 16.00-18.00 Uhr"
#let SFM = "Vroni Spörl"
#let MAIL = "stammstjakobus@gmail.com"
#let PHONE = "01577774472"
#let INSTAGRAM = "@muenchen"
#let WICHTEL = true
#let twoWEEKS = true
#let STAMMESMEISTERIN = true
EOF

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "ok: $*"; }

command -v typst >/dev/null 2>&1 || fail "`typst` binary not found in PATH"
[[ -f "${FLYER_TPL}" ]]    || fail "${FLYER_TPL} not found (run from project root)"
[[ -d "${FONTS_DIR}" ]]    || fail "${FONTS_DIR} directory not found"

# Compile flyer.typ into a fresh temp copy so we never touch the real source.
prepare_flyer() {
  local dest="$1"
  rm -rf "${dest}"
  cp -r "${FLYER_DIR}" "${dest}"
  printf '%s\n' "${VALID_METADATA}" > "${dest}/metadata.typ"
}

# Compile flyer.typ and return the number of produced output files matching
# `pattern` (a find-compatible basename glob, e.g. 'flyer.pdf' or 'page*.png').
compile() {
  local dest="$1" pattern="$2"; shift 2
  local pages_arg=()
  if [[ "${1:-}" == "single" ]]; then
    pages_arg=(--pages 1)
    shift # drop the sentinel before calling typst
  fi
  (
    cd "${dest}"
    export TYPST__SANDBOX=0
    rm -f *.pdf page*.png   # stray files copied from flyer/ (e.g. test.pdf)
    typst compile --font-path "${FONTS_DIR}" "${pages_arg[@]}" flyer.typ "$@" >/dev/null 2>typst_err.txt
  ) || { echo "----- typst stderr -----"; cat "${dest}/typst_err.txt" >&2; return 1; }
  find "${dest}" -maxdepth 1 -type f -name "${pattern}" | wc -l | tr -d ' '
}

mkdir -p "${OUT_DIR}"

# --- PDF (both pages, single output file) -----------------------------------
tmp_pdf="${OUT_DIR}/pdf"
prepare_flyer "${tmp_pdf}"
echo "== Compiling flyer.typ -> PDF =="
n=$(compile "${tmp_pdf}" "flyer.pdf" "flyer.pdf") || fail "Typst failed to compile the PDF"
[[ -f "${tmp_pdf}/flyer.pdf" ]] || fail "flyer.pdf was not created"
head -c 4 "${tmp_pdf}/flyer.pdf" | grep -q '%PDF' || fail "flyer.pdf is not a valid PDF (bad magic bytes)"
ok "compiled flyer.pdf (${n} file, %PDF ok)"

# --- PNG all pages -----------------------------------------------------------
tmp_all="${OUT_DIR}/png-all"
prepare_flyer "${tmp_all}"
echo "== Compiling flyer.typ -> PNG (both pages) =="
n=$(compile "${tmp_all}" "page*.png" "page{p}.png") || fail "Typst failed to compile the PNGs"
[[ "${n}" -eq 2 ]] || fail "expected 2 page PNGs, got ${n}"
ok "compiled both pages (${n} PNG files)"

# --- PNG single page (pages=1) ----------------------------------------------
tmp_single="${OUT_DIR}/png-single"
prepare_flyer "${tmp_single}"
echo "== Compiling flyer.typ -> PNG (page 1 only) =="
n=$(compile "${tmp_single}" "page*.png" single "page{p}.png") || fail "Typst failed to compile the single-page PNG"
[[ "${n}" -eq 1 ]] || fail "expected 1 page PNG, got ${n}"
ok "compiled single page (${n} PNG file)"

rm -rf "${OUT_DIR}"
echo "== All typst templates compiled successfully =="
