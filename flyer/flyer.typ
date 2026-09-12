#import "textpolyblock/lib.typ": polyblock
// -----------------------------------------------------------------------------
// KPE DIN-lang Wickelfalz-Flyer – editierbares Typst-Template
// Format: 2 x A4 quer, jeweils 3 Paneele à 99 mm = 6 DIN-lang-Seiten.
// Außenseite: [Klappe | Rückseite | Titelseite]
// Innenseite: [Innen links | Innen mitte | Innen rechts]
//

#let show-fold-lines = false

// ===== EDITIERBEREICH =========================================================

#import "metadata.typ"

#let assets = (
  lily: "pictures/Lilie.svg",
  qr-code: "pictures/qrcode-kpe.svg",
  compass: "pictures/compass-transparent.svg",
  people: "pictures/icons/people.svg",
  clock: "pictures/icons/clock.svg",
  map: "pictures/icons/map-pin-house.svg",
  mail: "pictures/icons/mail.svg",
  phone: "pictures/icons/phone.svg",
  web: "pictures/icons/web.svg",
  instagram: "pictures/icons/instagram.svg",
  youtube: "pictures/icons/youtube.svg",
)
#let picture_or(path, override) = {
  // Gibt den Dateinamen als STRING zurück; bei leerem Override wird das
  // Originalfoto verwendet. Damit funktioniert pictures.* direkt als Quelle.
  if override.len() > 0 { "pictures/" + override } else { path }
}

#let pictures = (
  outside_photo: "pictures/BuWaAÖ.jpeg",
  woelflinge: picture_or("pictures/Wölflinge.jpeg", metadata.WOELFLINGE_PHOTO),
  pfadi: picture_or("pictures/Pfadfinder.png", metadata.PFADI_PHOTO),
  raider: picture_or("pictures/Raider2.jpg", metadata.RAADER_PHOTO),
)

#let t = (
  // Innen links
  wichtel: metadata.WICHTEL,
  wichtel_title: "WICHTEL",
  wichtel_age: "ab 4 Jahren",
  wichtel_body: "spielen, toben, Spaß\nhaben, basteln",

  woelflinge_title: "WÖLFLINGE",
  woelflinge_age: "8-11 Jahre",
  woelflinge_body: [So wie Zelten, Singen, Wandern und Kochen\ zu unserem Pfadfindersein dazugehören, so auch das\ gemeinsame Gebet und Sprechen über den Glauben.],

  pfadi_title: "PFADFINDER",
  pfadi_age: "12-16 Jahre",
  pfadi_body: [Als Pfadfinder bringt sich jeder ein - mit seinen\ Ideen, Fähigkeiten und Engagement. Gemeinsam\ bestehen wir Abenteuer und Herausforderungen,\ errichten Lagerbauten, gewinnen Olympiaden und\ helfen tatkräftig bei Hilfseinsätzen.],

  ranger_title: "RANGER & ROVER",
  ranger_age: "ab 17 Jahren",
  // ranger_body: [Als Teil der Union Internationale des Guides et Scouts d'Europe führen unsere Lager über Grenzen hinweg. Dabei lernen wir fremde Kulturen kennen, knüpfen Freundschaften\ und erleben ein lebendiges Europa.],
  // ranger_body: [Selbstverantwortung,\ geimeinsam unterwegs,\ sozialer Einsatz,\ vom Glauben\ Zeugnis geben],
  ranger_body: [Selbstverantwortung, geimeinsam unterwegs, sozialer Einsatz, vom Glauben Zeugnis geben],


  // Blauer Infoblock
  group_title: "GRUPPENSTUNDEN",
  group_time_1: metadata.GROUPTIME,
  group_time_2: "(alle zwei Wochen)",

  // Außenseite – Zitat
  quote: "VERSUCHT, DIE\nWELT EIN BISSCHEN\nBESSER ZURÜCKZU-\nLASSEN, ALS IHR SIE\nVORGEFUNDEN\nHABT.",
  quote_author: "BADEN POWELL",

  // Außenseite – Rückseite/Kontakt
  sfm: metadata.SFM,
  address: metadata.ADDRESS,
  plz: metadata.PLZ,
  email: metadata.MAIL,
  phone: metadata.PHONE,
  youtube: "www.youtube.com/@KPEimNetz",
  web: "www.kpe.de",

  // Außenseite – Titelseite
  cover_name: "KPE",
  cover_place: metadata.STAMM,
  cover_sub: [
    #strong[K]atholische \
    #strong[P]fadfinderschaft \
    #strong[E]uropas
  ]
)

// ===== FARBEN / TYPOGRAFIE ===================================================
#let c_bg = rgb("#F2F7FA")
// #let c_bg = blue
#let c_navy = rgb("#4E5E7F")
#let c_navy_dark = rgb("#445879")
#let c_text = rgb("#202124")
#let c_quote = rgb("#7E90AE")
#let c_quote_light = rgb("#D8E0E9")
#let c_placeholder = rgb("#CCD5DF")
#let c_placeholder_dark = rgb("#AAB6C5")
#let c_white = rgb("#FFFFFF")
#let c_red = rgb("#D71D12")
#let c_yellow = rgb("#FFD21A")

#let panel = 99mm

// ===== Hilfslinien =========================================================


#let fold-lines(width: 297mm, height: 210mm) = {
  if show-fold-lines {
    for i in range(1, 6) {
      let x = width * i / 6
      let major = i == 2 or i == 4

      place(
        top + left,
        dx: x,
        dy: 0mm,
      )[
        #line(
          start: (0pt, 0pt),
          end: (0pt, height),
          stroke: (
            paint: if major { gray.darken(50%) } else { gray },
            thickness: if major { 1.5pt } else { 0.5pt },
            dash: "dashed",
          ),
        )
      ]
    }
  }
}
// ===== PAGE SETTINGS ===================================================
#set page(width: 297mm, height: 210mm, margin: 0mm, fill: c_bg)
// #set text(font: ("Lato", "Liberation Sans", "Arial"), fill: rgb("#202124"))
#set text(font: ("League Spartan"), fill: rgb("#202124"), size: 16pt)
#set par(leading: 0.8em)

// -----------------------------------------------------------------------------

#let headline(body, size: 23pt, color: c_navy, weight: "black", leading: 0.36em) = {
  set text(size: size, weight: weight, fill: color)
  set par(leading: leading)
  body
}

#let subhead(body, size: 11pt, color: c_text) = {
  set text(size: size, weight: "bold", fill: color)
  body
}

#let bodytext(body, size: 10pt, color: c_text, leading: 0.5em) = {
  set text(size: size, weight: "regular", fill: color)
  set par(leading: leading)
  body
}

// Absolute Platzierung auf der A4-Seite.
#let abs(x, y, w, body, h: auto) = {
  place(top + left, dx: x, dy: y,
    block(width: w, height: h, breakable: false)[#body]
  )
}


#let woelfling-photo(path, wolf_x, wolf_y, wolf_z) = {
  let img-fill = tiling(
    offset: (wolf_x, wolf_y),
    image(path, width: 14.5cm * wolf_z)
  )
  let w = 14.5cm
  place(top + left, dx: 2.5cm, dy: -2.3cm,
    polygon(
      fill: img-fill,
      (w/2, 0cm),
      (w, w/2),
      (w/2, w),
      (0cm, w/2)
    )
  )
}

#let pfadi-photo(path, pfx, pfy, pfz) = {
  let img-fill = tiling(
    offset: (pfx, pfy),
    image(path, width: 12cm * pfz)
  )
  let w = 12cm
  let h = 8.4cm
  place(bottom + left, dx: 9.9cm, dy: 0cm,
    polygon(
      fill: img-fill,
      (0cm, 1.2cm),
      (1.2cm, 0cm),
      (9cm, 0cm),
      (w, h/2),
      (9cm, h),
      (0cm, h)
    )
  )
}

#let raider-photo(path, rax, ray, raz) = {
  let w = 13cm
  let h = 14cm
  let img-fill = tiling(
    offset: (rax, ray),
    image(path, height: h * raz)
  )
  place(top + right,
    polygon(
      fill: img-fill,
      (0cm, 7.5cm),
      (7.5cm, 0cm),
      (w, 0cm),
      (w, h),
      (4.8cm, h)
    )
  )
}

#let background-photo(path, zoom, move-x, move-y) ={
  place(top + left, dx: 99mm, dy: 0mm,
  box(width: 198mm, height: 210mm, clip: true)[
    #place(top + left, dx: move-x, dy: move-y,
      image(path, width: zoom)
    )
  ]
  )
}

#let stufen-info(title, age, body, alignment: center) = {
  align(alignment)[
    #set par(spacing: 0.2em)
    #headline(title)
    #v(4.6mm)
    #subhead(age)\
    #v(2.1mm)
    #bodytext(body)
  ]
}

// Berechnet die Bounding Box (x, y, w, h) einer Liste von Polygon-Punkten.
#let bbox(points) = {
  let xs = points.map(p => p.at(0))
  let ys = points.map(p => p.at(1))
  (
    x: calc.min(..xs),
    y: calc.min(..ys),
    w: calc.max(..xs) - calc.min(..xs),
    h: calc.max(..ys) - calc.min(..ys),
  )
}

// Breite eines nach unten spitz zulaufenden, symmetrischen Dreiecks
// (Basis oben bei y=0 mit Breite bb.w, Spitze unten bei y=bb.h) an
// der Position y. Linear interpoliert zwischen voller Breite und 0.
#let triangle-width-at(bb, y) = bb.w * (1 - y / bb.h)

#let ranger-text-box(title, age, body) = {
  let box-width = 10.5cm
  let box-height = 5.2cm
  let pts = (
    (0cm, 0cm),
    (box-width, 0cm),
    (box-width/2, box-height),
  )
  place(top + left, dx: 12.9cm, dy: 4mm,
    box(width: box-width)[
    #set par(spacing: 0.2em)
    #set  align(center)
    #headline(title)
    #v(2.0mm)
    #subhead(age)
    #let padding = -0.01
    #let heigth = 0.8
    #polyblock(
      points: ((padding,0), (1-padding,0), ((1-2*padding)/2, heigth) ),
      stroke: none,
      justify: false,
      body
    )

  ]
  )
}

#let lily(size: 18mm) = {
  image(assets.lily, width: size, height: size, fit: "contain")
}




// =============================================================================
// SEITE 1 – INNENSEITE
// =============================================================================

// Photos
#woelfling-photo(pictures.woelflinge, metadata.WOELFLINGE_X, metadata.WOELFLINGE_Y, metadata.WOELFLINGE_ZOOM)

#pfadi-photo(pictures.pfadi, metadata.PFADI_X, metadata.PFADI_Y, metadata.PFADI_ZOOM)

#raider-photo(pictures.raider, metadata.RAIDER_X, metadata.RAIDER_Y, metadata.RAIDER_ZOOM)


#fold-lines()

#ranger-text-box(t.ranger_title, t.ranger_age, t.ranger_body)

#columns(3, gutter: 0mm)[
  #v(11mm)
  #move(dx: 5mm)[
    #if t.wichtel [
      #stufen-info(t.wichtel_title, t.wichtel_age, t.wichtel_body, alignment: left)
      #v(54.3mm)
    ]else[
    #v(79.8mm)
    ]
    #stufen-info(t.woelflinge_title, t.woelflinge_age, t.woelflinge_body, alignment: left)
  ]
  #v(4mm)
  #box(width: 92%, height: 7cm)[
    #place()[
    #polygon(fill: c_navy,
      (0%, 0%), (100%-1.4cm, 0%), (100%, 1.4cm), (100%, 8cm), (0%, 8cm),
    )]
    #align(center)[
      #v(5mm)
      #image(assets.people, width: 20mm)
      #headline("GRUPPENSTUNDEN", color: c_text, size: 19pt)
    ]
    #move(dx: 2em)[
      #set par(spacing: 0.8em)
      #box(height: 1.1em, baseline: 10%, image(assets.clock)) #t.group_time_1
      #if metadata.twoWEEKS [
      #bodytext((h(3em)+t.group_time_2), size: 14pt)
      ] else [#v(0.5em)]
      #box(height: 1.1em, baseline: 10%, image(assets.map)) #t.address \
      #h(1.4em)#t.plz
    ]
  ]

  #colbreak()
  #v(90mm)
  #align(center)[#lily(size: 25mm)]

  #colbreak()
  #v(160mm)
  #move(dx: 20mm)[#stufen-info(t.pfadi_title, t.pfadi_age, t.pfadi_body, alignment: right)]

]
#pagebreak()

// =============================================================================
// SEITE 2 – AUSSENSEITE
// Reihenfolge beim Wickelfalz: [Klappe | Rückseite | Titelseite]
// =============================================================================

// Großes Außenfoto über Rückseite + Titelseite
#fold-lines()

#background-photo(pictures.outside_photo, 160%, -4cm, 0cm)
#set align(center)
#columns(3, gutter: 0mm)[
  #v(17mm)
  #lily(size: 24mm)
  #place(dx: -5mm )[#text(size: 180pt, weight: "bold", fill: c_quote_light)[“]]
  #v(27mm)
  #headline(t.quote, size: 23pt, color: c_quote, weight: 700, leading: 0.36em)
  #headline(t.quote_author, color: c_quote, weight: 700, leading: 0.36em)
  #place(right, dy: -12mm, image(assets.compass))
  #colbreak()
  #align(left)[
    #move(dx: 10mm )[
    #v(10mm)
    #headline("KONTAKT", color: c_text, size: 28pt, weight: 800)
    #text(if metadata.STAMMESMEISTERIN { "Stammesmeisterin: " } else { "Stammesmeister: " } + t.sfm, size: 15pt)\
    #box(height: 0.8em, baseline: 10%, image(assets.phone)) #t.phone \
    #box(height: 0.8em, baseline: 10%, image(assets.mail)) #t.email

    #if metadata.INSTAGRAM != "" [
      #v(7mm)
      #box(height: 0.8em, baseline: 10%, image(assets.instagram)) #metadata.INSTAGRAM \
    ] else [#v(15mm) ]
    #box(height: 0.8em, baseline: 10%, image(assets.youtube)) #t.youtube \
    #box(height: 0.8em, baseline: 10%, image(assets.web)) #t.web \
  ]]
  #image(assets.qr-code, width: 20mm)
  #colbreak()
  #v(16mm)
  #lily(size: 22mm)
  #text(size: 60pt, weight: 700, fill: c_text, tracking: 0.2em)[#t.cover_name]
  \
  #text(size: 18pt, fill: c_text, tracking: 0.2em)[#t.cover_place]
  #v(116mm)
  #move(dx: 22mm)[
  #align(left)[
    #set par(leading: 0.5em)
    #text(fill: c_text, tracking: 0.1em, )[#t.cover_sub]
  ]
  ]
]
