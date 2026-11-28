# References for the wet media

<!-- cspell:ignore asadi colonygums Cosentino dryingshift etoolbox evap gumarabic IAPWS IFAC krainer Lyubavin openstax patil revigo Swchuck walji webexhibits -->

The register of what `murex.aquarelle` is judged against (`murex-cjx.11`).
The owner has no wet media to paint swatches with, so these replace them:
laws with numbers, published ratings, measured spectra and openly licensed
photographs. `design.md` ("References without swatches") says how each kind
is used. This file is what every session and every agent works from: a
number used in aquarelle's code or tests names its entry here (by the key
after `####`).

Gathered on 2026-11-28 by four searches, one for each kind. Every number
below was read in the source named, at the place given, on a page fetched
that day. Remarks that are not in a source are marked "(my note)" or "(my
arithmetic)". "Archived" is the address the Wayback Machine's
`archive.org/wayback/available` gave; the snapshots themselves could not be
opened from the session that gathered them.

## What is kept, and where

- `references/papers/`: the papers and standards whose licence lets them be
  kept: das2019 (CC BY 4.0), the IAPWS releases on water (republication
  allowed with attribution), asadi2020 (CC BY 4.0), and the full texts of
  walji2016 (CC BY 4.0) and krainer2018 (CC BY 3.0) as Europe PMC's XML,
  their publishers having refused the PDFs.
- `references/spectra/`: Deborah's spectral library (CC BY 4.0) with its
  pigment lists, and the core pigments' spectra taken out of it as plain
  CSV by `tools/aquarelle/extract_deborah.py`; the revigo oil-paint data
  (CC0).
- `references/photos/`: 25 photographs and scans (CC0, public domain, CC BY
  and CC BY-SA), each with its entry below.

PDFs, images and the spectral library (`*.pdf`, `*.png`, `*.jpg`, `*.sli`,
`*.xls`) are in Git LFS. CI does not fetch them, and no test may need one:
a test reads the CSV extracts, which are ordinary files, or numbers written
from this register into the code.

Everything else is cited and not kept: copyrighted papers, pages and charts
(handprint.com, the makers' charts, Deegan, Curtis), and the non-commercial
data (Cosentino 2014, the IFAC databases), which an MIT package should not
carry without the owner deciding so.

### Attribution

What is kept under CC BY or CC BY-SA asks to be credited where it is used,
and CC BY-SA asks that what is made from it be shared alike:

- Photographs: 05 (Les.aqua, CC BY 4.0), 24 (Alexander Lyubavin, CC BY
  2.0), 07 (Oscar, CC BY-SA 3.0 or GFDL), 28 (Francis Flinch, CC BY-SA 3.0
  or GFDL), 29 (Swchuck, CC BY-SA 3.0). Each entry gives the exact credit.
- Data and papers: deborah2022, das2019, walji2016, krainer2018, asadi2020;
  IAPWS for its releases.

## What each behaviour has

The behaviours are those of `design.md` ("What aquarelle has to get right").

| # | Behaviour | Numbers | Ratings | Photographs |
| --- | --- | --- | --- | --- |
| 1 | A wet edge stays where it was painted | gonzalez2019 (stages of wet paper) | handprint diffusion | 03, 10 |
| 2 | Edge darkening | deegan1997, deegan2000 (rim growth, edge flux), patil2019, seo2017, gonzalez2019 | | 11, 12, 22, 20 |
| 3 | Wet-in-wet | | handprint diffusion (0 to 4) | 10, 03 |
| 4 | Backruns | gonzalez2019 (dendrites late in drying) | handprint blossoming | 22 (the only one) |
| 5 | Granulation | Stokes (openstax_stokes); sizes and densities: gonzalez2019, handprint_attributes, handbook_mineralogy, webexhibits_pigments | the table under Ratings | 01, 02 |
| 6 | Staining and lifting | | the table under Ratings; wn-inks-guide (waterproof inks) | 11 (lifting, as read) |
| 7 | Glazing | deborah2022 (four thicknesses over paper); revigo (K and S, oil) | | 20 |
| 8 | Wet is darker | handprint_dryingshift (75 paints, wet and dry); iapws_water, handprint_attributes, gumarabic_reviews (indices) | | |
| 9 | The paper drinks | walji2016, das2019, krainer2018, wu2016xuan | | 06, 27 |
| 10 | Dry brush | | | 10, 21 |
| 11 | Lines of ink | wu2016xuan (ink on xuan) | | 18, 19, 08, 28, 29; 07 and 15 (chromatography) |
| 12 | Markers | | | 24 (alcohol), 15 |
| 13 | Gouache | | wn-designers-gouache-2007 (opacity) | 25, 21 |
| 14 | Conservation | (needs none) | | |

Also: how long a wash takes to dry (gonzalez2019: about 2500 s for a 50 µL
drop on 300 g/m² paper; etoolbox_evap), and water's viscosity, surface
tension and index (iapws_water), and gum arabic's (colonygums_arabic,
gumarabic_reviews).

Colour: deborah2022 for 14 core pigments as they thin over paper, cerulean
and a quinacridone included; Cosentino 2014 (not kept) for 54 pigments in
gum arabic on watercolour paper.

## What the references change in the design

- **A wash does not simply dry lighter.** The one measurement of
  watercolour wet and dry (handprint_dryingshift, 75 paints) finds that it
  mainly loses chroma (−10.7 C* on average) while its lightness changes
  little (+2.3 L*) and either way: fine dark pigments lighten by 7 to 16 L*,
  yellows and cadmiums darken by up to 6, coarse cerulean hardly changes.
  `design.md` says so now.
- **Sizing works through the contact angle, not smaller pores**
  (krainer2018): a sized paper's pores are if anything larger than an unsized
  one's (4.9 µm against 2.6 and 3.9), and water wets them less. The paper's `sizing` acts on how readily water
  enters, not on the size of the paper's pores.
- **The fibres' direction is measured** only on a laboratory paper
  (walji2016, 30% faster along the machine direction), not on watercolour
  paper.
- **Humidity does not change wicking** (walji2016, 30% to 85%), only
  evaporation; temperature acts through the viscosity of water.

## What has no reference

Absolute tones of a given brand, absolute drying times of a whole wash,
backruns and granulation measured physically, dry brush, railroading of a
dip pen, salt and alcohol in a wash, streaks of water-based markers, sumi
bleeding on xuan at close range, named gouache swatches, measured K and S
of watercolour, and anything measured wet. These are built to be there and
to go the right way, then left (`design.md`).

## To check before use

- deegan2000's evaporation constant reads "16.1 g/cm s" in the extracted
  text: probably µg/(cm·s), the micro sign lost.
- gonzalez2019's evaporation rate reads "−1.405 gr/s": the unit is
  incomplete.
- In the ratings table, "lamp black (Daniel Smith)" is under both PBk6 and
  PBk7 with different numbers: one is mis-read.
- The sources on staining disagree (handprint rates the cadmiums 3 to 4,
  the makers hardly mark them; Schmincke alone has phthalo green
  non-staining): which scale a test follows is to be chosen when it is
  written, and said in the test.
- The photographs from Wikimedia Commons are thumbnails (960 to 1920 px,
  3840 for 24): Wikimedia's servers refused the originals. Each entry gives
  the original's address.

The entries below are as they were gathered, with their sources' names,
titles and words in other languages: the spelling check skips them.

<!-- cspell:disable -->

## Physical laws and their numbers, for murex.aquarelle

Gathered 2026-11-28. Every number below was read in the source named, at the place given. Where a PDF's text extraction lost symbols (Greek letters, exponents), that is said at the number. Remarks of mine that are not in a source are marked "(my note)".

### Coffee ring and edge darkening

#### deegan1997
- Citation: R. D. Deegan, O. Bakajin, T. F. Dupont, G. Huber, S. R. Nagel, T. A. Witten, "Capillary flow as the cause of ring stains from dried liquid drops", Nature 389, 827-829 (1997). DOI 10.1038/39827
- Address: https://jfi.uchicago.edu/~tten/Science%20topics/Coffee.drops/Nagel.7.4.pdf (authors' preprint, "typeset July 15, 1997", 4 pages; publisher's page https://www.nature.com/articles/39827) ; Archived: preprint none; publisher's page http://web.archive.org/web/20261031171932/https://www.nature.com/articles/39827
- Read: 2026-11-28
- Licence: copyright (Nature); authors' preprint on a University of Chicago page; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - Conditions for a ring (p. 1, col. 2): "(1) the solvent meets the surface at a nonzero contact angle, (2) the contact line is pinned to its initial position, and (3) the solvent evaporates." Surface-tension gradients, solute diffusion, electrostatics and gravity "are negligible in ring formation".
  - Evaporative flux near the pinned edge (p. 2): J(r) ~ (R - r)^-lambda; as the contact angle goes to zero, lambda goes to 1/2 (exact formula given in deegan2000, Eq. 5).
  - Depth-averaged outward velocity (p. 2): v(r) ~ (R - r)^-lambda; Eq. (1) t = integral dr/v ~ (R - r_t)^(1+lambda).
  - Early ring growth (p. 2): M(R, t) ~ t^(2/(1+lambda)). For contact angle about 0.25 rad the theory predicts M ~ t^1.37; measured power-law fits gave p = 1.3 +- 0.1 (p. 3; Fig. 3 solid line (M - M0) = const (t + t0)^1.37).
  - Late times (p. 2): the height falls to zero as (t_f - t), v must grow as (t_f - t)^-1, "all initial points r > 0 are carried to the perimeter before the drying time t_f".
  - Experiment (p. 2-3): polystyrene microspheres at starting volume fraction 10^-4; drops of nominal radius 4 mm on glass; total drying time about 800 s for the drops of Fig. 3 (inset: entire 1300 s drying time); "Roughly 90 percent of the particles were observed to go to the contact line" (Fig. 3 caption); the volume decreased at a rate within 2% of steady vapour-diffusion-limited evaporation.
  - Early transient (p. 3): before t ~ (4R)^2/D, about 10 s, steady diffusion is not established; a time shift of order 10 s was allowed.
  - Modifiers (p. 3): non-circular drops: "highly convex regions have a stronger evaporating flux and thus denser deposits"; higher initial concentration gives a wider ring; Marangoni circulation was observed but its impact was minor; high viscosity can prevent the equilibrium shape, negligible here "except within a few microns of the contact line".
  - Pinning (p. 3): "Contact line pinning is produced by surface irregularities and is much stronger with the solute than without it."
- Settles: edge darkening of a wet-on-dry stroke; ring mass growth with time; dependence on contact angle; stronger rim at convex corners of a stroke.
- Proposed test: a round puddle of dilute pigment dried with a pinned edge must put most of its pigment (of order 90%) within a narrow rim, and the rim's pigment, plotted against time in log-log, must rise with a slope near 2/(1+lambda) (1.3-1.4 for small angles) before a late surge; convex parts of an irregular outline must end darker than straight parts.

#### deegan2000
- Citation: R. D. Deegan, O. Bakajin, T. F. Dupont, G. Huber, S. R. Nagel, T. A. Witten, "Contact line deposits in an evaporating drop", Phys. Rev. E 62, 756-765 (2000). DOI 10.1103/PhysRevE.62.756
- Address: https://public.websites.umich.edu/~rddeegan/PDF/Coffee_Rings_3_PRE.pdf (author's page, published version) ; Archived: http://web.archive.org/web/20250828141829/https://public.websites.umich.edu/~rddeegan/PDF/Coffee_Rings_3_PRE.pdf
- Read: 2026-11-28
- Licence: copyright 2000 The American Physical Society; author's copy; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - Sec. I: the flow "is capable of transferring 100% of the solute to the contact line"; Fig. 1 and Sec. I name "enhanced edges in water color paintings" as an instance.
  - Sec. II: rings seen on glass, metal, polyethylene, roughened Teflon, mica, ceramic, silicon; drops from 1 mm to 15 cm; solvents water, acetone, methanol, toluene, ethanol; solutes from molecules (sugar, dyes) to 10 um spheres; solute volume fractions 10^-6 to 10^-1; temperature, humidity and pressure "could be extensively varied without affecting the ring".
  - Eq. (5): J_s(r,t) ~ (R - r)^-lambda with lambda = (pi - 2 theta_c)/(2 pi - 2 theta_c).
  - Sec. IV: for a drop starting at a contact angle of 15 deg, lambda goes from 0.455 to 0.5 over the drying; in the thin-drop limit h(0,t) = h(0,0)(1 - t/t_f) (centre height falls linearly in time).
  - Eq. (10): m_R ~ t^(2/(1+lambda)) at early times.
  - Fig. 6(b): evaporation rate dM/dt, normalised to 0% relative humidity and 20 C, proportional to the drop radius R (diffusion limited, not to the area): fitted alpha = 16.1 +- 0.4, theory 16.5, printed units "g/cm s" (the text extraction shows no power of ten; (my note) 4 D c_s for water at 20 C is about 1.6e-5 g/(cm s), so the printed figure is presumably in ug/(cm s), the micro sign lost like the other Greek letters of the extraction: check on the page before using it).
  - Sec. V, Fig. 8: measured velocity exponent 0.54 +- 0.06 against a predicted 0.47 +- 0.01.
  - Fig. 10: run with t_f = 326 s, R = 2.08 mm, theta_c = 0.26 rad; fit N = N_p (t/t_f)^1.38.
  - Sec. V: only about 50% of the expected solute had reached the edge at the time the theory predicted; complete transfer still happens, but later ("the theory predicts that the material arrives at the contact line earlier than it actually does").
  - Sec. V: drops without solute first shrink in contact angle at fixed base, then unpin; ring-forming drops have no unpinned phase: "the drop is self-pinning".
  - Sec. V, Fig. 11-12: a surface layer of particles (Marangoni inward surface flow) held about 10% of the solute; it breaks up at late times and goes to the contact line.
  - Sec. VI: sedimentation of large particles reduces what reaches the edge; viscosity distorts the drop near the edge, negligible for water; for 1 um particles the theory accounted for 50% of the ring growth, for 0.1 um particles much better.
  - Fig. 9: shielding the drop's edge from evaporation (a chamber with a small hole, a bath around a pedestal) moves the deposit: the vapour field controls the pattern.
- Settles: edge darkening; that large or dense particles (settling) reach the rim less; that a stroke keeps its outline (self-pinning) once pigment is at the edge.
- Proposed test: for a fixed wet patch, the fraction of pigment ending in the rim must fall as the settling speed of the pigment rises (heavier pigments darken edges less and granulate more), and must rise towards 1 for fine, light pigment.

### Watercolour, simulated

#### curtis1997
- Citation: C. J. Curtis, S. E. Anderson, J. E. Seims, K. W. Fleischer, D. H. Salesin, "Computer-Generated Watercolor", Proc. SIGGRAPH 97, 421-430 (1997). DOI 10.1145/258734.258896
- Address: https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf (authors' copy on the project page https://grail.cs.washington.edu/projects/watercolor/) ; Archived: http://web.archive.org/web/20260302170657/https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf
- Read: 2026-11-28
- Licence: copyright ACM; authors' copy; not kept
- Kept file (in `references/papers/`): none
- Numbers and behaviours:
  - Sec. 2.1: pigments "ground ... into a powder made of grains ranging from about 0.05 to 0.5 microns"; lighter pigments stay suspended longer and spread further; granulation (settling into the hollows of rough paper) and flocculation (clumping, "usually by electrical effects") named; paper of linen or cotton rag, "mostly air"; sizing "slows the rate of water absorption and diffusion"; the surfactant "allows water to soak into sized paper".
  - Sec. 2.2, Fig. 1 (real watercolour): drybrush; edge darkening (wet-on-dry, sizing and surface tension stop the stroke spreading and pigment migrates to its edge); backruns ("a puddle of water spreads back into a damp region of paint ... complex, branching shapes with severely darkened edges"); granulation, "strongest when the paper is very wet", and separation ("denser pigments settle earlier than lighter ones"); flow patterns in wet-in-wet (soft, feathery, striations along the flow); glazing, with "low resolubility" paints.
  - Sec. 3: three layers: shallow water above the paper, pigment deposition, capillary layer (only for backruns).
  - Sec. 4.1: paper as a height field 0 < h < 1; fluid capacity c = h (c_max - c_min) + c_min.
  - Sec. 4 (list of the shallow-water quantities) and 4.3.2: viscosity and viscous drag set to 0.1 and 0.01 in all examples (symbols lost in the extraction; dimensionless, per pixel and time step); divergence relaxation with N = 50 iterations, tolerance 0.01, step 0.1.
  - Sec. 4.3.3, Eq. (3): edge darkening by removing water near the wet edge: Gaussian blur K x K of the wet mask, K = 10, strength between 0.01 and 0.05; the section cites the pinned-contact-line mechanism of Deegan et al. [3].
  - Sec. 4.3.1: time step adaptive so that velocities do not exceed one pixel per step; "our solution is resolution-dependent".
  - Sec. 4.5: adsorption down = g (1 - h gamma) rho, desorption up = d (1 + (h - 1) gamma) rho / omega (density rho, staining power omega, granulation gamma; operators partly lost in the extraction).
  - Sec. 4.6: backruns occur "only when a puddle of water spreads slowly into a region that is drying but still damp"; water diffuses cell to cell up to capacity c; thresholds for giving and receiving water; the variation of capacity gives the branching.
  - Fig. 5 table, per pigment K (r,g,b), S (r,g,b), then three columns that by Sec. 4.5 are density, staining power, granulation (headers partly lost): e.g. "French Ultramarine" K 0.86 0.86 0.06, S 0.005 0.005 0.09, then 0.01, 3.1, 0.91; "Cerulean Blue" K 1.52 0.32 0.25, S 0.06 0.26 0.40, then 0.01, 1.0, 0.31; "Burnt Umber" K 0.74 1.54 2.10, S 0.09 0.09 0.004, then 0.09, 9.3, 0.90; "Quinacridone Rose" K 0.22 1.47 0.57, S 0.05 0.003 0.03, then 0.02, 5.5, 0.81; "Phthalo Green" K 1.55 0.47 0.63, S 0.01 0.05 0.035, then 0.02, 1.0, 0.12. These are hand-set, not measured.
  - Fig. 10: 11 glazes, 2750 iterations, 640 x 480, 7 hours on a 133 MHz SGI R4600.
- Settles: the list of behaviours to reproduce (drybrush, edge darkening, backruns, granulation and separation, flow patterns, glazing); not physical numbers: its parameters are dimensionless and hand-set, and it says so ("by no means a strict physical simulation", Sec. 1).
- Proposed test: each of the six effects of Fig. 1 must be produced by the physics, not by a dedicated mechanism; in particular edge darkening must arise from evaporation at a pinned edge (as deegan1997) rather than from an imposed pressure drop near the mask edge as in Curtis's Eq. (3).

#### gonzalez2019
- Citation: J. González-Gutiérrez, O. Moctezuma, V. Angeles, M. Rios-Ramirez, S. Zetina, A. Marin, R. Zenit, "Pattern formation by droplet evaporation and imbibition in watercolor paintings", arXiv:1909.09098 [physics.flu-dyn] (v1, 19 Sep 2019). No journal version found on Crossref.
- Address: https://arxiv.org/pdf/1909.09098 (abstract https://arxiv.org/abs/1909.09098) ; Archived: http://web.archive.org/web/20260310104219/https://arxiv.org/abs/1909.09098
- Read: 2026-11-28
- Licence: arXiv non-exclusive distribution licence (not CC); not kept
- Kept file (in `references/papers/`): none
- Numbers (real Winsor & Newton pigment on Fabriano watercolour paper):
  - Methods, "Watercolor ink preparation": Mars Black, Ultramarine Blue, Rose Genuine, Permanent Rose (Winsor & Newton) powders in deionised water at 0.0075 g/mL at 22 C ("very close to the saturation concentration of the Mars Black"), diluted to 0.00375, 0.001875, 0.000937, 0.000468, 0.000234, 0.000117 g/mL. No gum arabic was added: these are pigments in water, not paint.
  - Methods, "Drop evaporation": cold-pressed Fabriano watercolour paper, 25% cotton, 300 g/m2; drops of 50 uL; 22 C, 35% relative humidity; time for complete evaporation of a drop on dry paper "around 2500s"; Results: t_c (mass down by 1/e) = 2490 s for 50 uL.
  - Table I, particle sizes by dynamic light scattering (mode: size nm, error nm, share %): Mars Black (synthetic iron oxides) 1528 (504) 53.4%; 258 (71) 43.3%; 5322 (374) 3.3%. Ultramarine 3810 (78) 55.4%; 1669 (401) 44.6%. Permanent Rose (quinacridone) 272 (73) 83.8%; 99 (19) 16.2%. Rose Genuine (Rubia tinctorum) 164.5 (29) 50.4%; 573 (118) 49.6%.
  - Results, dry paper: every pigment made a ring ("coffee rings effect is a universal effect"); mean pixel intensity of the inner deposit against relative concentration phi_p follows Eq. (1) mu = -mu0 exp(-phi_p/k) + mu_s (saturating); ring thickness grows with concentration for the colloidal (rose) pigments and does not change for the larger, denser black and blue ones, most of whose particles "sediment in the order of seconds" (settling velocities in their supplementary Fig. 1s, not read).
  - Results, wet paper: drying paper passes through three water distributions: (I) water bodies (puddles, glossy), (II) stagnant water in the surface cavities (gloss), short-lived, (III) water in bulk between pores and fibres (dull). A drop on (I) spreads by fast imbibition (t/t_c = 0.06) into radial tips, then slow diffusion from centre outwards (t/t_c = 0.12-0.361); on (II) large stains with sharp tips (t/t_c = 0.016-0.0301), then a ring (t/t_c = 1.35), gone by t/t_c = 1.8; on (III) a lower contact angle, a fast ring and dendrites around it (t/t_c = 0.15), finished at t/t_c = 3.01. The stain's structure depends on the water distribution, not on the paper's water content (Discussion, points 4-6 and 10: "The creation of dendrites emerges in the last stage of evaporation"); "Colour gradients arise from the sedimentation of non-colloidal particles" (point 8).
  - Methods, "Wetting and drying paper processes": paper soaked 3 minutes; the slope of surface water density against time gave an evaporation rate printed as "-1.405gr/s +-0.027" (units as printed; the quantity is a surface density per time, so the printed unit is incomplete: read Fig. 7c before using it).
- Settles: edge darkening on dry paper for every pigment; granulation and gradients from settling of large dense particles (ultramarine, iron oxide) while fine quinacridone stays suspended; backrun and dendrite formation in the late damp stage (III); drying time of a drop on watercolour paper.
- Proposed test: a 50 uL drop on dry 300 g/m2 paper at 22 C and 35% RH should take of order 2500 s to dry and leave a ring with every pigment; dropped on paper in its damp, dull stage it should grow dendrites around a ring, while on glossy wet paper it should spread into soft radial tips; a fine quinacridone should thicken its ring with concentration, a coarse ultramarine should not.

### Wicking in paper

#### walji2016
- Citation: N. Walji, B. D. MacDonald, "Influence of Geometry and Surrounding Conditions on Fluid Flow in Paper-Based Devices", Micromachines 7(5), 73 (2016). DOI 10.3390/mi7050073
- Address: https://www.mdpi.com/2072-666X/7/5/73 (read as full text from Europe PMC, PMC6190155: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6190155/fullTextXML) ; Archived: http://web.archive.org/web/20250714134142/https://www.mdpi.com/2072-666X/7/5/73
- Read: 2026-11-28
- Licence: CC-BY 4.0
- Kept file (in `references/papers/`): walji2016_micromachines_paper_flow.europepmc.xml (the publisher's PDF refused automated download; the full text kept is Europe PMC's JATS XML)
- Numbers:
  - Eq. (1), Sec. 3.1: Washburn, x = sqrt(gamma r_c cos(theta) t / (2 mu)), distance proportional to the square root of time; wicking distance proportional to mu^-1/2 confirmed against temperature (Fig. 3).
  - Sec. 3.1: Whatman 1 CHR strip, 10 mm wide, 45 mm long: about 11 min to wick 45 mm at 15 C; about 8 min with fluid at 35 C (air 45 C); "the temperature of the fluid in the reservoir ... influenced the wicking behaviour rather than the air temperature".
  - Sec. 3.2: humidity from 30% to 85% at 20 C: wicking time "a consistent value of approximately 7 min" for 45 mm, no effect beyond error.
  - Sec. 3.3, Fig. 5: Whatman 17 CHR, 10 mm wide: machine direction faster than cross direction, the difference growing with distance; to 45 mm "30% faster than in the cross direction".
  - Sec. 3.5, Fig. 7-8: thin paper (1 CHR, 0.18 mm) wicks faster in wider strips (5 to 40 mm), the dependence fading with width; thick paper (17 CHR, 0.70 mm) shows no width effect.
  - Table 1: Whatman 1 CHR: 87 g/m2, 0.18 mm, porosity 67.8%, flow rate 4.33 mm/min; Whatman 17 CHR: 325 g/m2, 0.70 mm, porosity 69.1%, flow rate 6.33 mm/min.
  - Sec. 3.6: "post-wetting flow": the strip kept darkening with dye for 17 min after the front reached the end (Fig. 9).
- Settles: wicking front (sqrt t), its temperature dependence through viscosity, its indifference to humidity, anisotropy along the grain.
- Proposed test: a front fed from a reservoir must advance as sqrt(t) (log-log slope 0.5) and, on an anisotropic paper, a round drop's wicked stain must become an ellipse whose axes differ by tens of per cent (on 17 CHR, "30% faster" to 45 mm; (my note) under x ~ sqrt(t) a 1.3 times shorter time means about 14% more distance at equal time).

#### das2019
- Citation: D. Das, A. Dsouza, N. Kaur, S. Soni, B. J. Toley, "Paper Stacks for Uniform Rehydration of Dried Reagents in Paper Microfluidic Devices", Scientific Reports 9, 15755 (2019). DOI 10.1038/s41598-019-52202-9
- Address: https://www.nature.com/articles/s41598-019-52202-9 (read as full text from Europe PMC, PMC6823543) ; Archived: http://web.archive.org/web/20230715182828/https://www.nature.com/articles/s41598-019-52202-9
- Read: 2026-11-28
- Licence: CC-BY 4.0
- Kept file (in `references/papers/`): das2019_scirep_paper_stacks.pdf
- Numbers:
  - Results, "Rationale ...": L = K sqrt(t); Washburn coefficient K = 0.38 cm/s^0.5 for Whatman filter paper (Grade 1, Methods) and 1.19 cm/s^0.5 for Standard 17 glass fibre, from the time to wick 4 cm: T_4cm = 110 s (filter paper) and 11.3 s (glass fibre); through the 180 um thickness of the filter paper, 2.43 ms.
  - Methods: strips 1 cm wide (filter paper) laid horizontally in a humidity chamber; water.
- Settles: the magnitude of the wicking coefficient of an unsized cellulose paper: K about 3.8 mm/s^0.5, i.e. 1 cm in about 7 s, 4 cm in 110 s.
- Proposed test: on an unsized (blotting) paper preset, water fed at a line must reach 4 cm in of order 100 s and 1 cm in of order 7 s; a sized watercolour paper must be far slower (no measured coefficient for sized watercolour paper was found).

#### krainer2018
- Citation: S. Krainer, U. Hirn, "Short timescale wetting and penetration on porous sheets measured with ultrasound, direct absorption and contact angle", RSC Advances 8, 12861 (2018). DOI 10.1039/c8ra01434e
- Address: https://pubs.rsc.org/en/content/articlehtml/2018/ra/c8ra01434e (read as full text from Europe PMC, PMC9079626) ; Archived: http://web.archive.org/web/20240415111819/https://pubs.rsc.org/en/content/articlehtml/2018/ra/c8ra01434e
- Read: 2026-11-28
- Licence: CC-BY 3.0
- Kept file (in `references/papers/`): krainer2018_rscadv_penetration.europepmc.xml (PDF refused automated download)
- Numbers:
  - Table 1 (wood-free fine papers, bleached hardwood): AKD sized: 77.2 g/m2, filler 13.52%, porosity 20.6%, average pore diameter 4.9 um; unsized (HSI treated): 78.5 g/m2, 21.51%, 38.8%, 2.6 um; pigmented: 79.89 g/m2, 22.98%, 23.6%, 3.2 um; unsized and untreated: 97.2 g/m2, 21.51%, 40.3%, 3.9 um.
  - Table 2 (liquids): water 1.004 mPa s, 72.4 mN/m; 80% water/20% glycerin 1.6 mPa s, 65 mN/m; 80% water/20% glycol 1.7 mPa s, 71 mN/m; inks 5-6.3 mPa s, 32.8-37.4 mN/m.
  - Sec. 2: climate room 23 C, 50% RH (ISO 187).
  - Results (Fig. 9): water, water/glycerin and water/glycol into the unsized untreated paper were "too fast" to be measured by the scanning absorptometer (10 ms to 10 s range); into the AKD sized paper the liquids with 80-100% water "penetrate really slowly", found by both ultrasound and absorptometry. The coefficients themselves are in figures and the ESI, not read.
  - "Contact angle calculated from scanning absorptiometry", Eqn (1): Lucas-Washburn penetration H in terms of pore diameter D, surface tension gamma, viscosity eta and contact angle theta_LW, H proportional to sqrt(t) (Fig. 7 shows H linear in sqrt(t)); used to compute an apparent contact angle from absorption. (The equation is an image in the full text; its exact form was not read.)
- Settles: how sizing changes wicking: it acts through the contact angle (cos theta), not through pore size (the sized paper has the larger pores here).
- Proposed test: sizing in the model should enter as an apparent contact angle near or above 90 deg that stops capillary entry (water stands on the paper for seconds), not as a smaller pore radius.

### Evaporation

#### etoolbox_evap
- Citation: The Engineering ToolBox, "Evaporation from a Water Surface" (2004).
- Address: https://www.engineeringtoolbox.com/evaporation-water-surface-d_690.html ; Archived: http://web.archive.org/web/20261031030846/https://www.engineeringtoolbox.com/evaporation-water-surface-d_690.html
- Read: 2026-11-28
- Licence: copyright, reference web page; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - Eq. (1): g_h = Theta A (x_s - x) kg/h, with Theta = 25 + 19 v kg/(m2 h), v the air speed over the surface in m/s; x_s the saturation humidity ratio at the water surface temperature, x the humidity ratio of the air (kg/kg). The page calls it empirical (its units do not match) and gives no primary source.
  - Worked example: water 20 C, x_s = 0.014659 kg/kg; air 25 C, 50% RH, x = 0.0098 kg/kg; v = 0.5 m/s; Theta = 34.5 kg/(m2 h); latent heat 2454 kJ/kg at 20 C.
  - (my note, arithmetic on the page's numbers): the worked example gives 34.5 x (0.014659 - 0.0098) = 0.168 kg/(m2 h), i.e. 0.17 mm of water per hour; in still air (Theta = 25) about 0.12 mm/h for the same humidities. A wash of 0.1 mm of free water would then take of order an hour at the surface alone, faster where it soaks in.
- Settles: drying time of a wash and its dependence on humidity (through x_s - x) and air speed (Theta).
- Proposed test: the evaporation rate per area should be linear in (x_s - x) and rise by about 76% per m/s of air (19/25); halving the humidity deficit should double the drying time of a free film.

### Pigments: size, density, refractive index

#### handprint_attributes
- Citation: B. MacEvoy, "the material attributes of paints", handprint.com (last revised 8 Jan 2015). Tables compiled from Handbook of Industrial Chemistry (1999), Gettens & Stout, Painting Materials (1956), Artists' Pigments (1996-2005), Kremer Pigments and manufacturer data (as the page says under each table).
- Address: https://www.handprint.com/HP/WCL/pigmt3.html ; Archived: http://web.archive.org/web/20260818014606/https://www.handprint.com/HP/WCL/pigmt3.html
- Read: 2026-11-28
- Licence: copyright 2015 Bruce MacEvoy; not kept. A secondary compilation by a watercolourist, not a measurement; its numbers are representative values per pigment family, given as rows of a scale (a pigment is listed in the row nearest its typical value).
- Kept file (in `references/papers/`): none
- Numbers:
  - Table "average pigment particle size" (section "Particle Size"), rows: 50 um: cobalt violet, manganese blue; 10 um: cobalt green, cobalt turquoise, cerulean blue, manganese violet, black iron oxides; 5 um: ultramarine blue (RS), viridian, cobalt blue, violet (brown) iron oxides, yellow iron oxides; 1 um: ultramarine blue (GS), red iron oxides, cadmium red, cadmium orange, semi-opaque synthetic organics (diarylides, pyrroles, naphthols, perinone orange); 0.5 um: chromium oxide green, cadmium yellow, bismuth yellow, titanium white, transparent red and yellow iron oxides, semi-transparent organics (arylides, benzimidazolones, dioxazines, perylenes); 0.1 um: zinc white, iron (prussian) blue, transparent organics (quinacridones, phthalocyanines); 0.05 um: carbon black. Note under the table: aggregates or agglomerates "may be 5 to 50 times larger than the sizes listed".
  - Table "pigment refractive index" (section "Refractive Index"), pigment RI and RI ratio to the vehicle: air 1.0; water 1.33; phthalocyanines, arylide yellows 1.4; gum arabic 1.47 (acrylic resin 1.49), ratio 1.00; ultramarine blue, iron blue, indanthrone, alumina hydrate 1.5; viridian, naphthol reds, ultramarine violet, kaolin 1.6; cobalt blue, perylene red, benzimidazolone yellows 1.7; cerulean blue, lamp black 1.8; burnt sienna 1.9; zinc white, quinacridone red and violet, raw umber 2.0; raw sienna 2.2; cadmium yellow, burnt umber, bone black 2.3; chromium oxide, titanium white (anatase) 2.5; cadmium red 2.6; titanium white (rutile) 2.7; venetian red 2.8. Note: values "in some cases represent the average of a range of values for the principal (alpha) refraction index".
  - Same section: "A pigment appears significantly cloudy when the RI ratio is around 1.33, and almost completely opaque when it is above 1.5"; watercolour pigments lie "almost naked" on the fibres, so their RI ratio is against air; scattering at the particle surface "causes a drying shift in the pigment color: many watercolors become lighter and less saturated as they dry, especially those with particle sizes below 1.0um"; a dilute gum arabic varnish over dried paint reduces surface scattering and deepens the colour (pigmt1.html, "Binder").
  - Table "pigment specific gravity" (section "Specific Gravity"): 1.4 arylide yellows; 1.5 diarylide yellows, quinacridone violet, quinacridone rose, indanthrone blue; 1.6 quinacridone red, naphthol reds, phthalocyanine blues, dioxazine violet; 1.7 benzimidazolone yellows, perylenes, perinone orange; 1.8 pyrrole reds, carbon (lamp) black, iron (prussian) blue; 2.1 phthalocyanine greens; 2.3 ultramarine blue, ultramarine violet, carbon (bone) black; 2.5 aluminium hydrate, manganese violet; 3.0 raw sienna, raw umber; 3.5 burnt sienna, burnt umber, cobalt violet, viridian; 4.0 yellow iron oxide, titanium white, cobalt blue, cobalt teal blue; 4.5 cadmium yellows, cerulean blue, cobalt turquoise; 5.0 cadmium reds, red iron oxide, black iron oxide, transparent iron oxides, chromium oxide green; 5.5 zinc white.
  - "Sedimentation test": tinting solutions left standing clear in their upper half in "three to seven days, depending on the particle size and specific gravity".
  - Groups (same section): small and light (synthetic organics, iron blue, carbon black) stay in suspension and diffuse and backrun; heavy or large ("sedimentary": cobalts, chromiums, cadmiums, some earths) settle and granulate.
- Settles: granulation order and separation of pigments (Stokes speed from size and density); wet-darker / dries-lighter shift and its dependence on particle size; transparency.
- Proposed test: ranked by Stokes speed from these sizes and densities, cerulean, cobalt, viridian and coarse ultramarine must granulate and settle out first, phthalocyanine, quinacridone and carbon black last (they must stay in suspension through a wash's drying); fine pigments (below 1 um) must show a larger lightening on drying than coarse ones.

#### handprint_making
- Citation: B. MacEvoy, "how watercolor paints are made", handprint.com (last revised 8 Jan 2015).
- Address: https://www.handprint.com/HP/WCL/pigmt1.html ; Archived: http://web.archive.org/web/20261026143016/https://www.handprint.com/HP/WCL/pigmt1.html
- Read: 2026-11-28
- Licence: copyright 2015 Bruce MacEvoy; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - "Pigment": pigment share of total volume of tube paint: under 10% to about 20% for phthalocyanines, red quinacridones, dioxazine, alizarin; 20-30% for prussian blue, carbon black, raw iron oxides, zinc and titanium white, most synthetic organics; 30-40% for yellow iron oxides, viridian, ultramarine blue and violet, finer cobalts; 40-50% for cadmium yellows, cobalt violet, burnt iron oxides; 50% or more for cadmium orange and reds, manganese violet and blue ("illustrative").
  - "Binder": the vehicle is "about 65% of vehicle volume" binder (gum arabic); plasticiser (glycerin) "usually 20% or less of vehicle volume"; "Water": tube paints "contain about 15% by volume of water".
  - Home recipe: gum arabic solution 1 part gum to 2 parts boiling water (by the page's measures); vehicle 9 T gum solution, 1 T glycerin, 1 T humectant.
- Settles: the starting composition of a paint (pigment volume fraction, gum arabic and glycerin content), from which a wash's gum concentration follows by dilution.
- Proposed test: a dried wash's binder-to-pigment volume ratio should follow from the tube composition (gum about two thirds of the vehicle), independent of how much water dilutes it; a dilute wash then lies as nearly bare pigment on the fibres only if the gum is spread thin over the paper (my note: check against what the model keeps on the paper).

#### webexhibits_pigments
- Citation: WebExhibits, "Pigments through the Ages", technical pages (Institute for Dynamic Educational Advancement).
- Address: https://www.webexhibits.org/pigments/indiv/technical/ultramarine.html, .../viridian.html, .../titaniumwhite.html, .../ceruleanblue.html, .../carbonblack.html ; Archived: http://web.archive.org/web/20260711082606/https://www.webexhibits.org/pigments/indiv/technical/ultramarine.html (the others not checked)
- Read: 2026-11-28
- Licence: copyright WebExhibits; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - Ultramarine (PB 29, Na8-10 Al6 Si6 O24 S2-4): refractive index 1.5; "Particles are usually between 1-50um in size"; synthetic particles "more uniform and finely divided", "more rounded finer particles".
  - Viridian (the page shows Cr2O3 . 2H2O and "Color Index (C.I.) PG 17"; handprint names viridian PG18, and (my note) PG 17 is usually anhydrous chromium oxide green, so the page's index number looks wrong): refractive index "alpha and beta = 1.62; gamma = 2.12"; "Particle size is usually 1-10um".
  - Titanium white (PW 6): refractive index "anatase: 2.3 - 2.65" (rutile not shown in the text read); "Particles are usually up to 1um in size".
  - Cerulean blue (PB 35, cobalt(II) stannate): refractive index n/a; particles "fine, rounded and uniform"; "not recommended for use in watercolor painting because of chalkiness in washes".
  - Carbon black (PBk 6): refractive index n/a. No page found for cobalt blue, phthalocyanine blue, quinacridone, burnt sienna (404).
- Settles: refractive indices and particle sizes for ultramarine, viridian, titanium white, as a cross-check of handprint_attributes.
- Proposed test: none of its own; it corroborates handprint's indices (ultramarine 1.5, viridian 1.6).

#### handbook_mineralogy
- Citation: J. W. Anthony, R. A. Bideaux, K. W. Bladh, M. C. Nichols (eds.), Handbook of Mineralogy, Mineralogical Society of America; data sheets for lazurite (natural ultramarine), rutile and anatase (titanium white), hematite (red iron oxide: burnt sienna, Mars red), goethite (yellow iron oxide: raw sienna, yellow ochre), eskolaite (Cr2O3, chromium oxide green). Mineral Data Publishing, 2001-2005.
- Address: https://www.handbookofmineralogy.org/pdfs/lazurite.pdf (and rutile.pdf, anatase.pdf, hematite.pdf, goethite.pdf, eskolaite.pdf) ; Archived: lazurite http://web.archive.org/web/20240727205031/https://handbookofmineralogy.org/pdfs/lazurite.pdf ; rutile http://web.archive.org/web/20260922120621/http://www.handbookofmineralogy.org/pdfs/rutile.pdf ; hematite http://web.archive.org/web/20261109044202/https://www.handbookofmineralogy.org/pdfs/hematite.pdf ; anatase http://web.archive.org/web/20261117023633/http://www.handbookofmineralogy.org/pdfs/anatase.pdf ; goethite http://web.archive.org/web/20260503043818/https://www.handbookofmineralogy.org/pdfs/goethite.pdf ; eskolaite not checked
- Read: 2026-11-28
- Licence: copyright 2001-2005 Mineral Data Publishing, reproduced by permission; not kept
- Kept file (in `references/papers/`): none
- Numbers ("Physical Properties" and "Optical Properties" of each sheet; the symbol of the second index of uniaxial minerals is lost in the extraction, it is epsilon):
  - Lazurite: D(meas.) = 2.38-2.45, D(calc.) = 2.39-2.42; isotropic, n = 1.502-1.522.
  - Rutile: D(meas.) = 4.23(2); omega = 2.605-2.613, epsilon = 2.899-2.901.
  - Anatase: D(meas.) = 3.79-3.97; omega = 2.5612, epsilon = 2.4880.
  - Hematite: D(meas.) = 5.26, D(calc.) = 5.255; omega = 3.15-3.22, epsilon = 2.87-2.94.
  - Goethite: D(meas.) = 4.28(1); alpha = 2.260-2.275, beta = 2.393-2.409, gamma = 2.398-2.515.
  - Eskolaite: D(meas.) = 5.18, D(calc.) = 5.20.
- Settles: the density in Stokes's law and the index contrast for natural ultramarine, titanium white, iron-oxide earths. Synthetic pigments of the same compound (French ultramarine, Mars colours) have the crystal density; earths diluted with clay are lighter (handprint gives raw sienna 3.0, burnt sienna 3.5 against hematite 5.26).
- Proposed test: with these densities, Stokes speeds at equal size rank hematite > goethite > rutile > anatase > lazurite, about 4.26 : 3.28 : 3.23 : 2.88 : 1.41 in (rho_p - 1) (my arithmetic, middle of each range); a pure iron oxide must settle about three times faster than ultramarine of the same size.

#### iapws_water
- Citation: International Association for the Properties of Water and Steam: IAPWS R1-76(2014), "Revised Release on Surface Tension of Ordinary Water Substance" (Moscow, June 2014); IAPWS R9-97, "Release on the Refractive Index of Ordinary Water Substance as a Function of Wavelength, Temperature and Pressure" (Erlangen, September 1997); IAPWS R12-08, "Release on the IAPWS Formulation 2008 for the Viscosity of Ordinary Water Substance" (Berlin, September 2008).
- Address: https://iapws.org/documents/release/Surf-H2O.download, https://iapws.org/documents/release/Rindex.download, https://iapws.org/documents/release/viscosity.download (pages https://iapws.org/technical-guidance/release/Surf-H2O, .../Rindex) ; Archived: http://web.archive.org/web/20261014015839/https://iapws.org/technical-guidance/release/Surf-H2O ; http://web.archive.org/web/20261117183336/https://iapws.org/technical-guidance/release/Rindex ; the PDFs themselves: none
- Read: 2026-11-28
- Licence: "Publication in whole or in part is allowed in all countries provided that attribution is given to the International Association for the Properties of Water and Steam" (front page of each release): free to republish with attribution
- Kept file (in `references/papers/`): iapws_R1-76-2014_surface_tension.pdf, iapws_R9-97_refractive_index.pdf, iapws_R12-08_viscosity.pdf
- Numbers:
  - Surface tension, equation: sigma = B tau^mu (1 + b tau), tau = 1 - T/Tc, Tc = 647.096 K, B = 235.8 mN/m, b = -0.625, mu = 1.256 (the extraction shows "b = 0.625" and lost the symbol mu; (my arithmetic) only b = -0.625 reproduces Table 1's 72.74 mN/m at 20 C). Table 1: 10 C 74.23 mN/m; 15 C 73.49; 20 C 72.74; 25 C 71.98; 30 C 71.19 (uncertainty 0.36-0.37 mN/m).
  - Refractive index, Table 3 at 0.1 MPa: at 0.589 um, 0 C: 1.334 344; at 0.226 50 um, 0 C: 1.394 527; at 1.013 98 um, 0 C: 1.326 135. Eq. (1) with coefficients a0-a7 (Table 1) gives n(lambda, T, rho) over 0.2-1.1 um.
  - Viscosity, Table 4: 298.15 K, 998 kg/m3: 889.735100 uPa s (Eq. 10 with mu_2 = 1); Sec. 2.5: reproduces the ISO value at 20 C (293.15 K), uncertainty 0.17% there.
- Settles: water's index (about 1.33) against air (1.00) and gum arabic (about 1.47) for wet-darker; viscosity and surface tension in Washburn, Stokes and the capillary flows.
- Proposed test: the model's water constants must agree with these at 20-25 C (eta 0.89 mPa s at 25 C, sigma 72.7 mN/m at 20 C, n 1.333); its wicking speed must scale as sqrt(sigma/eta) when either is changed.

#### colonygums_arabic
- Citation: Colony Gums, "Gum Arabic" product information sheet (undated).
- Address: https://colonygums.com/uploads/GUM_ARABIC.pdf ; Archived: http://web.archive.org/web/20251005155650/https://www.colonygums.com/uploads/GUM_ARABIC.pdf
- Read: 2026-11-28
- Licence: copyright, supplier's sheet; not kept
- Kept file (in `references/papers/`): none
- Numbers ("Viscosity", "Solubility", "Chemical Characteristics"): viscosity "increases slowly up to 25% concentration and exhibits Newtonian behavior. Above 25% gum concentration, the viscosity increases rapidly"; "A 30% solution is about 100 cps"; "At 40% and higher, Arabic is pseudo-plastic"; solutions "slightly acidic at pH 4-5. Maximum viscosity occurs between pH 4.6-7"; "solutions of over 50% concentrations may be prepared"; molecular weight "of the order of 250,000". Temperature and shear rate of the 100 cP figure not given.
- Settles: viscosity of the paint vehicle as it concentrates on drying: Newtonian and near water when dilute (a wash), about 100 times water at 30%, shear-thinning past 40% (a drying edge, the paint in the pan).
- Proposed test: a wash whose gum concentration rises past 25-30% as it dries must slow sharply (flow and backrun speeds fall with 1/eta), which bounds how late a backrun can form.

#### gumarabic_reviews
- Citation: (a) "Gum Arabic: A Commodity with Versatile Formulations and Applications", Nanomaterials 15, 290 (2025), DOI 10.3390/nano15040290, PMC11858195; (b) G. O. Phillips, S. Al-Assaf, "Characterization and Prediction of Emulsification Performance of Acacia Gums", LCGC International, 1 Feb 2008; (c) "Physicochemical Characterization of Exudate Gum from Neltuma flexuosa (ex Prosopis flexuosa)", Polymers 18, 1850 (2026), DOI 10.3390/polym18151850, PMC13467649. (Authors not read.)
- Address: (a) https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11858195/fullTextXML ; (b) https://www.chromatographyonline.com/view/characterization-and-prediction-emulsification-performance-acacia-gums ; (c) https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13467649/fullTextXML ; Archived: not checked
- Read: 2026-11-28
- Licence: (a) and (c) MDPI open access, in the Europe PMC open-access subset (the licence element was missing from the XML; MDPI publishes under CC-BY 4.0, not confirmed for these two); (b) copyright; none kept
- Kept file (in `references/papers/`): none
- Numbers:
  - (a) Table 2 "Physical properties of Gum Arabic" (citing its ref. [4]): density 1.35-1.49 g/mL; molecular weight about 250 kDa. Text: arabinogalactan about 88% of the weight (~300 kDa, under 1% protein), arabinogalactan-protein about 10% (~1500 kDa, about 10% protein), glycoprotein under 2%; shear-thinning in oil-recovery use.
  - (b) GPC-MALLS: "A value of 0.141 mL/g was used for the differential refractive index increment (dn/dc)", eluent 0.2 M NaCl, gum at 2 mg/mL.
  - (c) Introduction and Results: intrinsic viscosity of gum arabic 19.81 cm3/g (from its ref. [60], molecular weight 760,000 g/mol); Mark-Houwink constants for arabic gum k = 0.151, a = 0.52 (from its ref. [121]). It also prints "[eta] ~ 19 dL/g" for arabic gum, which contradicts 19.81 cm3/g by a factor 100; the cm3/g figure agrees with (my note) the low viscosity of gum solutions.
- Settles: the index of a gum solution, n = n_water + (dn/dc) c, about 1.333 + 0.141 x 0.3 = 1.375 for 0.3 g/mL (my arithmetic, linear extrapolation from a dilute increment), and the density of dry gum for the binder film; the dilute viscosity (eta_rel about 1 + [eta] c: 1.2 at 1% w/v, my arithmetic).
- Proposed test: the index of the medium around the pigment should move from 1.33 (wet wash) through about 1.37-1.40 (concentrated gum) to the dry gum's (about 1.47 per handprint) and to air (1.0) where the gum does not fill the pores, and the model's wet-to-dry lightening should follow from that contrast.

### Wet darker, dry lighter

#### handprint_dryingshift
- Citation: B. MacEvoy, "watercolor drying shifts", handprint.com (last revised 8 Jan 2005); and the "DRYING SHIFT", "Bl - BLOSSOMING", "Df - DIFFUSION" and "Granulation" sections of "what the ratings mean" (last revised 8 Jan 2015).
- Address: https://www.handprint.com/HP/WCL/cds.html and https://www.handprint.com/HP/WCL/pigmt8.html ; Archived: http://web.archive.org/web/20260304015456/https://handprint.com/HP/WCL/cds.html ; http://web.archive.org/web/20260818014501/https://www.handprint.com/HP/WCL/pigmt8.html
- Read: 2026-11-28
- Licence: copyright 2005 and 2015 Bruce MacEvoy; not kept
- Kept file (in `references/papers/`): none
- Numbers (real tube watercolours, measured; the only wet-against-dry measurement of watercolour found):
  - Method (cds.html): masstone swatches measured with a GretagMacbeth Spectrolino "at a satin wetness and again after they had dried for one hour", average of two samples; (pigmt8.html) 2 cm swatches on Arches CP paper, first reading "still glistening moist (about 30 to 60 seconds after application)", second "4 or more hours after" (the two pages differ on the drying time). Shifts are dry minus wet in CIELAB: dL (minus = darker), dC (minus = duller), dh in degrees, and the total.
  - Average over 75 paints: dL = 2.3, dC = -10.7, dh = -2.9, total 12.9 (27%). "over one third of the pigments listed here actually darkened"; "loss of chroma is the main cause of the drying shift".
  - Selected rows (dL, dC, dh, total): PB15:3 phthalo blue GS (W&N) 6.9, -10.4, -5.3, 12.7; PB15:1 phthalo blue RS 9.2, -14.7, -5.9, 17.6; PB27 prussian blue 11.4, -9.3, -11.3, 15.2; PB28 cobalt blue 6.5, -10.7, -2.9, 12.7; PB29 French ultramarine 7.3, -15.8, -4.1, 17.7; PB36 cerulean blue 0.0, -2.3, 0.0, 2.3; PBk7 lamp black 16.2, 1.5, 32.1, 16.2; PBk9 ivory black 13.3, 1.5, 7.5, 13.5; PBr7 burnt sienna (W&N, light) 0.0, -14.5, -2.9, 14.6; burnt sienna (Daniel Smith, dark) 3.7, -12.7, -4.2, 13.4; PG17 chromium oxide green -6.2, -12.1, 4.9, 13.6; PG7 phthalo green BS 6.4, -10.1, -2.1, 12.8; PR209 quinacridone red 0.6, -11.0, -3.9, 11.4; PV19 quinacridone rose 0.8, -9.7, -1.8, 9.9; PR122 quinacridone magenta 4.6, -12.0, -5.1, 13.2; PY35 cadmium yellow -4.5, -17.3, -7.5, 19.2; PY43 yellow ochre -0.3, -5.6, -1.6, 6.0; PY154 benzimidazolone yellow -0.8, -2.3, -1.3, 3.6. (Viridian is not in the table.)
  - Explanation given (cds.html): wet, the pigment sits in water of similar index and little white light is scattered; dry, it is in contact with air, "which has a much lower refractive index than pigment", so more white light is scattered.
  - Ratings (pigmt8.html): Diffusion (wet in wet) 0 = imperceptible to 4 = 1 inch or more ("Greater diffusion is caused by a smaller size and lower specific gravity" of the particles; "rapid, shooting diffusion" in cadmiums, chromium oxide, ultramarine, iron oxides is caused by a dispersant such as ox gall); Blossoming measured on a layer "allowed to dry until nonreflective, then rewetted with clear water"; Granulation 0 (liquid) to 4 (coarse).
- Settles: wet-darker / dries-lighter: in watercolour, the dominant drying change is a loss of chroma (about -11 C*), the lightness change is small on average (+2.3 L*) and of either sign: dark, fine, transparent pigments (phthalos, prussian blue, blacks) lighten by 7-16 L*, while yellows and cadmiums darken by up to 6 L*; coarse cerulean barely changes.
- Proposed test: painted as masstone on a white paper and rendered wet (pores filled with water, index 1.33) and dry (air, with the gum's film), the model's dry-minus-wet shift should average a chroma loss of order 10 C* with a lightness change of a few L*, larger lightening for fine dark pigments (phthalo blue +7 to +9 L*) than for coarse ones (cerulean about 0), and darkening for light yellows.

### Settling

#### openstax_stokes
- Citation: OpenStax, University Physics Volume 1, Sec. 6.4 "Drag Force and Terminal Speed" (Rice University).
- Address: https://openstax.org/books/university-physics-volume-1/pages/6-4-drag-force-and-terminal-speed ; Archived: http://web.archive.org/web/20261104234140/https://openstax.org/books/university-physics-volume-1/pages/6-4-drag-force-and-terminal-speed
- Read: 2026-11-28
- Licence: CC BY-NC-SA 4.0 (non-commercial; the page also forbids use for training language models without permission); not kept (web page, not a PDF)
- Kept file (in `references/papers/`): none
- Numbers: Eq. (6.6), Stokes's law F_s = 6 pi r eta v for a sphere of radius r in a fluid of viscosity eta at speed v, for objects "very small", "going very slow, or ... in a denser medium than air"; terminal speed with linear drag v_T = mg/b; bacteria of about 1 um have terminal speeds around 2 um/s, lake sediment around 5 um/s. (The page gives no Reynolds-number bound.)
- Settles: settling speed of pigment in a wash: (my note) balancing 6 pi r eta v against the buoyant weight (4/3) pi r^3 (rho_p - rho_w) g gives v = 2 r^2 (rho_p - rho_w) g / (9 eta), the form to use with the sizes and densities of handprint_attributes and handbook_mineralogy.
- Proposed test: in still water at 20 C, a pigment sphere must settle at v = 2 r^2 (rho_p - rho_w) g / (9 eta): (my arithmetic, eta = 1.0 mPa s, handprint's sizes taken as diameters, r = d/2) about 41 um/s for a 5 um cobalt blue grain (rho 4.0), 0.71 um/s for 1 um ultramarine GS (2.3), 0.0033 um/s for 0.1 um phthalocyanine (1.6); so through a wash 0.1 mm deep, cobalt settles in about 2 s, ultramarine in about 2 minutes, and phthalo not before the wash dries. Settling against Brownian motion should then decide granulation.

### Coffee ring: what changes it

#### patil2019
- Citation: N. D. Patil, R. Bhardwaj, "Recent Developments on Colloidal Deposits Obtained by Evaporation of Sessile Droplets on a Solid Surface", J. Indian Inst. Sci. (2019), DOI 10.1007/s41745-019-0105-9; arXiv:1904.06413.
- Address: https://arxiv.org/pdf/1904.06413 ; Archived: http://web.archive.org/web/20250317104017/https://arxiv.org/abs/1904.06413
- Read: 2026-11-28
- Licence: arXiv non-exclusive distribution licence; published version copyright; not kept
- Kept file (in `references/papers/`): none
- Numbers (a review; the numbers are those of the studies it reports):
  - Sec. 2: constant-contact-radius evaporation (pinned) gives a ring, constant-contact-angle (depinned) an inner deposit, stick-slip multiple rings; Sangani et al. studied particles of 1 to 70 um and gave a pinning criterion from the surface-tension force on a particle at the line.
  - Sec. 3: thermal Marangoni flow (from cooling by evaporation or a heated substrate) reverses the outward flow and moves deposit to the centre (Hu and Larson); e.g. Li et al., glass of 24-30 deg, 2.5 uL drops, 0.25% v/v 100 nm polystyrene, substrate 30 to 80 C: ring to "coffee eye".
  - Sec. 4: particle size: Perelaer et al. silica 0.33-5 um at 1% w/w: rings for small particles on low-angle substrates, inner or uniform deposits for large; Weon and Je 0.1 and 1.0 um on glass at 15 deg: small particles ring, large do not; Ryu et al. 100 nm to 10 um: rings for small colloids, uniform for large.
  - Sec. 6: ring when Marangoni and DLVO (particle-substrate attraction) velocities are negligible against the radial velocity, central bump when Marangoni dominates, uniform when particle-substrate attraction dominates (Bhardwaj et al.); surfactant (SDS) makes Marangoni eddies (Still et al., 1.33 um particles, 0.5% w/w); ellipsoids give uniform deposits (Yunker et al.).
- Settles: what suppresses edge darkening: depinning, Marangoni flow, large particles, particle-substrate attraction, particle shape.
- Proposed test: in the model, coarse heavy pigment (several um) must darken a dried edge less than fine pigment does at equal load; a wash that can recede (unpinned edge on a sized, non-absorbing ground) must leave a central or multiple-ring deposit instead of one rim.

#### seo2017
- Citation: C. Seo, D. Jang, J. Chae, S. Shin, "Altering the coffee-ring effect by adding a surfactant-like viscous polymer solution", Scientific Reports 7, 500 (2017). DOI 10.1038/s41598-017-00497-x
- Address: https://www.nature.com/articles/s41598-017-00497-x (read as full text from Europe PMC, PMC5428518) ; Archived: http://web.archive.org/web/20250320191138/https://www.nature.com/articles/s41598-017-00497-x
- Read: 2026-11-28
- Licence: Scientific Reports, open access (CC-BY 4.0 is the journal's licence; the licence element was missing from the XML read)
- Kept file (in `references/papers/`): none (PDF not fetched: the publisher's site redirects automated requests to a login)
- Numbers:
  - Methods: drops of 1 +- 0.05 uL on glass, 23 +- 1 C, 20 +- 3% RH; PEG of molecular weight 35,000 at 0.1-5.0 wt%; polystyrene particles at 0.5% v/v.
  - Results, Fig. 2: with 0.5 wt% PEG, the polymer at the edge reached 13.1 wt% by t = 10 s (t/t_e = 0.036; total evaporation t_e about 280 s); viscosity 1.08 cP in the bulk and 29.15 cP at the edge; the surface tension fell most near the edge, driving a Marangoni vortex.
  - Fig. 4: the pinned contact angle fell from 31.4 deg; first receding at 26.1 deg, then at 18.1-20.8 deg: multiple rings by repeated pinning and receding.
  - Fig. 5: outward radial velocity in pure water 4.8 um/s on average; Marangoni velocity at t/t_e = 0.43: 390 um/s with SDS, 72 um/s with PEG; vortex length up to 160 um (SDS, l/R = 0.16) and 33 um (PEG).
  - Uniformity (std. dev. of deposit intensity): water 14.61, SDS 12.44, PEG 9.34.
  - Introduction: Cui et al. showed that a polymer raising the viscosity resists the outward flow, so fewer spheres reach the edge.
- Settles: what a dissolved, surface-active binder (gum arabic is one: an arabinogalactan-protein) does at a drying edge: it concentrates there about 25-fold in seconds, raises the local viscosity about 27-fold, and drives an inward Marangoni flow, giving multiple rings and a more even deposit.
- Proposed test: if the model carries the gum as a solute, it must concentrate at a drying edge (several-fold within the first few per cent of the drying time) and its viscosity there must slow the outward flow; turning the binder off must sharpen the edge darkening.

### Ink on absorbent paper

#### wu2016xuan
- Citation: S. Wu, X. Wu, P. K. Chu, "Ink Dispersion on Qianlong Xuan Paper with Improved Ink Expression", Journal of Materials Science & Technology 32, 182-188 (2016). DOI 10.1016/j.jmst.2015.12.014 (from Crossref)
- Address: http://www.cityu.edu.hk/phy/appkchu/Publications/2016/16.19.pdf (co-author's publication list, published version) ; Archived: none (journal page https://www.jmst.org/article/2016/1005-0302/1005-0302-32-2-182.html: none)
- Read: 2026-11-28
- Licence: "Copyright 2015, The editorial office of Journal of Materials Science & Technology. Published by Elsevier"; author's page copy; not kept
- Kept file (in `references/papers/`): none
- Numbers:
  - Sec. 2.2/3.1: Chinese ink drops of 50 uL let fall from 1 mm (Weber number of order 1, Eq. (1), "no splashing") spread over 24.5, 22.7 and 19.6 cm2 on Qianlong, Bamboo and Jingpi xuan papers.
  - Sec. 3.2, Fig. 2: water contact angle (4 uL drop, 0.02 s after impact, 200 positions per paper): 36.8 deg Qianlong, 50.1 deg Bamboo, 60.6 deg Jingpi; Fig. 4: the angle falls fastest on the paper with the smallest initial angle.
  - Sec. 3.4, Eqs. (2)-(4): Poiseuille flow in capillaries plus Laplace pressure 2 gamma cos(theta)/r gives the classical Washburn-Lucas law; "a small contact angle and a large effective radius are beneficial to transverse wicking".
  - Sec. 3.5: paper densities 463, 356, 429 kg/m3 (Qianlong, Bamboo, Jingpi); ink is "a diluted mixture consisting of water, soot, and glue"; soot "spherical primary carbon particles about 10 to 150 nm"; "water flows slowly carrying pigments with it through the fibers while pigment diffusion itself can be neglected"; the roughness of the advancing front has a crossover length scaling as d^1/2 with the separation d of the fibres (their ref. 25); a denser, more connected fibre web gives a smoother edge, a sparse one an irregular edge.
- Settles: feathering and the spread of ink on unsized paper: area spread per volume (50 uL over about 20-25 cm2, i.e. (my arithmetic) 20-25 um of liquid per unit area of thin paper), the smoothness of the wicked edge against fibre network density, pigment carried with the water rather than diffusing.
- Proposed test: on an unsized, thin absorbent paper preset (density about 0.4-0.46 g/cm3), a 50 uL drop of ink should wick to about 20-25 cm2 and its edge roughness should fall as the fibre network densifies; ink pigment must move only with the water (no diffusion of its own once the paper is wet through).

### Not found or not verified

- Washburn 1921 (Phys. Rev. 17, 273), the original of the sqrt(t) law: no open copy reached (APS refused automated access; the Zenodo record found is Gardner's reply, Phys. Rev. 18, 206, CC0, not Washburn's paper). The law itself is taken from walji2016 Eq. (1), krainer2018 Eqn (1) and wu2016xuan Eqs. (2)-(4).
- A measured wicking coefficient for sized paper, and for watercolour or printing paper in particular: not found. krainer2018 shows the sized paper is far slower but its numbers are in figures and the ESI; St Cuthberts Mill's page on absorbency (https://www.stcuthbertsmill.com/advice-centre/?id=1016) describes the Cobb test (100 mL, 10 cm2, 1 minute) but gives no values. Indirect: on Fabriano 300 g/m2 watercolour paper a 50 uL drop sits and evaporates over about 2500 s (gonzalez2019), so it does not soak in quickly.
- Anisotropy measured on watercolour paper: not found; only Whatman 17 CHR (walji2016, 30% faster along the machine direction). A search summary quoted 5-15% (Lindsay) and MD/CD permeability ratios of 1-2 from the papermaking literature (academia.edu and Georgia Tech repository copies); not read, so not used.
- Yunker et al., Nature 476, 308 (2011) (ellipsoids suppress the ring) and Hu & Larson, J. Phys. Chem. B 110, 7090 (2006) (Marangoni reverses the ring): no author's copy found (one copy is on a course website, not the authors'); their results are taken only as reported by patil2019.
- CAMEO (MFA Boston) pigment and gum arabic pages: refused (Cloudflare block, HTTP 403), and no Wayback copy of the ultramarine page. National Gallery of Art "Artists' Pigments" volumes (free PDFs): the NGA pages refused automated access (403), and the PDFs are hundreds of MB. Pigment Compendium (Eastaugh et al.): not openly available. ColourLex pages read have no physical data. Natural Pigments' technical pages and its "Measuring Watercolor Granulation" article (a Granulation Index) refused (403).
- Densities measured for synthetic watercolour pigments (cobalt blue CoAl2O4, cerulean, phthalocyanine, quinacridone, carbon black): only handprint's representative values; no primary datasheet read. Measured particle-size distributions for watercolour pigments: only gonzalez2019 Table I (four Winsor & Newton pigments, DLS).
- Refractive index of dry gum arabic: only handprint's 1.47 (a secondary compilation); no measurement found. Refractive index of gum arabic solutions: only the dilute increment dn/dc = 0.141 mL/g (gumarabic_reviews b); a measured n against concentration up to paint concentrations was not found (MDPI's Neltuma gum paper says only that n rises with concentration, for that gum).
- Viscosity and surface tension of gum arabic solutions at paint concentrations: no open primary measurement found. The supplier's "30% about 100 cP" (colonygums_arabic) and the intrinsic viscosity 19.81 cm3/g (gumarabic_reviews c) are all there is here. Search summaries mentioned 125-110 mPa s at 30% and 20 C (Gomez-Diaz et al. 2008) and surface tension unchanged between 20 and 40 wt%; neither was read in a source, so not used. The University of Khartoum Engineering Journal paper on Acacia senegal viscosity returned 404.
- Surface tension of watercolour paint (with ox gall or other wetting agents): not found.
- Evaporation of a water film measured at controlled humidity and air speed: only the Engineering ToolBox empirical formula (no primary source cited there) and the diffusion-limited drop rate of deegan2000. Hanssen's AIVC paper on pool evaporation (https://www.aivc.org/sites/default/files/airbase_4058.pdf) is a poor scan whose tables could not be read; the Western Michigan University dissertation on still-surface evaporation did not download. A measured drying time of a full wash (not a drop) was not found.
- Backruns (blooms) measured physically: no study found beyond gonzalez2019's dendrites in the damp stage and handprint's blossoming test (a rating, not a measurement). Granulation measured: only handprint's 0-4 rating.
- Wet-against-dry measurements other than handprint's: none found in the peer-reviewed literature. Note that handprint contradicts itself: pigmt3.html says "many watercolors become lighter and less saturated as they dry", while its own measurements (cds.html, pigmt8.html) show chroma loss as the main shift and over a third of the paints darkening.
- Not checked in the Wayback Machine: the webexhibits pages other than ultramarine, eskolaite's sheet, the IAPWS PDF downloads (their pages are archived), the gum arabic review articles.

## Published ratings of watercolour (and gouache, ink) paints: granulation, staining, transparency

Read 2026-11-28. Every value below was read on the page or chart named in its entry. The HTML pages (handprint) were read through a fetch tool that turns the page into text. The PDF charts were opened from the tool's temporary copy only to read them: the transparency and staining marks are glyphs, not text, so the pages were rendered and the marks read by eye. No copy was kept (see "Kept file" in each entry).

### Scales

- **HP** = handprint (MacEvoy), per paint, tested 2004 to 2015. Tr 0 (very opaque) to 4 (transparent). St 0 (nonstaining) to 4 (heavily staining). Gr 0 (liquid texture) to 4 (granular). The cell gives the **median [min-max] over the brands he lists** for that pigment, with n brands, then the W&N or DS paint's own Tr/St/Gr in brackets where that paint is also in another column.
- **WN** = Winsor & Newton Professional Watercolour chart 2022. Transparency T (transparent), ST (semi-transparent), SO (semi-opaque), O (opaque); "St" = staining marked; "G" = granulating marked; "-" = not marked. The chart prints no pigment: the pigment is from handprint's listing of the same W&N paint, or "pigment?" where it was not read.
- **DS** = Daniel Smith Extra Fine chart, Rev01-19 (2019). Staining 1 (non-staining), 2 (low), 3 (medium), 4 (high). Granulation N/Y ("Yes, in varying degrees"). Transparency T, ST (semi-transparent), O.
- **SCH** = Schmincke Horadam Aquarell chart (Nuancier 2024). Transparency T, ST, SO, O. Staining: ns (non-staining, "leicht vom Papier anzulösen"), ss (semi-staining), s (staining, "schwer vom Papier anzulösen"). "G" = granulating.
- **WN-G** = W&N Designers Gouache chart 2007, opacity only (same four marks as WN; "BL" = colour may bleed).
- **LQ-ink** = Liquitex Professional Acrylic Ink chart 2008, opacity only: O opaque, TL translucent (semi-opaque), TP transparent.

### Table: pigment x source

| Pigment | HP Tr | HP St | HP Gr | WN (paint: T/St/G) | DS (paint: St, G, T) | SCH (paint: T, St, G) | WN-G gouache | LQ-ink |
|---|---|---|---|---|---|---|---|---|
| PB29 ultramarine | 3 [1-4] n18 (WN Fr. ultramarine 3) | 2 [1-3] (WN 1; DS Fr. ultra 3) | 2 [1-4] (WN 3; DS Fr. ultra 2) | French Ultramarine 263: T, -, G; Ultramarine (GS) 667: T, -, - | Ultramarine Blue: 3, Y, T; French Ultramarine: 3, Y, T | 493 French ultramarine: T, ns, G; 494 Ultramarine finest: ST, ss, - | Ultramarine 660: O | (no ultramarine read) |
| PB28 cobalt blue | 2 [1-4] n11 (WN 4) | 2 [1-4] (WN 1; DS 2) | 1 [1-3] (WN 3; DS 1) | Cobalt Blue 178: ST, -, G | Cobalt Blue: 2, Y, ST | 487 Cobalt blue light: ST, ss, - | Cobalt Blue 178: O | - |
| PB35 cerulean | 2 [1-3] n6 | 1.5 [0-3] | 2 [1-3] | Cerulean Blue 137: SO, -, G (pigment per handprint: W&N cerulean blue is PB35) | Cerulean Blue (PB35): 1, Y, ST | 483 Cobalt azure (PB35): ST, ns, G | Cerulean Blue 137: O | Cerulean Blue Hue: O (hue, pigment not read) |
| PB36 cerulean chromium | 1.5 [0-3] n12 | 3 [1-4] (DS 3) | 1 [1-2] (DS 1) | Cerulean Blue (Red Shade) 140: O, -, G (handprint files this paint under PB35) | Cerulean Blue, Chromium (PB36): 2, Y, ST | 499 Cobalt cerulean (PB36): SO, ss, G | - | - |
| PB15 phthalo blue | 4 [3-4] n17 | 4 [3-4] | 0 [0-1] | Winsor Blue (RS) 709 (PB15:1): T, St, -; Winsor Blue (GS) 707 (PB15:3): T, St, - | Phthalo Blue GS (PB15:3): 4, N, T; Phthalo Blue RS (PB15:6): 4, N, T | 484 Phthalo blue (PB15:1): ST, ss, -; 477 Phthalo sapphire (PB15:6): ST, s, - | Winsor Blue 706: O; Phthalo Blue 514: O | Phthalocyanine Blue (GS): TP |
| PG7 phthalo green | 4 [3-4] n9 | 4 [3-4] | 0 [0-1] | Winsor Green (BS) 719: T, St, - | Phthalo Green (BS): 4, N, T | 519 Phthalo green: ST, **ns**, - | Winsor Green 720: O | Phthalocyanine Green (BS): TP |
| PG18 viridian | 4 [3-4] n10 | 1 [1-3] (WN 3; DS 2) | 2 [0-3] (WN 2; DS 3) | Viridian 692: T, -, G | Viridian: 1, Y, T | 513 Viridian: ST, ns, G | Viridian 692: **T** | - |
| PV19 quinacridone rose/violet | not read (page would not load) | not read | not read | Permanent Rose 502: T, St, -; Quinacridone Red 548: T, -, - (pigments not printed) | Quinacridone Rose (PV19): 3, N, T; Quinacridone Red (PV19): 3, N, T | 351 Ruby red (PV19): ST, ss, -; 353 Perm. carmine (PV19): SO, ss, -; 368 Quin. violet (PV19): SO, ss, - | Permanent Rose 502: O | - |
| PR122 quinacridone magenta | not read | not read | not read | Quinacridone Magenta 545: T, -, - (pigment not printed) | Quinacridone Lilac (PR122): 3, N, T | 367 Purple magenta (PR122): T, ss, - | Quinacridone Magenta 550: not read | Quinacridone Magenta: TP (pigment not read) |
| PR83 alizarin crimson | 4 [3-4] n8 (WN 4; DS 4) | 3 [2-4] (WN 3; DS 3) | 0 [0-1] | Alizarin Crimson 004: T, St, - | Alizarin Crimson (PR83): 3, N, T | 357 Alizarin crimson (PR83:1): T, ss, - | Alizarin Crimson 004: **SO** | - |
| PR108 cadmium red | 1 [0-2] n25 (WN cad red 1) | 4 [2-4] (WN 3) | 1 [0-1] (WN 0) | Cadmium Red 094: O, St, G; Cadmium Red Deep 097: O, -, G | (only hues in this chart) | 349 Cad. red light: O, ss, -; 347 medium: O, s, -; 350 deep: O, ss, - | (cadmium red row not read) | - |
| PY35 cadmium yellow | 2 [1-2] n19 (WN lemon 1, pale 2) | 3 [2-4] (WN 4, 4) | 0 [0-1] | Cadmium Lemon 086: O, St, -; Cadmium Yellow Pale 118: O, St, -; Cadmium Yellow 108: O, -, - | (only hues) | 223 lemon, 224 light, 225 medium: SO, s, - | Cadmium Lemon 086: O; Cad. Yellow Pale 118: O; Cad. Yellow 108: O | Cadmium Yellow Light Hue: TL (hue) |
| PY150 nickel azo yellow | 3 [3-4] n3 (WN 4; DS 3) | 2 [2-3] (WN 3; DS 2) | 1 [1-1] (WN 1; DS 1) | Transparent Yellow 653: T, St, - | Nickel Azo Yellow: 2, N, T | 209 Transparent yellow: T, ss, - | - | - |
| PY153 | 3 [3-4] n5 | 1 [0-4] | 0 [0-2] | (W&N New Gamboge is now 267, a mixture per handprint; not used) | (DS New Gamboge is now PY97+PY110; not used) | (212 is PY153+PY155; not used) | - | - |
| PR101 red iron oxide (opaque: venetian / indian / light red) | 1 [0-4] n15 (WN venetian 0, indian 0) | 3 [2-4] (WN 4, 4) | 0 [0-2] | Venetian Red 678: O, St, -; Indian Red 317: O, -, -; Light Red 362: SO, -, - | Indian Red: 3, Y, O; Venetian Red: 3, Y, O | 649 English Venetian red: O, s, - | Venetian Red 678: O | Red Oxide: O (pigment not read) |
| PR101 transparent red oxide | DS 4/2/2 (one paint) | | | - | Transparent Red Oxide: 1, Y, T | 653 Transparent sienna: T, ss, - | - | Transparent Burnt Sienna: TP |
| PBr7 burnt sienna | 2 [1-3] n11 (DS 1) | 3 [2-3] (DS 3) | 1 [0-2] (DS 1) | Burnt Sienna 074: T, -, - (pigment?) | Burnt Sienna (PBr7): 1, Y, ST | (661 is PR101+PBk9: SO, s, -) | - | - |
| PBr7 burnt umber | 2 [1-4] n7 (DS 1) | 3 [2-4] (DS 3) | 0 [0-2] (DS 0) | Burnt Umber 076: T, -, - (pigment?) | Burnt Umber (PBr7): 2, Y, ST | 668 Burnt umber (PBr7): SO, ss, - | Burnt Umber 076: O | Transparent Burnt Umber: TP |
| PBr7 raw umber | 3 [2-4] n9 (WN 3; DS 2) | 2 [1-4] (WN 2; DS 3) | 1 [0-3] (WN 3; DS 1) | Raw Umber 554: T, -, G | Raw Umber (PBr7): 2, Y, ST | 665 Green umber (PBr7): ST, ns, G (667 raw umber is PY43) | Raw Umber 554: O | - |
| PW6 titanium white | 2 [1-2] n5 (WN 2) | 2 [2-2] | 0 [0-0] | Titanium White 644: O, -, - | Titanium White: 1, N, ST | 101 Titanium opaque white: O, ss, - | Permanent White 512: O (pigment?) | Titanium White: O |
| PW4 Chinese (zinc) white | 1 [1-1] n5 (WN 1; DS 1) | 2 [2-2] | 0 [0-0] | Chinese White 150: SO, -, - | Chinese White: 1, N, ST | 102 Perm. Chinese white: ST, ss, - | Zinc White 748: O | - |
| PBk6 lamp black | 0.5 [0-1] n2 (DS 0) | 4 [4-4] (DS 4) | 0.5 [0-1] | Lamp Black 337: O, -, - (pigment?) | Lamp Black (PBk6): 4, N, O | 781 Lamp black (PBk6): O, ss, - | Lamp Black 337: O | - |
| PBk7 carbon black | 3 [1-3] n4 | 2 [2-4] | 0 [0-1] | - | - | 786 Anthracite (PBk7): O, s, - | - | Carbon Black: O (pigment not read) |
| PBk9 ivory black | 3 [2-3] n5 (WN 3; DS 2) | 3 [3-4] (WN 4; DS 3) | 1 [1-2] (WN 1; DS 2) | Ivory Black 331: O, -, G | Ivory Black: 2, Y, ST | 780 Ivory black: SO, ss, - | Ivory Black 331: O | - |
| PBk11 Mars black | 1.5 [1-2] n2 (WN 1; DS 2) | 3.5 [3-4] (WN 4; DS 3) | 2 [1-3] (WN 1; DS 3) | Mars Black 386: O, -, G | Lunar Black: 2, Y, **T** | 791 Iron oxide black: O, ss, G | - | - |

#### Where the sources disagree

- **Staining of opaque inorganics.** Handprint's staining test (dilute swatch, five wipes with a wet swab) gives cadmiums St 3-4 (PR108 median 4, PY35 median 3) and opaque red oxides 3-4. W&N marks Cadmium Lemon, Cadmium Yellow Pale, Cadmium Red and Venetian Red as staining but not Cadmium Yellow 108, Cadmium Red Deep or Indian Red; Schmincke has cadmium red light and deep only semi-staining, medium staining. The makers' "staining" is closer to "hard to lift"; handprint counts any residue, discoloration included. A simulation must choose which one it is held to.
- **PG7.** Handprint 4 (heavily staining), DS 4, W&N "St"; Schmincke 519 Phthalogrün is marked **non-staining**. Schmincke's PB15:1 is only semi-staining where every other source has PB15 near the top. Schmincke's staining scale sits lower than the others' throughout.
- **PB28 granulation.** W&N marks Cobalt Blue G and handprint gives the W&N paint Gr 3, but the median over 11 brands is 1 and Schmincke 487 has no G. DS says Y ("in varying degrees").
- **PB29.** Granulation depends on the grade: W&N French Ultramarine G but Ultramarine (Green Shade) not; Schmincke 493 French ultramarine G, non-staining, but 494 Ultramarine finest no G, semi-staining. Handprint's Gr runs from 1 to 4 across 18 brands. DS rates both of its PB29s staining 3; handprint's median is 2, and W&N marks neither as staining.
- **Whites.** Titanium white: O at W&N and Schmincke, ST at DS, Tr 1-2 at handprint. Chinese white: SO at W&N, ST at Schmincke and DS, but handprint Tr 1 ("opaque"), lower than his titanium white (Tr 2). He notes PW4 "became brighter and more opaque" in sunlight.
- **PBk11.** DS chart 2019 marks Lunar Black transparent; handprint gave the same paint Tr 2 (2015); W&N and Schmincke Mars blacks are opaque.
- **Burnt sienna.** W&N Burnt Sienna is transparent on the chart; DS (PBr7) semi-transparent; Schmincke's burnt sienna is PR101+PBk9, semi-opaque and staining. Handprint warns that "burnt sienna" is natural PBr7 in some lines and synthetic PR101 in others, so the name settles nothing.
- **Gouache.** In W&N Designers Gouache nearly every colour is opaque, including the phthalos and cobalt; only Viridian is transparent and Alizarin Crimson semi-opaque. The order in gouache is not the watercolour order.

### Entries

#### handprint-key
- Citation: Bruce MacEvoy, "handprint : what the ratings mean" (key to the paint ratings), last revised 08.I.2015.
- Address: https://www.handprint.com/HP/WCL/pigmt8.html ; Archived: http://web.archive.org/web/20260818014501/https://www.handprint.com/HP/WCL/pigmt8.html (API status 202)
- Read: 2026-11-28
- Licence: © 2015 Bruce MacEvoy, all rights reserved. Cited only.
- Kept file: none
- Numbers: How each rating is measured. Transparency: a stroke of paint diluted to about 1:3 with water over two closely spaced black lines, with a third line drawn across it once dry; 4 = "no visible masking", 0 = "extensive or complete masking". Staining: a stroke of the same 1:3 dilution, dried, then "firmly wiping the paint five times with a wet cotton swab and blotting the paint dry"; 4 = "heavy and indelible staining of paper", 0 = "no stain, lifts completely". Granulation: "the visible or tactile graininess, clumping or texture of the paint" in a dilute wash; 4 = "coarse granulation", 0 = "no texture in any application". Blossom: a moderately diluted layer dried "until nonreflective, then rewetted with clear water"; 0 to 4. Diffusion: paint laid on premoistened paper, movement beyond the brush mark; 4 = "diffusion of 1" or more", 0 = "imperceptible movement". Value range VR = 97 − J (CIECAM J, measured with a spectrophotometer in the masstone).
- Settles: what each handprint number means operationally. Each test can be repeated on a simulated swatch: lines under a 1:3 wash, five wet wipes, rewetting a dry layer, a drop on wet paper.
- Proposed test: build the five handprint tests as simulation scenarios (a line under a wash for Tr, a 5-wipe lift for St, a dilute wash's texture for Gr, a rewet for Bl, a drop on wet paper for Df), score each on 0-4 by a fixed measurement, and compare the ranks with the table (Spearman across pigments).

#### handprint-material
- Citation: Bruce MacEvoy, "handprint : the material attributes of paints", last revised 08.I.2015.
- Address: https://www.handprint.com/HP/WCL/pigmt3.html ; Archived: http://web.archive.org/web/20260818014606/https://www.handprint.com/HP/WCL/pigmt3.html
- Read: 2026-11-28
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: specific gravity, water = 1.0: phthalocyanine blues about 1.6, ultramarine about 2.3, viridian about 3.5, cobalt blue about 4.0, cadmium reds about 5.0, zinc white about 5.5. Particle size: pigments typically 0.1 to 50 µm, carbon black about 0.05 µm. Refractive index: pigments 1.0 to 2.8, gum arabic about 1.5, titanium white anatase about 2.5 and rutile about 2.7; hiding is cloudy near an RI ratio of 1.33 and almost fully opaque above 1.5. Tinting strength: phthalo blue about 40 times ultramarine. Pigment load from under 10% (some phthalos, quinacridones) to 50% or more (cadmium oranges and reds). Staining "is not an inherent property of a pigment": small particles enter the fibres, much gum arabic holds paint at the surface, heavier sizing reduces staining. Viridian "always redissolve[s] slowly and leave[s] grainy clumps".
- Settles: physical parameters (density, particle size, RI) behind granulation, staining and hiding, which a simulation can take as inputs rather than fitting.
- Proposed test: with pigment density and particle size from this page as inputs, and no per-pigment tuning, the simulated granulation should order PB28/PG18 above PB29 above PB15/PG7 (handprint medians 1-2 vs 0), and the simulated lift should leave PB15 and PG7 behind more than PG18 (median St 4 vs 1).

#### handprint-blue
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (blue pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/waterb.html ; Archived: http://web.archive.org/web/20261020191647/https://www.handprint.com/HP/WCL/waterb.html
- Read: 2026-11-28
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: per-paint rows Tr St VR Gr Bl Df HA HS Lf. Examples: W&N french ultramarine 3 1 64 3 3 1; DS ultramarine blue 4 3 66 1 3 2; Holbein ultramarine deep 4 1 64 4 2 1; W&N cobalt blue 4 1 44 3 3 2; DS cobalt blue 3 2 51 1 3 2; DS cerulean blue (PB36) 3 3 51 1 3 4; Holbein cerulean (PB35) 1 0 46 3 3 1; W&N winsor blue RS (PB15:1) 3 3 64 0 3 2; DS phthalo blue (PB15:3) 4 4 65 1 2 1. Summaries: PB29 "a very lightfast, semitransparent, staining, very dark valued, intense violet blue pigment"; PB28 "... semitransparent, moderately staining ..."; PB35/PB36 "very lightfast, semiopaque, moderately staining, granulating ..."; PB15 "a lightfast, transparent, strongly staining, very dark valued ...". Medians in the table were computed from all single-pigment rows read here (18 PB29, 11 PB28, 6 PB35, 12 PB36, 17 PB15).
- Settles: blue order. Transparency: PB15 > PB29 > PB28 ≈ PB35 > PB36. Staining: PB15 high, the others middling. Granulation: PB29, PB28 and PB35 vary by brand from 1 to 4, PB15 is 0.
- Proposed test: a dilute PB15 wash on rough paper gives a texture variance near that of the bare paper (Gr 0), and a PB29 or PB28 wash clearly more; after a simulated 5-wipe lift, PB15 keeps more of its colour than PB28.

#### handprint-green
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (green pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/waterg.html ; Archived: http://web.archive.org/web/20261026143027/https://www.handprint.com/HP/WCL/waterg.html
- Read: 2026-11-28 (the fetch returned an empty page twice; a third fetch with a query string returned the text)
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: PG7 rows, e.g. W&N winsor green BS 3 4 53 0 1 1; DS phthalo green BS 3 4 59 0 2 1; M. Graham 3 4 64 1 2 2. PG18 rows, e.g. W&N viridian 3 3 44 2 3 2; DS viridian 4 2 38 3 3 2; M. Graham 4 2 39 3 1 1; Rembrandt 4 1 40 3 2 2. Summaries: PG7 "a very lightfast, transparent, heavily staining, dark valued, moderately dull blue green pigment"; PG18 "a very lightfast, transparent, moderately staining, moderately dark valued, moderately dull blue green pigment".
- Settles: two pigments of the same hue (hue angles 174-184) and transparency (Tr 3-4) that differ in staining (4 vs 1) and granulation (0 vs 2-3). The cleanest pair for testing staining and granulation apart from colour.
- Proposed test: PG7 and PG18 laid with the same dilution and lifted the same way: the PG18 swatch lifts to near the paper and granulates; the PG7 swatch stays and is smooth.

#### handprint-yellow
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (yellow pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/watery.html ; Archived: http://web.archive.org/web/20261020132853/https://www.handprint.com/HP/WCL/watery.html
- Read: 2026-11-28
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: PY35, e.g. W&N cadmium lemon 1 4 7 0 1 2; W&N cadmium yellow pale 2 4 12 0 2 1; M. Graham cadmium yellow light 1 4 7 0 1 3 (19 rows). PY150: DS nickel azo yellow 3 2 25 1 3 1; W&N transparent yellow 4 3 22 1 4 2; Schmincke translucent yellow 3 2 21 1 2 2. PY153: W&N new gamboge 3 4 14 0 2 2; DS new gamboge 3 1 22 0 4 1; Utrecht indian yellow 4 0 17 0 3 2.
- Settles: an opaque yellow against a transparent yellow of similar value (PY35 Tr 1-2 vs PY150 Tr 3-4). Handprint's staining for cadmium yellow is high (3-4), which is unlike the makers' charts.
- Proposed test: a PY35 glaze over a black line hides it more than a PY150 glaze of the same value; the hiding ratio is checked against the Tr gap (1-2 vs 3-4).

#### handprint-red
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (red pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/waterr.html ; Archived: http://web.archive.org/web/20261011105454/https://www.handprint.com/HP/WCL/waterr.html
- Read: 2026-11-28 (empty twice over https://www; read over http://handprint.com)
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: PR83, e.g. W&N 002 4 3 59 0 3 2; DS 001 4 3 61 1 4 1; M. Graham 010 4 4 55 0 1 4. Summary: "Alizarin crimson PR83 is a fugitive, transparent, staining, dark valued, moderately intense [deep red] pigment". PR108 (25 rows), e.g. W&N cadmium red 082 1 3 50 0 3 2; M. Graham cadmium red 040 0 4 53 1 2 3; Rowney cadmium red 501 0 4 49 1 3 1. Summary: "Cadmium red PR108 is a very lightfast, opaque, staining, moderately dark valued, very intense …". The page has no single-pigment rows for PR101, PV19 or PR122.
- Settles: the transparent-vs-opaque pair at similar hue and value: PR83 Tr 4 against PR108 Tr 0-1, both rated staining.
- Proposed test: the same as handprint-yellow with PR83 against PR108: the ratio of hiding over a black line between the two follows Tr 4 vs 0-1.

#### handprint-earth
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (earth pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/watere.html ; Archived: http://web.archive.org/web/20261016194254/https://www.handprint.com/HP/WCL/watere.html
- Read: 2026-11-28
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: PBr7 burnt sienna, e.g. DS 1 3 56 1 3 1; Holbein 3 2 50 1 4 2; M. Graham 1 2 57 1 2 3. Burnt umber, e.g. DS 1 3 66 0 3 3; Rembrandt 2 4 58 0 1 0. Raw umber, e.g. W&N 3 2 47 3 1 2; DS 2 3 66 1 3 1. PR101, e.g. W&N venetian red 0 4 54 0 2 2; W&N indian red 0 4 62 0 1 2; DS transparent red oxide 4 2 58 2 3 3. Summaries: burnt sienna "dark valued, moderately dull [earth orange], lightly staining, and semiopaque to semitransparent"; burnt umber "a very dark, very dull [earth brown], staining and semiopaque"; PR101 "very lightfast, opaque to transparent, staining ...". No single-pigment PBk11 on this page.
- Settles: one pigment (PR101) at both ends of the transparency scale (Tr 0 for the venetian and indian reds, 4 for transparent red oxide): transparency set by particle size and treatment, not by the colour index name.
- Proposed test: two PR101 paints that differ only in particle size: the fine one is transparent (Tr about 4), the coarse one opaque (Tr 0-1), with similar staining (2 vs 3-4).

#### handprint-white-black
- Citation: Bruce MacEvoy, "handprint : colormaking attributes" (white and black pigments), last revised 07.I.2015.
- Address: https://www.handprint.com/HP/WCL/waterw.html ; Archived: http://web.archive.org/web/20261026143027/https://www.handprint.com/HP/WCL/waterw.html
- Read: 2026-11-28 (empty over https://www; read over http://handprint.com, twice, with the same rows)
- Licence: © 2015 Bruce MacEvoy. Cited only.
- Kept file: none
- Numbers: PW6, W&N 206 2 2 0 0 2 2; Schmincke 101 1 2 0 0 2 1. PW4, W&N 011 1 2 1 0 2 1 (all five brands the same apart from hue). PBk6, DS lamp black 0 4 73 1 4 1. PBk7, MaimeriBlu carbon black 1 4 73 1 3 4; Schmincke charcoal gray 3 2 67 0 3 4. PBk9, W&N ivory black 3 4 64 1 1 1. PBk11, DS lunar black 2 3 72 3 4 2; W&N mars black 1 4 75 1 2 2. Summaries: PW6 "very lightfast, semiopaque, lightly staining"; PW4 "very lightfast, opaque, moderately staining white pigment"; PBk6 "very lightfast, very opaque, heavily staining black pigment"; PBk11 "very lightfast, semiopaque, staining, very dark valued black pigment". Caution: the extracted text lists a "lamp black (Daniel Smith)" under both PBk6 and PBk7 with different numbers; one of the two may be a different DS paint misnamed by the extraction.
- Settles: whites and blacks are not at the opaque end on handprint's dilute (1:3) test: PW6 Tr 1-2, PBk9 Tr 2-3. The PBk7 paints diffuse strongly wet in wet (Df 4 in all four), the PBk6 ones barely (0, 1), PBk11 2, and PBk9 mostly 1-2 (one bone black 4).
- Proposed test: a simulated drop of PBk7 on wet paper spreads further than one of PBk11 or PBk9 (Df 4 vs 2 and mostly 1-2).

#### wn-watercolour-2022
- Citation: Winsor & Newton, "Professional Watercolour Colour Chart" (file title "W&N PROFESSIONAL WATER COLOUR CHART 2022", created 14 April 2022).
- Address: https://www.artsupplies.co.uk/vendure-assets/winsor-newton-professional-watercolour-paint-colour-chart.pdf (a retailer's copy) ; Archived: http://web.archive.org/web/20241213130610/https://www.artsupplies.co.uk/vendure-assets/winsor-newton-professional-watercolour-paint-colour-chart.pdf
- Read: 2026-11-28
- Licence: Winsor & Newton chart; no copyright line printed, copyright by default. Cited only.
- Kept file: none
- Numbers: key: □ Transparent, ⧄ Semi-Transparent, ◩ Semi-Opaque, ■ Opaque; "St Staining", "G Granulation". Read per colour (number, mark, St, G): French Ultramarine 263 T, G; Ultramarine (Green Shade) 667 T; Cobalt Blue 178 ST, G; Cobalt Blue Deep 180 ST, St, G; Cerulean Blue 137 SO, G; Cerulean Blue (Red Shade) 140 O, G; Winsor Blue (Red Shade) 709 T, St; Winsor Blue (Green Shade) 707 T, St; Winsor Green (Blue Shade) 719 T, St; Viridian 692 T, G; Permanent Rose 502 T, St; Quinacridone Magenta 545 T; Alizarin Crimson 004 T, St; Cadmium Red 094 O, St, G; Cadmium Red Deep 097 O, G; Cadmium Lemon 086 O, St; Cadmium Yellow Pale 118 O, St; Cadmium Yellow 108 O; Transparent Yellow 653 T, St; Raw Sienna 552 T, G; Burnt Sienna 074 T; Burnt Umber 076 T; Raw Umber 554 T, G; Light Red 362 SO; Venetian Red 678 O, St; Indian Red 317 O; Chinese White 150 SO; Titanium White 644 O; Ivory Black 331 O, G; Lamp Black 337 O; Mars Black 386 O, G. The chart prints no pigment names.
- Settles: a binary granulating/staining classification for a single maker's line, from which granulating pigments (cobalt, ultramarine, cerulean, viridian, earths, iron oxide black) and non-granulating ones (phthalos, quinacridones, alizarin) can be read.
- Proposed test: a binary classifier on simulated swatches: texture above a threshold for each "G" paint and below it for each unmarked paint, with errors counted.

#### ds-watercolour-2019
- Citation: Daniel Smith, "DANIEL SMITH Extra Fine Watercolor" colour chart, 259 colours, Rev01-19 (PDF created 5 January 2019).
- Address: https://cdn.shopify.com/s/files/1/2101/9939/files/Daniel_Smith_259_Water_Color_Chart_Rev01-19.pdf ; Archived: http://web.archive.org/web/20240808023250/https://cdn.shopify.com/s/files/1/2101/9939/files/Daniel_Smith_259_Water_Color_Chart_Rev01-19.pdf
- Read: 2026-11-28
- Licence: Daniel Smith chart; no copyright line printed, copyright by default. Cited only.
- Kept file: none
- Numbers: legend "Non-staining/Staining 1=Non-Staining 2=Low Staining 3=Medium Staining 4=High Staining"; "Granulation N=No Y=Yes, in varying degrees"; "Transparency ○=Transparent ◑=Semi-Transparent ●=Opaque"; each colour reads LR • staining • granulation • transparency. Read: Ultramarine Blue PB29 I•3•Y•T; French Ultramarine PB29 I•3•Y•T; Cobalt Blue PB28 I•2•Y•ST; Phthalo Blue (GS) PB15:3 I•4•N•T; Phthalo Blue (RS) PB15:6 I•4•N•T; Cerulean Blue PB35 I•1•Y•ST; Cerulean Blue, Chromium PB36 I•2•Y•ST; Viridian PG18 I•1•Y•T; Phthalo Green (BS) PG7 I•4•N•T; Quinacridone Rose PV19 I•3•N•T; Quinacridone Red PV19 I•3•N•T; Quinacridone Lilac PR122 II•3•N•T; Quinacridone Magenta PR202 I(NR)•3•N•T; Alizarin Crimson PR83 IV(NR)•3•N•T; Nickel Azo Yellow PY150 I•2•N•T; Hansa Yellow Medium PY97 I•2•N•ST; Raw Sienna PBr7 I•2•Y•ST; Indian Red PR101 I•3•Y•O; Venetian Red PR101 I•3•Y•O; Transparent Red Oxide PR101 I•1•Y•T; Burnt Sienna PBr7 I•1•Y•ST; Burnt Umber PBr7 I•2•Y•ST; Raw Umber PBr7 I•2•Y•ST; Lamp Black PBk6 I•4•N•O; Ivory Black PBk9 I•2•Y•ST; Lunar Black PBk11 I(NR)•2•Y•T; Chinese White PW4 I•1•N•ST; Titanium White PW6 I•1•N•ST. This chart has cadmium hues only, no cadmium. A newer DS chart may exist; this one was the one read.
- Settles: a 4-step staining scale from the maker, with pigment names: PB15, PG7, PBk6 at 4; PB29, PV19, PR122, PR83, PR101 (opaque) at 3; PB28, PB36, PBr7 umbers at 2; PB35, PG18, burnt sienna, transparent red oxide, whites at 1.
- Proposed test: Spearman correlation between the simulated lift residue and DS staining 1-4 over the 20-odd single-pigment paints here, required above a set level (e.g. 0.7); the same with handprint's St, to see which one the model agrees with.

#### schmincke-horadam-2024
- Citation: Schmincke, "HORADAM® Aquarell – Feinste Künstler-Aquarellfarbe / Sorte 14" colour brochure ("Nuancier 2024", 36 pp.).
- Address: https://denisbeauxarts.com/img/cms/HORADAM_AQUARELL_%20NUANCIER%202024.pdf (a retailer's copy) ; Archived: http://web.archive.org/web/20260308141744/https://www.denisbeauxarts.com/img/cms/HORADAM_AQUARELL_%20NUANCIER%202024.pdf
- Read: 2026-11-28
- Licence: Schmincke brochure; no copyright line found in its text, copyright by default. Cited only.
- Kept file: none
- Numbers: key (p. 2): □ lasierend/transparent, ⧄ halblasierend/semi-transparent, ◩ halbdeckend/semi-opaque, ■ deckend/opaque; staining △ "leicht vom Papier anzulösen (non-staining)", half-filled "halb vom Papier anzulösen (semi-staining)", ▲ "schwer vom Papier anzulösen (staining)"; "G Granulieren / Granulation". Read (pp. 8-20): 101 PW6 O ss; 102 PW4 ST ss; 223/224/225 PY35 SO s; 209 PY150 T ss; 349 PR108 O ss; 347 PR108 O s; 350 PR108 O ss; 357 PR83:1 T ss; 351 PV19 ST ss; 353 PV19 SO ss; 368 PV19 SO ss; 367 PR122 T ss; 493 PB29 T ns G; 494 PB29 ST ss; 487 PB28 ST ss; 483 PB35 ST ns G; 499 PB36 SO ss G; 484 PB15:1 ST ss; 477 PB15:6 ST s; 519 PG7 ST ns; 513 PG18 ST ns G; 653 PR101 T ss; 649 PR101 O s; 660 PBr7+PY43 ST ss; 668 PBr7 SO ss; 665 PBr7 ST ns G; 781 PBk6 O ss; 786 PBk7 O s; 780 PBk9 SO ss; 791 PBk11 O ss G. The page says 22 granulating colours in the 139-colour range.
- Settles: a third maker's scale (3-step staining, 4-step opacity) with pigment names. Granulating here: French ultramarine, cobalt azure (PB35), cobalt cerulean (PB36), viridian, green umber, iron oxide black; not granulating: cobalt blue light (PB28) and ultramarine finest.
- Proposed test: ties in the rank tests must allow Schmincke's coarser scales. The model's opacity ranks, mapped T<ST<SO<O, are compared with Schmincke's over the 30 paints read here.

#### wn-designers-gouache-2007
- Citation: Winsor & Newton, "Designers Gouache Colour Chart", © Winsor & Newton 2007 (PDF created 13 November 2007).
- Address: https://www.jacksonsart.com/media/pdf/wngouachecc.pdf ; Archived: none
- Read: 2026-11-28
- Licence: © Winsor & Newton 2007. Cited only.
- Kept file: none
- Numbers: key: □ Transparent, ⧄ Semi-Transparent, ■ Opaque, ◩ Semi-Opaque, "BL Colour may bleed". Read: Viridian 692 T; Alizarin Crimson 004 SO; Lemon Yellow 345 SO; Primary Yellow 527 SO; Winsor Red 726 SO; Primary Red 524 SO, BL; Permanent Green Light 483 SO. Opaque (■): Permanent Rose 502, Ultramarine 660, Ultramarine (GS) 667, Cobalt Blue 178, Winsor Blue 706, Prussian Blue 538, Cerulean Blue 137, Phthalo Blue 514, Winsor Green 720, Oxide of Chromium 459, Cadmium Lemon 086, Cadmium Yellow Pale 118, Cadmium Yellow 108, Venetian Red 678, Raw Umber 554, Burnt Umber 076, Ivory Black 331, Lamp Black 337, Jet Black 335, Permanent White 512, Zinc White 748. "BL" also on several reds, roses and greens (e.g. Permanent Green Deep 482, Olive Green 447). The chart prints no pigments and no staining column ("BL" is the nearest thing).
- Settles: gouache hides with nearly every pigment, phthalos and cobalts included; the exceptions are viridian (transparent) and alizarin (semi-opaque), the most transparent pigments in their watercolour rows too.
- Proposed test: with the same pigment and a high load plus white extender (gouache), the simulation hides a black line for every paint marked ■ here, and leaves it visible under viridian.

#### liquitex-acrylic-ink-2008
- Citation: Liquitex, "Professional Acrylic ink!" colour chart, © 2008 Liquitex Artists Materials.
- Address: https://boatcraft.com.au/informationpages/Liquitex-Professional-Acrylic-Ink-Colour-Chart.pdf (a retailer's copy) ; Archived: http://web.archive.org/web/20250409122447/https://boatcraft.com.au/informationpages/Liquitex-Professional-Acrylic-Ink-Colour-Chart.pdf
- Read: 2026-11-28
- Licence: © 2008 Liquitex Artists Materials. Cited only.
- Kept file: none
- Numbers: opacity key: "noted with an 'O' (for opaque), a 'TL' (for translucent or semi-opaque), or a 'TP' (for transparent)"; on the chips: "lightfastness I / transparent" etc. Read: Quinacridone Magenta transparent; Naphthol Crimson transparent; Red Oxide opaque; Transparent Burnt Sienna transparent; Transparent Burnt Umber transparent; Yellow Oxide opaque; Cadmium Yellow Light Hue translucent; Phthalocyanine Green (BS) transparent; Cerulean Blue Hue opaque; Phthalocyanine Blue (GS) transparent; Carbon Black opaque; Titanium White opaque. The text also says "Some pigments are rock-solid (like the cadmiums) ... naturally opaque" and "Some are like stained glass (like the phthalocyanines)". Pigment codes were not read.
- Settles: an acrylic ink keeps the watercolour order of transparency for the same pigments: phthalos and quinacridone transparent, iron oxide red and titanium white opaque.
- Proposed test: when aquarelle has an acrylic-ink binder that dries insoluble, its opacity per pigment keeps this order, and nothing lifts after drying.

#### wn-inks-guide
- Citation: Winsor & Newton, "Understanding the lightfast, permanence and archival quality of inks" (guide; no date or author shown; site footer © 2026 Winsor & Newton NA).
- Address: https://www.winsornewton.com/blogs/guides/lightfastness-permanence-archival-quality-of-inks ; Archived: http://web.archive.org/web/20260103083138/https://www.winsornewton.com/blogs/guides/lightfastness-permanence-archival-quality-of-inks
- Read: 2026-11-28
- Licence: © 2026 Winsor & Newton NA, all rights reserved. Cited only.
- Kept file: none
- Numbers: none, only classes: "Drawing Inks are made with dyes, making them brilliant and transparent, but not lightfast", "formulated with soluble dyes in a high-quality shellac solution", "Fast-drying and water-resistant"; "Black Indian Ink: Is based on shellac, making it water-resistant—ideal for applying paint washes once dry"; "Liquid Indian Ink: Archival and permanent, though not waterproof"; "White, Silver, Gold, and Indian Black: Pigmented"; "Calligraphy Inks are pigment-based ... but they are not waterproof ... even when dry, they can be reactivated with water".
- Settles: three kinds of black ink behave differently once dry. A shellac-bound India ink does not lift under a later wash; Liquid Indian Ink and calligraphy ink rewet.
- Proposed test: a wash laid over dried "Black Indian Ink" (shellac) moves none of the black; over dried "Liquid Indian Ink" it picks some up and spreads it.

### Not found or not verified

- **handprint PV19 and PR122 (violet/magenta page `waterv.html`, magenta page `waterc.html`).** The fetch tool returned an empty page every time, over http and https, with and without www and a query string. The Wayback copy exists (http://web.archive.org/web/20261017093838/http://handprint.com/HP/WCL/waterv.html) but web.archive.org could not be fetched from here. A search summary said handprint rates PV19 rose's lightfastness as variable across brands and PR122 as consistently lightfast, but no Tr/St/Gr rating was read, so the table has none.
- **handprint: no single-pigment PR101 row on the red page**, and no PBk11 section on the earth page (they are on the earth and white/black pages, used above).
- **W&N watercolour pigments.** The 2022 chart prints no pigment names. The pigment column for W&N paints relies on handprint's 2015 listing of the same paint names (W&N's numbers changed since). W&N Burnt Sienna, Burnt Umber and Lamp Black are not matched to a pigment here. W&N New Gamboge (267) is a mixture by handprint's listing and was not used for PY153.
- **Cadmiums at Daniel Smith.** The 2019 chart read has only cadmium hues; a later DS chart with genuine cadmiums was not read.
- **M. Graham, Holbein, Sennelier charts**: not searched for lack of time; no ratings from them were read.
- **Daler-Rowney FW acrylic ink**: the maker's page fetched empty, and retailers disagree on its transparency (one says opaque, another transparent). Not used.
- **W&N Designers Gouache current chart**: the Shopify copy found returned 404; the 2007 chart was used. Its Quinacridone Magenta, Burnt Sienna and Cadmium Red marks were not read. No Wayback copy of the 2007 chart.
- **India ink opacity**: no maker's figure for the opacity of India ink was found; W&N says only that its drawing inks are transparent (dyes) and its Indian Black pigmented.
- **Jane Blundell** (an independent tester whose site summarises handprint and her own swatches): seen only in a search result, not read.
- **Markers**: no published per-pigment ratings found or searched.

## Measured spectra of watercolour, gouache and ink paint-outs, and of pigments in gum arabic

References for `murex.aquarelle`. Gathered 2026-11-28. Every address was fetched that day. "Archived" is the answer of `https://archive.org/wayback/available?url=...`; web.archive.org itself could not be fetched from this session, so the snapshots were not opened.

Kept files are in `references/spectra/`. The `deborah2022_core_*` CSVs are written there by `tools/aquarelle/extract_deborah.py` from the library kept beside them. Files named `*_murex24.csv` are box means over murex's 24 bands (`murex.spectral.WAVELENGTHS`, about 13 nm wide). Files named `*_10nm.csv` are box means 10 nm wide.

**Licence warning.** murex is MIT. Two of the kept sets are **non-commercial** (CC BY-NC): Cosentino 2014, and the IFAC policy. They may serve as references for the owner. They must not be committed into the repository or shipped in the wheel without the owner deciding so. The CC BY sets (Deborah 2022) and the CC0 set (revigo) can be committed with attribution.

**Summary.** No dataset found gives K and S of *watercolour* (gum arabic) paints per pigment, and none measures a watercolour wet. Here is what exists:
- Single paint-outs in gum arabic on watercolour paper (Cosentino 2014, kept).
- Thickness series on paper (Deborah 2022, binder not stated, kept).
- Dilution series on paper and transmittance on film (NTU 2019, NC, not kept).
- Dilution and mixture swatches (Asadi 2020, data host gone).
- One paper giving the over-white and over-black method for watercolour (Tominaga 2016, numbers only in figures).
- K and S *are* derivable for oil (revigo, over black and over white, CC0, kept) and acrylic (Berns/RIT, masstone and tint, no licence).

---

#### cosentino2014
- Citation: A. Cosentino, "FORS spectral database of historical pigments in different binders", e-conservation Journal 2 (2014) 53–65 (page range given as 57–68 elsewhere). No DOI found. Data: "FORS-Spectral-database-of-historical-pigments-in-different-binders-CSV.zip", CHSOS (Cultural Heritage Science Open Source).
- Address: https://chsopensource.org/new-free-pigments-fors-spectroscopy-database (data: https://chsopensource.org/download/94363/ ; paper: https://chsopensource.org/download/7142/ ; original home, cited in the paper: http://e-conservation.org/issue-2/36-FORS-spectral-database) ; Archived: http://web.archive.org/web/20240414031842/https://chsopensource.org/new-free-pigments-fors-spectroscopy-database/ (data zip: none; paper: http://web.archive.org/web/20260301220207/https://chsopensource.org/download/7142/ ; e-conservation page: http://web.archive.org/web/20230715093629/http://www.e-conservation.org/issue-2/36-FORS-spectral-database)
- Read: 2026-11-28
- Licence: the journal's back page says "e-conservation journal is published and distributed under the Creative Commons Licence Attribution - Noncommercial 3.0" (CC BY-NC 3.0). The ICOMOS archive record of the issue also says CC BY-NC. The CSV zip carries no licence of its own. The CHSOS page calls it "free" to download. Redistribution is allowed only for non-commercial use, with attribution. **Do not commit it into murex (MIT) without the owner's decision.**
- Kept file: none in the repository: the licence is non-commercial, and murex is MIT. Whether to keep it is the owner's decision. (It was downloaded once and read: `cosentino2014_FORS-database-CSV.zip`, 6.2 MB, sha256 starting 709c3fc3; the extracts below are what were measured from it.)
- Numbers:
  - **Samples.** 54 historical pigments, all from Kremer Pigmente. Each was measured as powder, ground with a glass muller into gum arabic, egg tempera and linseed oil, and as fresco.
  - **Substrate.** Brushed onto Fabriano watercolour paper (cellulose and cotton, acid- and lignin-free, 270 g/m²). The paper's spectrum is flat. Fresco was laid on marble powder and lime (2:1).
  - **Instrument.** Ocean Optics USB4000, measured dry. Range 360–1000 nm in raw CCD pixels of about 0.19 nm (3320 rows). Resolution 1.5–2.3 nm FWHM. Halogen lamp.
  - **Two gum arabic files.**
    - "gum Arabic.csv" was measured with an integrating sphere (ISP-R). It has 56 columns, with extra columns "cardboard" and "Gumarabic".
    - "gum arabic refletion probe.csv" was measured with a 45°/45° fibre probe (R400-7). The paper says the probe was used only on the gum arabic set.
  - **Pigment list.** It has no quinacridone and no cerulean (PB35). It has ultramarine (synthetic), cobalt blue, phthalo blue, phthalo green, viridian, alizarin, burnt sienna, cadmium red, cadmium yellow, titanium white, lamp, ivory and vine black, Prussian blue, red ochre, and more.
  - **The sphere file is not an absolute reflectance factor.** Every dark paint sits on a floor of about 0.18–0.22: lamp black 0.21 at 550 nm, phthalo blue 0.20. Whites and the "cardboard" exceed 1: TiO2 1.30 and cardboard 1.23 at 550 nm. Use the probe file, or rescale.
  - **Probe file, reflectance at 450/550/650 nm, 10 nm box means:**

    | Pigment | 450 nm | 550 nm | 650 nm |
    |---|---|---|---|
    | ultramarine | 0.149 | 0.041 | 0.039 |
    | cobalt blue | 0.505 | 0.090 | 0.061 |
    | phthalo blue | 0.098 | 0.015 | 0.025 |
    | phthalo green | 0.023 | 0.015 | 0.010 |
    | viridian | 0.063 | 0.056 | 0.033 |
    | alizarin | 0.021 | 0.023 | 0.751 |
    | burnt sienna | 0.038 | 0.044 | 0.177 |
    | Cd red | 0.026 | 0.026 | 0.988 |
    | Cd yellow | 0.041 | 1.041 | 1.026 |
    | TiO2 | 0.935 | 0.875 | 0.854 |
    | lamp black | 0.065 | 0.060 | 0.059 |
    | ivory black | 0.034 | 0.032 | 0.033 |
  - **Features of the probe spectra:**

    | Pigment | Peak | Minimum | Half-height crossing |
    |---|---|---|---|
    | ultramarine | 460 nm | 600 nm | 496 nm |
    | cobalt blue | 440 nm | 600 nm | 517 nm, and rises again past 695 nm |
    | phthalo blue | 460 nm | 540 nm | — |
    | phthalo green | 500 nm | 580 nm | — |
    | viridian | 510 nm | 620 nm | — |
    | Cd yellow | — | — | 488 nm |
    | Cd red | — | — | 613 nm |
    | alizarin | — | — | 606 nm |
    | burnt sienna | — | — | 628 nm |
  - **CIELAB through murex's `reflectance_to_srgb`/`srgb_to_lab`, probe file, 24 bands:**

    | Pigment | L* | a* | b* |
    |---|---|---|---|
    | ultramarine | 26.6 | 8.1 | −28.1 |
    | cobalt | 45.2 | 5.8 | −50.4 |
    | phthalo blue | 17.5 | 16.4 | −30.1 |
    | PG7 | 21.7 | −18.5 | −2.3 |
    | viridian | 30.5 | −21.8 | −4.1 |
    | alizarin | 42.2 | 63.3 | 44.1 |
    | Cd red | 43.5 | 69.2 | 42.9 |
    | Cd yellow | 97.2 | −20.8 | 87.7 |
    | TiO2 | 95.0 | −0.1 | −3.0 |
    | ivory black | 21.0 | 0.8 | −1.2 |
  - Cd red and Cd yellow read above 1 in the probe file.
  - Concentration and layer thickness are not given (one brushed layer, "masstone" in effect). There is no tint, no over-black and no wet measurement.
- Settles:
  - The dry colour and spectral shape of a full-strength gum arabic paint-out on watercolour paper for 13 of the 15 core pigments. PB35 and the quinacridones are missing.
  - Positions of bands and edges, e.g. the 600 nm minimum of ultramarine, cobalt's rise past 650 nm, the Cd yellow edge near 490 nm and the Cd red edge near 610 nm.
  - It does not give K and S. A single layer of unknown thickness over a white paper gives only the layer-plus-paper reflectance.
- Proposed test: murex's pigments laid as a heavy (near-opaque) wash on a white paper match the probe spectra in shape. Peak, minimum and half-height wavelengths should agree within ±15 nm, and ΔE00 ≤ 8 for dark paints. Absolute level is uncertain: probe geometry, values above 1 for the cadmiums.

#### cosentino2016-transmittance
- Citation: A. Cosentino, "Transmittance spectroscopy and transmitted multispectral imaging to map covered paints", Conservar Património 24 (2016). DOI 10.14568/cp2015021.
- Address: https://arp.org.pt/revista_antiga/pt/artigos/2015021.html (data: https://chsopensource.org/download/7948/, "Pigments-Transmittance-SpectroscopyDatabase.csv", 779 KB, text/csv) ; Archived: http://web.archive.org/web/20260412133112/https://arp.org.pt/revista_antiga/pt/artigos/2015021.html (data: http://web.archive.org/web/20231117035005/https://chsopensource.org/download/7948/)
- Read: 2026-11-28
- Licence: the article is CC BY-NC-ND 4.0 (journal rights page). The CSV on CHSOS carries no licence. Not downloaded.
- Kept file: none
- Numbers: transmittance of the same 54 Kremer pigments in gum arabic, laid on a glass plate, plus a swatch of gum arabic alone. ASEQ LR1 spectrometer, 300–1000 nm, 2 nm resolution; the published data cover 400–900 nm. Layer thickness and pigment concentration were not read.
- Settles: the spectral shape of absorption (K) of thin gum arabic films of the same pigments as cosentino2014. Paired with cosentino2014 it bounds K/S, which is the nearest thing to K and S in gum arabic that was found.
- Proposed test: murex's K for each pigment has its transmission minima and maxima at the same wavelengths as the measured film. Exp(−K·d) for some d should follow the measured transmittance within 0.05 after fitting d.
- How to fetch: `curl -L -o transmittance.csv https://chsopensource.org/download/7948/`. Ask the owner first; it is non-commercial at best.

#### ifac-fors
- Citation: A. Aldrovandi, A. Casini, M. L. Altamura, M. T. Cianfanelli, P. Riitano, A. Cagnini, M. Galeotti, M. Picollo, B. Radicati, A. Agostini, D. Andreuccetti, L. Stefani, eds., Fiber Optics Reflectance Spectra (FORS) of Pictorial Materials in the 270-1700 nm range, 2020 ed., SABeC IFAC-CNR Spectral Database. Citation form from the policy PDF. No DOI.
- Address: https://spectradb.ifac.cnr.it/fors/ (also https://fors.ifac.cnr.it/fors/ ; info: https://fors.ifac.cnr.it/fors/info.php ; policy: https://spectradb.ifac.cnr.it/DatabasePolicy.pdf) ; Archived: http://web.archive.org/web/20261117010540/https://spectradb.ifac.cnr.it/fors/ (policy: http://web.archive.org/web/20230924231206/https://spectradb.ifac.cnr.it/DatabasePolicy.pdf)
- Read: 2026-11-28
- Licence: "SABeC IFAC-CNR Spectral Databases Policy". Use is "just for scientific purposes": "You can, without permission, copy, distribute, display, or perform the Item, for non-commercial uses". Citation is mandatory. The pages also say "All rights reserved".
- Kept file: none (not downloadable)
- Numbers:
  - **Correction to the brief.** This database is by IFAC and the Opificio delle Pietre Dure, not by Cosentino, and it has **no gum arabic and no watercolour**. Its binders are egg tempera, linseed (stand) oil and mastic, plus pure pigment.
  - Laid on plywood with a gypsum and rabbit-skin-glue ground, prepared in 1994. Pigments from Zecchi.
  - Ranges 270–820, 350–1000 (Zeiss MCS501, 0.8 nm/pixel) and 980–1700 nm (MCS511, 6 nm/pixel). Geometry 2×45°/0° (NIR 45°/0°). Spectralon 99% reference.
  - "To date the spectroscopic data cannot be downloaded via the spectra pages": plots only. Access is through registration (https://spectradb.ifac.cnr.it/userreg/).
- Settles: nothing for watercolour directly; at most a cross-check of band positions in other binders.
- Proposed test: none for aquarelle.

#### ifac-mowcres
- Citation: A. M. Silva, M. Picollo, L. Stefani, eds., Visible and Near-Infrared Reflectance Spectra of Modern Watercolours, 2020 ed., SABeC IFAC-CNR Spectral Database. No DOI.
- Address: https://spectradb.ifac.cnr.it/mowcres/ ; Archived: http://web.archive.org/web/20260613095958/https://spectradb.ifac.cnr.it/mowcres/
- Read: 2026-11-28
- Licence: the same IFAC policy as ifac-fors (non-commercial, citation mandatory, "All rights reserved"). Access needs credentials.
- Kept file: none
- Numbers:
  - Modern watercolours on paper, after the palette of Amadeo de Souza-Cardoso (1887–1918). Measured by FORS and by a lab double-monochromator spectrophotometer (DRS, Perkin-Elmer Lambda 1050 per a search snippet, not verified), 350–2500 nm, specular excluded.
  - The page's own JavaScript lays out each pigment's photo table with columns **5%, 10%, 20%, 30%, 40%** and rows **"Normal"** and **"Transparency"**. That looks like a concentration series, measured in reflectance and in transmission or over a dark backing; this is not verified.
  - The pigment list, brand and step could not be read without logging in.
- Settles (if it can be obtained): dilution series of modern watercolours, possibly with a transparency measurement. That is the right material for K and S at several concentrations.
- Proposed test: if obtained, murex's wash at 5–40% concentration reproduces the measured series within ΔE00 ≤ 5 after fitting one thickness per sample. The owner would have to register and ask IFAC-CNR (contact via https://fors.ifac.cnr.it/fors/contacts.php) for the data and for permission.

#### ifac-drs
- Citation: M. Picollo, G. Basilissi, C. Cucci, L. Stefani, M. Tsukada, eds., Ultraviolet, Visible and Near Infrared Reflectance Spectra of Modern Pictorial Materials in the 200-2500 nm range, 2020 ed., SABeC IFAC-CNR Spectral Database.
- Address: https://spectradb.ifac.cnr.it/drs/ ; Archived: http://web.archive.org/web/20260317003202/https://spectradb.ifac.cnr.it/drs/
- Read: 2026-11-28
- Licence: IFAC policy (non-commercial; "All rights reserved").
- Kept file: none
- Numbers: mock-ups of materials "most commonly used in the second part of the 19th century" (with the National Museum of Western Art, Tokyo). d/0° geometry, 200–2500 nm. Binder and step are not stated on the page; plots only.
- Settles: nothing for watercolour as read.
- Proposed test: none.

#### deborah2022
- Citation: H. Deborah, "Hyperspectral Pigment Dataset", 12th WHISPERS 2022, DOI 10.1109/WHISPERS56178.2022.9955067. Data: H. Deborah, "Hyperspectral pigments", v1.0, Zenodo 2022, DOI 10.5281/zenodo.5592485 (concept DOI 10.5281/zenodo.5592484).
- Address: https://zenodo.org/records/5592485 (explorer: https://hyppigments.streamlit.app/) ; Archived: http://web.archive.org/web/20240420023703/https://zenodo.org/records/5592485
- Read: 2026-11-28
- Licence: CC BY 4.0 (Zenodo metadata `cc-by-4.0`).
- Kept file: `deborah2022_speclib_medians.sli` and `.hdr` (the ENVI spectral library of medians, 1592 spectra × 186 bands), `deborah2022_pigmentlistZenodo.xls`, `deborah2022_pigmentpatcheslist.pdf`. Core extracts: `deborah2022_core_{raw,10nm,murex24}.csv`. The per-group image cubes (1.2–3.4 GB each, about 40 GB in all) were not downloaded.
- Numbers:
  - **Samples.** Hyperspectral images of 195 patches from **Kremer Pigmente colour charts** (327 unique pigments) on acid-free 180 g paper, according to the HYPERDOC paper. The binder is **not stated** anywhere read.
  - **Thicknesses.** Each pigment has 4 spectra, `--1`..`--4` (`sh1..sh4`). These are the four diagonal bands of increasing thinness visible on each chart patch: sh1 darkest, sh4 lightest with the paper showing through.
  - **Range.** 405–996 nm, about 3.19 nm per band. Reflectance factor 0..1. Measured dry.
  - **Core pigments found (Kremer numbers):**
    - Blues: ultramarine 45010 and 45080, cobalt blue 45710, **cobalt cerulean 45730 (PB35)**, phthalo blue 23050.
    - Greens: phthalo green 23000, viridian 44250.
    - Reds and pinks: alizarin crimson light 23600, cadmium red light 21120, Hostaperm pink E 23153 (sold as PR122 quinacridone; the CI name is not in the data), Hostaperm red 23720 (CI name not verified).
    - Others: burnt sienna 40470, cadmium yellow medium 21040, ivory black 12000.
    - No titanium white, no lamp or carbon black.
  - **Thickness series, reflectance at 450 nm, sh1 → sh4:**
    - ultramarine 45010: 0.13 / 0.25 / 0.43 / 0.70
    - cobalt cerulean: 0.30 → 0.57
    - Cd yellow at 550 nm: 0.24 → 0.82
    - Cd red at 650 nm: 0.38 → 0.84
  - **CIELAB (murex conversion), sh1 → sh4:**
    - ultramarine 45010: (27.2, 6.8, −25.2) → (42.0, 28.5, −68.4)
    - cerulean: (45.8, −7.4, −28.4) → (53.3, −3.6, −45.6)
    - viridian: (37.2, −26.2, −1.3) → (44.1, −34.6, 5.2)
    - Cd yellow: (51.8, −7.1, 38.8) → (85.6, 0.7, 86.2)
    - Hostaperm pink E: (29.3, 17.1, −4.0) → (43.2, 49.1, −2.3)
  - Dark spectra sit on a floor of about 0.04–0.05. That is probably surface or stray light (camera, not sphere).
  - Coat counts and thicknesses are not given, and the bare paper's spectrum is not in the library.
- Settles:
  - How a pigment's colour moves as its layer thins over white paper, for 4 thicknesses. That is the behaviour a wash must show.
  - The hue of PB35 and of a PR122 on paper. This is the only kept source with cerulean and a quinacridone.
  - It gives K and S only if the thickness ratios are assumed (e.g. 4:3:2:1 coats) and the paper's reflectance is taken from the patch images.
- Proposed test: for each of these pigments, murex's wash at four thicknesses over a white paper follows the measured sh1..sh4 path in a*b*. For each sample, fit one thickness per band; residual ΔE00 ≤ 4 after the fit, and the hue angle ordering preserved, e.g. ultramarine's hue moves towards violet as it thins (a* rises from 6.8 to 28.5).

#### ntu-wpsm2019
- Citation: M.-Y. Chen, Y.-B. Huang, S.-P. Chang, M. Ouhyoung, "Prediction Model for Semitransparent Watercolor Pigment Mixtures Using Deep Learning with a Dataset of Transmittance and Reflectance", arXiv:1904.00275 (2019). Dataset "NTU watercolor pigments spectral measurement dataset (NTU WPSM)", ancillary files of the arXiv submission.
- Address: https://arxiv.org/abs/1904.00275 (files: https://arxiv.org/src/1904.00275v1/anc/NTU_WPSM_dataset/ — `MQ_train_1956_X_ok.csv` 4.0 MB, `MQ_train_1956_Y_ok.csv`, `MQ_test_488_X_ok.csv` 1.0 MB, `MQ_test_488_Y_ok.csv` 0.2 MB, `ReadMe.txt`) ; Archived: http://web.archive.org/web/20251230100222/https://arxiv.org/abs/1904.00275
- Read: 2026-11-28
- Licence: CC BY-NC-SA 4.0 (the arXiv licence of the submission). Not kept.
- Kept file: none
- Numbers:
  - **Paints.** 13 **Winsor & Newton** watercolours: cadmium red, alizarin crimson, burnt sienna, lemon yellow, cadmium yellow, raw sienna, sap green, cerulean blue, cobalt blue, ultramarine, Prussian blue, ivory black, Chinese white.
  - **Quantities.** 12 quantities each: 0.01–0.10 mL, 0.12 and 0.16 mL, spread with a silicone scraper on 1.5×1.5 cm squares bounded by masking tape. Measured dry.
  - **Measurements.** **Reflectance** over white paper (Canson "Ca grain") and **transmittance** on transparent film. OTO SD1220 spectrometer, 380–780 nm at 10 nm (41 values). Also 780 two-pigment mixtures (ratios 1:1, 1:2, 2:1).
  - **File layout.** Each X row holds, for 41 wavelengths, T and R of pigment A, T and R of pigment B and the paper's R (205 columns), plus the two quantities. Y holds the mixture's R.
  - **Rows carry no pigment names.** The single-pigment spectra are repeated in many rows and would have to be matched to the 13 paints.
  - The paint is weighed out "as paint" (tube paint diluted? not stated); the water ratio is not given.
- Settles:
  - Thickness series of 13 W&N watercolours (cerulean, cobalt, ultramarine, alizarin, cadmiums, burnt sienna, ivory black among them) in **both reflectance over paper and transmittance**. From these, K and S per paint can be fitted (Kubelka's R and T method).
  - Also measured two-pigment mixtures to test KM mixing.
- Proposed test: K and S fitted from murex's pigments reproduce the measured R(paper) and T(film) at 12 quantities, with quantity taken as proportional to thickness, within RMS 0.03. murex's KM mixture of two paints predicts the measured mixture R within ΔE00 ≤ 5 on median. Needs the owner's decision on NC-SA data, which could be used locally and not committed.

#### asadi2020
- Citation: A. Asadi Shahmirzadi, V. Babaei, H.-P. Seidel, "A Multispectral Dataset of Oil and Watercolor Paints", IS&T Electronic Imaging 2020, Material Appearance, 107-1–107-4. DOI 10.2352/ISSN.2470-1173.2020.5.MAAP-107.
- Address: https://library.imaging.org/ei/articles/32/5/art00007 (data said to be at http://cam.mpi-inf.mpg.de/ and http://www.azadehasadi.com/) ; Archived: http://web.archive.org/web/20261112172504/https://library.imaging.org/ei/articles/32/5/art00007 (cam.mpi-inf: http://web.archive.org/web/20211009000555/http://cam.mpi-inf.mpg.de/ ; azadehasadi.com: http://web.archive.org/web/20260514125054/http://www.azadehasadi.com/)
- Read: 2026-11-28
- Licence: the paper is CC BY 4.0 (stated on its first page). **The data's licence is unknown.** A GitHub issue of another watercolour project (timbrinded/watercolour#42) says the data "carries no licence"; this was not verified.
- Kept file: `asadi2020_multispectral-dataset-oil-watercolor_paper.pdf` (the paper only, in `references/papers/`).
- Numbers:
  - **Watercolour set.** 397 swatches from 9 **Schmincke** watercolours: Lemon Yellow, Cadmium Yellow light, Yellow Ochre, Cadmium Red light, Prussian Blue, Ultramarine Finest, Phthalo Green, Permanent Carmine, Ivory Black. Lightened with water, not white.
    - The mixtures were weighed (0.01 g) in a jar. 0.05 mL was taken with a syringe and swept with a silicone brush onto Hahnemühle Fine Art Archival Inkjet paper, 280 g, then framed 18 mm square.
  - **Oil set.** 286 swatches from 8 Old Holland oils on Arches oil paper.
  - **Measurement.** X-Rite Color i7, d/8°, specular excluded, 400–700 nm at 10 nm. Measured dry. The mixture ratios are published with the data.
  - Data host: cam.mpi-inf.mpg.de now redirects to aidam.mpi-inf.mpg.de, which lists no dataset. azadehasadi.com does not resolve. Both have Wayback snapshots, which could not be opened from here.
- Settles: the dry colours of a real watercolour palette at known paint:water ratios and in known mixtures, on a known paper. It is the best published test of KM mixing and dilution for watercolour, if the data can be had.
- Proposed test: murex's KM mix of the corresponding pigments, at the published ratios and diluted by thickness, reproduces the 397 swatches with median ΔE00 ≤ 5. Fetch the Wayback snapshots by hand, or write to the authors (Max-Planck-Institut für Informatik) for the files and a licence.

#### tominaga2016
- Citation: S. Tominaga, S. Dozaki, Y. Kuma, K. Hirai, T. Horiuchi, "Modeling and Estimation for Surface-Spectral Reflectance of Watercolor Paintings", IS&T Electronic Imaging 2016, Measuring, Modeling, and Reproducing Material Appearance, MMRMA-364.
- Address: https://library.imaging.org/ei/articles/28/9/art00012 (PDF: https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/ei/28/9/art00012) ; Archived: http://web.archive.org/web/20260712083857/https://library.imaging.org/ei/articles/28/9/art00012
- Read: 2026-11-28
- Licence: "©2016 Society for Imaging Science and Technology"; free to read. No data released.
- Kept file: none
- Numbers:
  - **Paints.** Four **Holbein** Artists' Watercolours: Vermilion, Permanent Yellow Light, Viridian, Cobalt Blue.
  - **Application.** Laid with a 5 mil applicator at "water ratios" (weight % of paint in the total) of 97.5, 95, 90, 80, 70, 60, 50 (reference), 40 and 30%. Two papers, Canson Mi-Teintes and Takeo Mermaid, with **white and black backing papers**.
  - **Measurement.** GretagMacbeth Spectrolino.
  - **Method.** K and S were taken by the over-white/over-black formula (after Minato), with Saunderson correction. The fitted Saunderson k1 and k2 were mostly 0, with k2 = 0.04 or 0.02 for two paints on Canson.
  - **Model.** S and K scale linearly with the paint ratio: S = (c/c_s)·S_s, K = (c/c_s)·K_s.
  - **Fit.** RMSE 0.01–0.06 and ΔEab 2.5–5.5 across water ratios. Spectra appear only in figures.
- Settles: that watercolour on paper is modelled adequately by KM with K and S proportional to paint concentration, at ΔE about 3–5. Also the measurement recipe (over white and over black backings) that murex's owner would need to make K and S from real paints.
- Proposed test (structural): in murex, a wash's K and S scale linearly with pigment load, and a wash at c = 0.3 to 0.975 of a reference reproduces the reference's own KM prediction to the bit. This is a property test, not a match to data.

#### revigo-geldof2018
- Citation: M. Geldof, A. Proaño Gaibor, E. Kirchner, F. Ligterink, "Reconstructing Van Gogh's palette to determine the optical characteristics of his paints", Heritage Science 6 (2018) 17. DOI 10.1186/s40494-018-0181-6. Data and code: F. Ligterink, "revigo-spectra", Rijkserfgoedlaboratorium Amsterdam.
- Address: https://github.com/fligt/revigo-spectra (pages: https://fligt.github.io/revigo-spectra/measured-reflectance-spectra.html) ; Archived: none
- Read: 2026-11-28
- Licence: **CC0 1.0** (LICENSE file of the repository). The page says "You are free to make use of the data and code", and asks for a citation of the article.
- Kept file: `revigo_aggregated-palette-spectral-data.txt`, `revigo_mixture-specifications.txt`, `revigo_LICENSE-CC0.txt`.
- Numbers:
  - **Samples.** 84 samples × 4 measurements, 400–700 nm at 10 nm, in %. Reconstructed 19th-century **oil** paints (Van Gogh's palette): eosin lakes, cochineal, minium, vermilion, viridian, emerald green, ultramarine, cobalt blue, Prussian blue, chrome yellows, zinc white, lead white, bone black, BaSO4, CaCO3.
  - **Mixtures.** Masstone (100-0-0), tints with zinc white (about 10:90 and 50:50) and tones with bone black (about 99:1 and 90:10).
  - **Suffixes**, read from the data:
    - `_w` is the bare white ground, ≈0.82–0.88.
    - `_b` is the bare black ground, ≈0.05.
    - `_ow` is the paint over white.
    - `_ob` is the paint over black.
  - Example values:
    - ultramarine 11A at 450 nm: 0.276 over white, 0.106 over black
    - cobalt 12A at 450 nm: 0.309 over white, 0.268 over black
    - viridian 09A at 550 nm: 0.053 over white, 0.052 over black, i.e. nearly opaque
- Settles: K and S, exactly by Kubelka's over-black/over-white method, for oil paints of ultramarine, cobalt blue, viridian, Prussian blue, bone black and zinc white (huile's medium). It is a cross-check for aquarelle's pigment absorption shapes, though the binder differs.
- Proposed test: K/S computed from murex's ultramarine, cobalt, viridian and bone black have the spectral shape of the revigo-derived K/S (correlation ≥ 0.95 over 400–700 nm). For huile, a layer over white and over black reproduces `_ow`/`_ob` within 0.03.

#### berns-artist-db
- Citation: R. S. Berns, "Artist Paint Spectral Database", RIT Studio for Scientific Imaging and Archiving of Cultural Heritage (CIC 2016 proceedings; see also Berns, "Artist Acrylic Paint Spectral, Colorimetric, and Image Dataset", Archiving 2022, 45–49, DOI 10.2352/issn.2168-3204.2022.19.1.10).
- Address: https://www.rit.edu/science/sites/rit.edu.science/files/2019-03/ArtistSpectralDatabase.pdf (spreadsheet, now a redirect to a lab page: https://www.rit.edu/cos/colorscience/mellon/Data/Final_artist_database.xlsx ; index: https://www.rit.edu/science/studio-scientific-imaging-and-archiving-cultural-heritage) ; Archived: http://web.archive.org/web/20261113170149/https://www.rit.edu/science/sites/rit.edu.science/files/2019-03/ArtistSpectralDatabase.pdf (xlsx: http://web.archive.org/web/20190803102144/https://www.rit.edu/cos/colorscience/mellon/Data/Final_artist_database.xlsx ; index: http://web.archive.org/web/20261023063813/https://www.rit.edu/science/studio-scientific-imaging-and-archiving-cultural-heritage)
- Read: 2026-11-28
- Licence: none stated for the data. The page's software is "noncommercial, educational, scholarly, and/or charitable purposes only". Not downloaded.
- Kept file: none
- Numbers:
  - **Paints.** 19 **Golden Heavy Body acrylics** with CI names:
    - Whites and blacks: PW6 titanium white, PBk9 bone black.
    - Yellows and oranges: PY184, PY74, PY83, PO20, PO73.
    - Reds and violets: PR108, PR254, PV19, PR122, PV23.
    - Blues and greens: PB29, PB28, PB36:1, PB15:1, PB15:4, PG7, PG36.
  - **Application and measurement.** Leneta 3B opacity charts, 0.006" bar. Macbeth MS7000 sphere, 380–750 nm at 10 nm.
  - **K and S.** By the **masstone–tint method** (paint out of the tube, and mixed with white at known concentration). Saunderson k1 = 0.03, k2 = 0.65. 770 computed tint and tone spectra. PCA: 3 eigenvectors carry 97.5% of variance, 5 carry 99.5%.
- Settles: measured K and S spectra of modern artists' pigments (PB29, PB28, PB15, PG7, PV19, PR122, PR108, PW6, PBk9), the same pigments as murex's core, in acrylic. A strong reference for the *shape* of K and of S per pigment, independent of binder.
- Proposed test: murex's K(λ) and S(λ) for each core pigment correlate ≥ 0.9 in shape with Berns's. A tint of murex's pigment with its titanium white at Berns's concentrations reproduces his computed tint within ΔE00 ≤ 5. The xlsx would be fetched by hand from the Wayback snapshot, with the owner's agreement, since no licence is stated.

#### okumura2005-paint-research
- Citation: Y. Okumura, "Developing a Spectral and Colorimetric Database of Artist Paint Materials", M.S. thesis, RIT, 2005 (record says "This paper has been withdrawn"). Supporting data "Okumura pigment and spectral information".
- Address: http://www.rit-mcsl.org/StudentResearch/paint_research.zip (application/zip, 5,710,609 bytes, live) ; thesis record https://repository.rit.edu/theses/8126/ ; Archived: http://web.archive.org/web/20241104011529/http://www.rit-mcsl.org/StudentResearch/paint_research.zip (thesis: http://web.archive.org/web/20240816113552/https://repository.rit.edu/theses/8126/)
- Read: 2026-11-28
- Licence: none stated. Not downloaded.
- Kept file: none
- Numbers: acrylic artists' paints, two-constant KM, 33 wavelengths (per the Pigmento paper, arXiv:1707.08323). Contents of the zip not read.
- Settles: K and S of acrylic paints; used by Pigmento as its measured set.
- Proposed test: as berns-artist-db.

#### golden-glassner-haines
- Citation: A. Glassner, E. Haines, "Golden Paint Spectra" (data from Golden Artist Colors, Inc.), last changed 2025-10-16.
- Address: https://www.realtimerendering.com/golden.html (zip: https://www.realtimerendering.com/downloads/GoldenSpectra.zip, refused to scripted requests with HTTP 403) ; Archived: http://web.archive.org/web/20241216104328/https://www.realtimerendering.com/golden.html
- Read: 2026-11-28
- Licence: no licence text. "Golden has allowed" sharing, and users are asked to tell the authors what they do with it. Not downloaded.
- Kept file: none
- Numbers: 78 Golden Heavy Body acrylics, drawdowns 10 mil wet (about 6 mil dry) over a Leneta **white** card only. L*a*b*, reflectance at 400–700 nm per 10 nm (D65/10°), and a K/S column. Golden says the paints are not opaque at that thickness and that the card's reflectance is included.
- Settles: K/S (single-constant) of many modern pigments in acrylic, over white only.
- Proposed test: secondary to berns-artist-db.

#### reichert2025-drifts-hsi
- Citation: A. S. Reichert, A. B. López-Baldomero, F. Moronta-Montero, A. López-Montes, E. M. Valero, C. Cardell, "Database of diffuse reflectance infrared Fourier transform spectroscopy (DRIFTS) and hyperspectral imaging (HSI) spectra of pigments and dyes for historical document analysis", Anal. Bioanal. Chem. 417 (2025) 4351–4372. DOI 10.1007/s00216-025-05948-3. Data: figshare DOI 10.6084/m9.figshare.28639103.
- Address: https://pmc.ncbi.nlm.nih.gov/articles/PMC12283775/ (data: https://doi.org/10.6084/m9.figshare.28639103) ; Archived: none (neither)
- Read: 2026-11-28
- Licence: article CC BY 4.0; data CC BY 4.0 (figshare metadata).
- Kept file: none. One file, "SUPPLEMENTARY INFORMATION.rar", 222 MB, too large for the brief.
- Numbers:
  - **Samples.** Historical pigments and dyes bound in **gum arabic** and in egg glair: azurite (4 grades), smalt, lapis lazuli, lead white, calcite, cinnabar, hematite, minium, orpiment, lead-tin yellow, yellow ochre, gamboge, saffron, buckthorn, malachite, verdigris, burnt umber, grape-seed black, carmine, indigo. 156 mock-ups.
  - **Substrate.** Handmade cotton/linen paper and parchment.
  - **Imaging.** Pika L, 400–1000 nm resampled at 5 nm. Pika IR+, 900–1700 nm. Averaged spectra in CSV.
  - None of murex's modern core pigments; the nearest are lapis (natural ultramarine), hematite (PR101 family) and carbon black from grape seed.
- Settles: gum arabic paint-outs on paper for natural ultramarine, red iron oxide and a vegetable carbon black. Mono-, bi- and triphasic mock-ups (layers and mixtures).
- Proposed test: murex's ultramarine, burnt sienna or red oxide, and black over a cotton paper match the averaged CSV spectra in band positions (±15 nm). Fetch with `curl -L -o si.rar https://ndownloader.figshare.com/files/56343494`, then extract only the averaged CSVs.

#### hyperdoc2025
- Citation: A. B. López-Baldomero et al., "Hyperspectral dataset of historical documents and mock-ups from 400 to 1700 nm (HYPERDOC)", Scientific Data 12 (2025) 1248. DOI 10.1038/s41597-025-05599-0. Data: figshare DOI 10.6084/m9.figshare.28319165.
- Address: https://pmc.ncbi.nlm.nih.gov/articles/PMC12267391/ (data: https://doi.org/10.6084/m9.figshare.28319165) ; Archived: http://web.archive.org/web/20250731203506/https://www.nature.com/articles/s41597-025-05599-0 (data: none)
- Read: 2026-11-28
- Licence: article CC BY-NC-ND 4.0; **data CC BY 4.0** (figshare metadata).
- Kept file: none (43.4 GB: minicubes.zip 11.7 GB, ParentCubes.zip 31.6 GB; RGB.zip 31 MB).
- Numbers: mock-ups of **inks**: iron-gall (metallo-gallate), sepia, carbon-based, and mixtures. Varying amounts of ink, some artificially aged. Supports: Paperlan handmade cotton, linen and 50/50 papers, hemp paper, goatskin parchment. VNIR 400–1000 nm and SWIR 900–1700 nm line-scan cameras, with pixel-level material annotations.
- Settles: reflectance of carbon and iron-gall inks on paper at several loads, for the ink part of aquarelle.
- Proposed test: murex's carbon ink at increasing load over paper follows the measured lightness series, with a neutral hue (|a*|, |b*| ≤ 3). Fetching means pulling 11.7 GB of minicubes; ask the owner first.

#### chsos-pigments-checker
- Citation: CHSOS (A. Cosentino), "Pigments Checker" v4/v5, free reflectance databases (UV-VIS-NIR 200–1000 nm "GorgiasUV", 350–950 nm "Gorgias", NIR 930–1690 nm).
- Address: https://chsopensource.org/products/pigments-checker/pigments-checker-4/pigments-checker-standard-pigments-list/ (example page https://chsopensource.org/cadmium-red-k-21120 ; zips https://chsopensource.org/download/2565/ "Database-Reflectance-Spectra-Pigments-acrylic-binder-on-cardboard.zip" 1.07 MB, https://chsopensource.org/download/27899/ 1.46 MB, https://chsopensource.org/download/24902/ 92 KB) ; Archived: http://web.archive.org/web/20260112083756/https://chsopensource.org/products/pigments-checker/pigments-checker-4/pigments-checker-standard-pigments-list/ (example: http://web.archive.org/web/20241204091306/https://chsopensource.org/cadmium-red-k-21120/)
- Read: 2026-11-28
- Licence: none stated. Not downloaded.
- Kept file: none
- Numbers: about 75 Kremer pigments (list on the page, including titanium white K-46200, lamp black K-47250, phthalo blue K-23050, phthalo green K-23000, viridian K-44250, cobalt cerulean K-45730, ultramarine K-45000, alizarin K-23611, cadmium red K-21120, cadmium yellow K-21010, burnt sienna 40430). They are in an **acrylic** binder on cardboard, per the zip's file name. No quinacridone.
- Settles: acrylic paint-outs only, so not watercolour.
- Proposed test: none for aquarelle beyond cross-checking band positions.

#### infra-art-watercolours
- Citation: I. M. Cortea, "INFRA-ART spectral data collections: watercolors", INFRA-ART blog, 2025-10-22.
- Address: https://blog.infraart.inoe.ro/2025/10/22/infra-art-spectral-data-collections-watercolors (database: https://infra-art.eu/database-index/spectral-database-index?alternativeName=watercolor&isAdvancedSearch=true) ; Archived: none
- Read: 2026-11-28
- Licence: the INFRA-ART library is CC BY-NC-SA 4.0 (per a search snippet, not verified on the site).
- Kept file: none
- Numbers: about 98 watercolour and gouache samples: Nevskaya Palitra White Nights (24), W&N Professional (20), Cotman (42), Designers Gouache (12). **ATR-FTIR and XRF only; no visible reflectance.** Useful because it gives the CI names of each paint, e.g.:
  - W&N Professional: French Ultramarine PB29, Cerulean PB35, Winsor Blue PB15, Viridian PG18, Alizarin PR83, Permanent Rose PV19, Burnt Sienna PR101, Ivory Black PBk9.
  - Designers Gouache: Cobalt Blue PB28, Zinc White PW5.
- Settles: which pigment a W&N paint uses, for matching the NTU W&N set to CI names.
- Proposed test: none.

#### colourlex
- Citation: ColourLex, pigment pages (e.g. "Ultramarine").
- Address: https://colourlex.com/project/ultramarine/ ; Archived: none
- Read: 2026-11-28
- Licence: no site-wide licence on the page; images credited individually.
- Kept file: none
- Numbers: shows a FORS spectrum as an image, credited "Spectra by A. Cosentino, CHSOS". Binder not stated; not downloadable.
- Settles: nothing beyond cosentino2014.
- Proposed test: none.

---

### Not found or not verified

- **Wet watercolour spectra.** No dataset or paper was found that measures a watercolour (or gouache, or ink) wet and again dry. Every set above is dry. How a wash darkens and shifts while wet has no published reference found here.
- **K and S of watercolour per pigment, tabulated.**
  - None found. Tominaga 2016 has the method but shows K and S only as reflectance curves in figures.
  - Curtis et al., "Computer-Generated Watercolor" (SIGGRAPH 1997) gives RGB-only KM coefficients. The PDF (https://maverick.inria.fr/Members/Cyril.Soler/DEA/NonPhotoRealisticRendering/Papers/p421-curtis.pdf) returned 503 and could not be read. A search snippet says the coefficients came from a "unit thickness" over white and black backgrounds, and Pigmento calls them a "three-wavelength" set. Not verified.
- **Kremer Pigmente's own reflectance data.** None found published by Kremer. Kremer pigments appear only through CHSOS (cosentino2014, Pigments Checker) and Deborah 2022.
- **Asadi 2020 data files.** The hosts are gone (see asadi2020); the Wayback snapshots could not be opened from this session.
- **MoWCReS contents.** The pigment list, brands and the meaning of "Normal/Transparency" sit behind a login (see ifac-mowcres).
- **Budsberg, Greenberg, Marschner**, Cornell PCG technical report PCG-06-02 (2006), "BGM06": appearance of artists' paints (acrylic, casein, distemper, encaustic, **gouache**, oil, tempera, **watercolour**) over six months, 168 samples on primed canvas, 350–700 nm at 10 nm, with "spectra.zip". The Cornell pages returned 503 or redirect to bowers.cornell.edu, whose data page does not list it. The PDF has a snapshot at http://web.archive.org/web/20250616013522/https://www.graphics.cornell.edu/pubs/2006/BGM06.pdf; no snapshot of spectra.zip was found. Not verified.
- **Okumura 2005 thesis** is "withdrawn" on RIT's repository. The data zip still exists (okumura2005-paint-research).
- **Kogou et al. 2015** (arXiv:1508.02343, Chinese export watercolours). Its reference samples are pigments in **animal glue** at 1, 3 and 10 layers on watercolour paper. Only −log(K/S) plots, no data released.
- **Mixbox** (Sochorová & Jamriška 2021) was reported as CC BY-NC in timbrinded/watercolour#42 (https://github.com/timbrinded/watercolour/issues/42; Archived: none). It is a model, not measurements. Not checked further.
- **Zenodo, figshare and Mendeley searches** for "watercolour reflectance dataset" found nothing else with gum arabic paint-outs of modern pigments. "Data in Brief" turned up nothing on watercolour.
- **The "IFAC-CNR FORS … Cosentino" pairing in the brief is a conflation.** The IFAC FORS database (Aldrovandi, Casini, Picollo et al.) has no gum arabic. Cosentino's database (CHSOS, cosentino2014) is the one with gum arabic, and it cites the IFAC database as its model.

## Openly licensed photographs and scans of wet media, for murex.aquarelle

Gathered 2026-11-28. Every licence below was read on the file's own page (Wikimedia Commons file description page) or, for the Metropolitan Museum of Art, from the object record of its Open Access API (`isPublicDomain: true`, which is the Met's Open Access flag: images released under CC0, https://www.metmuseum.org/openaccess). Images are in `references/photos/`, in Git LFS.

Notes on how they were obtained:

- From this machine Wikimedia's upload server answered almost every request with HTTP 429 (rate limit for the shared address). Where the original could not be fetched, the largest standard Wikimedia thumbnail that came through was kept; the entry says so ("thumbnail"). The original can be fetched later from the "Original" address.
- Flickr refused every download from this machine ("Rate limited - CIDR range blocked"), so no Flickr photograph is kept, though some openly licensed ones were found (see the end).
- The Art Institute of Chicago serves CC0 scans but only whole images up to 3000 px from this machine (its IIIF server refuses crops); none was kept, the Met's equivalents being sharper.
- Scales (px/mm) are estimates from the sheet size in the museum record and the width the sheet takes in the image; they are good to about 10%.
- Museum scans are evenly lit, colour-managed reproductions; photographs by individuals (Commons) are phone or camera shots, often sharpened or saturated: they give shapes and relative contrasts, not absolute colour.

#### 10-sargent-man-and-pool-drybrush-wet-in-wet.jpg
- Title: Man and Pool, Florida (1917), John Singer Sargent; Met accession 50.130.62
- Author: John Singer Sargent (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/12078 ; Original: https://images.metmuseum.org/CRDImages/ad/original/DT243231.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/; https://www.metmuseum.org/openaccess). No attribution required; credit "The Metropolitan Museum of Art, Gift of Mrs. Francis Ormond, 1950" is customary.
- Shows: the whole sheet, 34.8 x 53.3 cm, watercolour, gouache and graphite on white wove paper (paper maker not named), 3811 x 2493 px, about 7 px/mm. Top third: brown and green strokes dragged over a rough paper, broken by white specks where the brush skipped the troughs (dry brush). Lower half: a pool painted wet in wet, blues, greens and yellows fused with soft edges, a few hard back-edges where a wash met a drier one, and opaque lavender gouache marks on top. Even museum lighting, colour usable.
- Settles: 7 (dry brush: fraction of white specks against stroke darkness, speck size, their alignment with the paper's tooth, at ~7 px/mm); 3 (wet-in-wet: width of soft transitions between colours, several mm); 12 in part (opaque strokes over transparent wash).

#### 11-homer-shore-and-surf-sky-edges-lifting.jpg
- Title: Shore and Surf, Nassau (1899), Winslow Homer; Met accession 10.228.5
- Author: Winslow Homer (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/11138 ; Original: https://images.metmuseum.org/CRDImages/ad/original/DP-21450-001.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/). No attribution required; credit "The Metropolitan Museum of Art, Amelia B. Lazarus Fund, 1910" customary.
- Shows: whole sheet with its edges, 37.9 x 54.3 cm, watercolour and graphite on off-white wove paper, 4000 x 2814 px, about 7 px/mm. The grey sky is built of overlapping flat washes dried with hard edges: each dried patch has a thin darker rim (edge darkening), and light patches that look lifted or scrubbed back (inferred from their look; the Met's record names no technique) show the paper texture and a soft or ragged border. Sea: transparent blue washes, white of the paper reserved and opaque white touches for foam; dark rocks in the foreground, some granulating. Even lighting.
- Settles: 2 (edge darkening: rim width and the darkening ratio against the patch interior, in the sky, e.g. around x 2900-3900, y 150-800); 6 (lifting: lifted patches in the sky, contrast lost and edge softness); 8 (several glazes stacked in the sky); 5 a little (rocks).

#### 12-homer-hurricane-bahamas-layered-washes.jpg
- Title: Hurricane, Bahamas (1898), Winslow Homer; Met accession 10.228.7
- Author: Winslow Homer (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/11124 ; Original: https://images.metmuseum.org/CRDImages/ad/original/DP-17779-001.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: whole sheet with its edges, 36.7 x 53.5 cm, watercolour and graphite on off-white wove paper, 4000 x 2763 px, about 7 px/mm. Grey sky of two or three superposed washes, each with a hard, slightly darker edge, light gaps of paper left between them; palm fronds as single wet strokes with split, dragged ends; flat brown and grey roof washes. Even lighting.
- Settles: 1 (nearly flat washes on the roofs: uniformity and mottling); 2 (rims of the sky washes); 8 (glazing: optical density of one, two and three overlapping grey washes, which should add); 7 a little (split ends of the frond strokes).

#### 16-nankai-bamboo-rainy-day-sumi-tones.jpg
- Title: Window onto Bamboo on a Rainy Day (first half 18th century), Gion Nankai; Met accession 2015.300.154
- Author: Gion Nankai (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/53450 ; Original: https://images.metmuseum.org/CRDImages/as/original/DP-10807-115.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/). Credit customary: "The Metropolitan Museum of Art, Mary Griggs Burke Collection, Gift of the Mary and Jackson Burke Foundation, 2015".
- Shows: the whole hanging scroll with its mounting and a grey scale beside it; the painting, ink on paper, 133.7 x 58 cm, takes about 3000 px of the 4000 px height, so only about 2.2 px/mm. Bamboo leaves each laid in one stroke of sumi ink, at three or four dilutions (near black to pale grey), the dark ones over the pale ones; the pale leaves have soft, slightly bled edges, the dark ones crisp edges and streaks of dry brush (the white of the paper showing through where the brush ran dry). A grey scale is in the photograph (useful to calibrate tones).
- Settles: 9 (sumi ink: tone of a single stroke against dilution, the darkening where strokes overlap, the edge profile of a pale wet stroke against a dark drier one; stroke widths of 5-15 mm are measurable, finer feathering is not at this scale); 7 (dry-brush streaks in ink).

#### 18-baumann-penmanship-quill-swelling-lines.jpg
- Title: Specimens of Penmanship after Jan van de Velde and other Calligraphy Books (ca. 1620), Conrad Baumann; Met accession 30.58.3
- Author: Conrad Baumann (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/345657 ; Original: https://images.metmuseum.org/CRDImages/dp/original/DP372397.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: one opening of a manuscript on vellum (book 23.5 x 34.5 cm), 3903 x 2874 px, roughly 11 px/mm: German fraktur lines and large flourishes in brown ink (the record says only "manuscript on vellum"; the ink is not named), presumably with a quill; strokes swell from hairlines to broad shades and taper again, with dots and spirals; a drawn hand holding a quill. Vellum, not paper: no feathering. Even lighting.
- Settles: 10 (dip pen / quill: line width as a function of direction and pressure along a flourish, hairline width, the length of the swell and taper; the nearest thing found to flex-nib shading. No railroading is visible: a quill does not split into two tines like a steel flex nib).

#### 19-rembrandt-two-cottages-iron-gall-pen.jpg
- Title: Two Cottages (ca. 1636), Rembrandt van Rijn; Met accession 1975.1.801 (Robert Lehman Collection)
- Author: Rembrandt van Rijn (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/459318 ; Original: https://images.metmuseum.org/CRDImages/rl/original/DP359035.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: the whole sheet, 15 x 19.1 cm, pen and brown ink ("gallnut ink, possibly only partially") on paper, 3893 x 3060 px, about 20 px/mm. Fast pen lines of every width (fine scribbles to broad, ink-loaded strokes), blots, and in the dense thatch a brown halo around the strokes where ink spread into the paper and the iron gall has browned it. Paper toned beige, its texture visible.
- Settles: 10 (dip-pen line width distribution, ink pooling at stroke ends and turns, blots); 9 (the halo width beside dense strokes on an unsized/old paper: a measure of ink spreading, at 20 px/mm).

#### 20-cezanne-watermelon-glazing.jpg
- Title: Still-Life with a Watermelon and Pomegranates (1900-1906), Paul Cézanne; Met accession 2001.202.1
- Author: Paul Cézanne (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/343735 ; Original: https://images.metmuseum.org/CRDImages/dp/original/DT4962.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: the whole sheet on a dark ground, 31.4 x 48.8 cm, watercolour over graphite on laid paper, 3811 x 2549 px, about 7.5 px/mm. Cézanne's late method: many small transparent strokes of blue, green, ochre and red laid over dried ones, each keeping a hard edge, so that colour builds by superposition; white paper reserved for the lights. Even lighting.
- Settles: 8 (glazing: colour of two or three overlapping transparent strokes against each alone, which a Kubelka-Munk layer model should predict; hard edges of each stroke, with slight edge darkening); 2.

#### 21-sargent-brook-and-meadow-gouache-over-watercolour.jpg
- Title: Brook and Meadow (ca. 1907), John Singer Sargent; Met accession 50.130.80j
- Author: John Singer Sargent (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/12053 ; Original: https://images.metmuseum.org/CRDImages/ad/original/DT235921.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: the sheet on a white mount, 35.6 x 50.8 cm, watercolour, gouache and graphite on white wove paper, 3811 x 2651 px, about 7 px/mm. Stones painted in opaque lavender-white gouache over dark transparent washes: the gouache covers what is under it, and where dragged it breaks on the paper's tooth; dark transparent water with hard edges; dry-brush grass.
- Settles: 12 (opaque gouache over transparent watercolour: how far the under-layer shows through a gouache stroke, broken edges of dragged gouache); 7.

#### 22-rodin-nude-holding-foot-bloom-tide-lines.jpg
- Title: Nude female figure holding left foot (1900-1912), Auguste Rodin; Met accession 13.164.6
- Author: Auguste Rodin (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/339720 ; Original: https://images.metmuseum.org/CRDImages/dp/original/DP216717.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: the whole sheet, 49.4 x 31.9 cm, graphite and watercolour on paper, 2495 x 3860 px, about 7.5 px/mm. A pale blue-grey and ochre background wash laid very wet and left to dry: hard tide lines where puddles dried, and at the lower right (around x 2050-2350, y 2800-3100) a bloom: a drop that spread into a drying wash and dried with a feathered, darker scalloped rim around a paler centre, a blue speck at its source. The figure is a flat brown wash with darker edges. Even lighting.
- Settles: 4 (backrun / bloom: diameter about 4 cm, rim width, scalloping of the rim, the paler interior); 2 (tide lines and edge darkening of puddled washes).

#### 23-rodin-standing-nude-flat-puddled-wash.jpg
- Title: Standing Female Nude (n.d.), Auguste Rodin; Met accession 67.187.31
- Author: Auguste Rodin (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/339724 ; Original: https://images.metmuseum.org/CRDImages/dp/original/DP808101.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: the whole sheet, image 34.4 x 21.5 cm, watercolour over graphite on a beige paper, 2462 x 3798 px, about 10 px/mm. The figure is one flat ochre wash laid inside a pencil contour and left to dry: mottled with darker blotches where the wash pooled, and a slightly darker line along its edge in places. Even lighting.
- Settles: 1 (flat wash: mottling amplitude and blotch size of a single puddled wash on smooth paper); 2 (edge darkening of a single wash, weaker than in 11 and 22).

#### 25-alsatian-textile-design-flat-gouache.jpg
- Title: Textile Design with Scattered Ovals (1840), anonymous, Alsatian; Met accession 1978.671.5(18.6)
- Author: anonymous Alsatian designer (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/709039 ; Original: https://images.metmuseum.org/CRDImages/dp/original/DP889396.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: a small design sheet, 6.3 x 6.5 cm, gouache, 1299 x 1271 px, about 18 px/mm. A flat opaque pink ground, maroon ovals with crisp edges, stippled darker dots, opaque white highlights with brush marks, black outlines. Even lighting.
- Settles: 12 (gouache flat opaque colour: uniformity of a flat gouache field, sharpness of its edge, brush ridges in the thick white).

#### 27-bada-shanren-album-brush-ink-on-paper.jpg
- Title: Album of miscellaneous paintings (leaf with deer, and its facing inscription), Bada Shanren (Zhu Da); Met accession 54.34a-l
- Author: Bada Shanren (artwork); photograph by The Metropolitan Museum of Art
- Address: https://www.metmuseum.org/art/collection/search/51803 ; Original: https://images.metmuseum.org/CRDImages/as/original/DP154493.jpg
- Read: 2026-11-28
- Licence: Public domain artwork, Met Open Access image, CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: an opening of the album, each leaf 19.7 x 15.2 cm, ink wash on paper, 3841 x 2939 px, about 11 px/mm. Left: brush calligraphy in black ink, strokes with soft, slightly fuzzy edges where the ink crept into the paper's fibres; the laid lines of the paper are visible. Right: deer, pine and rocks in dry brush and pale ink washes. Slightly warm toned paper, even lighting.
- Settles: 9 (ink on absorbent paper: edge softness and halo of a brush stroke at ~11 px/mm, stroke width; dry-brush ink texture); 7.

#### 01-ultramarine-granulating-vs-concentrated.png
- Title: File:Bleu outremer, granulant à droite, concentré à gauche.png ("Ultramarine blue, granular on the right, concentrated on the left")
- Author: Les.aqua (Wikimedia Commons user, own work, 19 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Bleu_outremer,_granulant_%C3%A0_droite,_concentr%C3%A9_%C3%A0_gauche.png ; Original: https://upload.wikimedia.org/wikipedia/commons/1/14/Bleu_outremer%2C_granulant_%C3%A0_droite%2C_concentr%C3%A9_%C3%A0_gauche.png (1554 x 1557). Kept: Wikimedia thumbnail, 1280 x 1282 (https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Bleu_outremer%2C_granulant_%C3%A0_droite%2C_concentr%C3%A9_%C3%A0_gauche.png/1280px-Bleu_outremer%2C_granulant_%C3%A0_droite%2C_concentr%C3%A9_%C3%A0_gauche.png); the original was refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/deed.en). No attribution required.
- Shows: a close-up photograph of two ultramarine swatches side by side on watercolour paper (paper not named, brand of paint not named). Left: a concentrated, nearly even wash, graded lighter downwards, with a faint texture. Right: a dilute wash where the pigment has settled into the paper's grain: a network of dark pigment-filled hollows and pale ridges, mesh size a few tenths of a millimetre to about a millimetre (no scale in the picture). The blue is very saturated and probably clipped in the camera; take relative contrast, not colour.
- Settles: 5 (granulation: contrast between the granulated swatch and the smooth one, the spatial frequency of the granulation and its correlation with the paper's grain; also granulation against dilution, since the right swatch is the more dilute); 1 (graded wash on the left).

#### 02-mars-black-granulation.png
- Title: File:Lunar Black.png (no description on the page; on fr.wikipedia "Aquarelle" captioned as Mars black, PBk 11, which granulates)
- Author: Les.aqua (Wikimedia Commons user, own work, 19 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Lunar_Black.png ; Original: https://upload.wikimedia.org/wikipedia/commons/d/d7/Lunar_Black.png (1727 x 1628). Kept: thumbnail 960 x 905 (https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Lunar_Black.png/960px-Lunar_Black.png); original refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/deed.en).
- Shows: a close-up of a black watercolour wash (the page names no paint; the file name matches Daniel Smith's "Lunar Black", and fr.wikipedia's caption calls it Mars black, PBk 11, an iron oxide; paper not named) with a very strong granular pattern: clumps of pigment in the paper's hollows, white ridges between, a darker pool lower left with two light specks. The photograph is very contrasty (probably processed); no scale.
- Settles: 5 (an extreme of granulation and flocculation to set the upper bound of the effect; clump size against the paper's grain).

#### 03-two-types-of-wash.png
- Title: File:Deux types de lavis.png ("Two types of wash")
- Author: Les.aqua (Wikimedia Commons user, own work, 22 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Deux_types_de_lavis.png ; Original: https://upload.wikimedia.org/wikipedia/commons/d/df/Deux_types_de_lavis.png (1505 x 980). Kept: thumbnail 960 x 625 (https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Deux_types_de_lavis.png/960px-Deux_types_de_lavis.png); original refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/).
- Shows: a close-up of two crimson washes on a textured white watercolour paper, a strip of bare paper between them; no description, no scale, paint and paper not named. Left: a graded wash, dark at the top fading to pale pink at the bottom, the pigment diffusing downwards in streaks and soft fingers (laid wet in wet), with dark specks of undissolved pigment; the pale lower edge is ragged and hard. Right: a nearly flat, darker wash with mottling and a straight hard left edge along the white strip. Paper texture visible in both. Even daylight.
- Settles: 1 (flat against graded wash: the tone profile down the left wash, mottling amplitude of the right one); 3 (soft diffusion fingers at the dark-to-light transition); 2 (edge of the right wash along the white strip).

#### 05-masking-fluid-effects.png
- Title: File:Effets de drawing gum.png ("Effects of drawing gum", i.e. masking fluid)
- Author: Les.aqua (Wikimedia Commons user, own work, 22 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Effets_de_drawing_gum.png ; Original: https://upload.wikimedia.org/wikipedia/commons/7/75/Effets_de_drawing_gum.png (1058 x 919). Kept: thumbnail 960 x 834 (https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Effets_de_drawing_gum.png/960px-Effets_de_drawing_gum.png); original refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0). Attribution required: "Les.aqua, CC BY 4.0, via Wikimedia Commons", link to the licence, and say if changed.
- Shows: a close-up of a greyish-blue wash on a white textured watercolour paper over areas that were masked with drawing gum and then rubbed off: the masked shapes are white with crisp, irregular, slightly ragged edges, some islands of blue inside them; the wash itself shows the paper's texture. No scale; paint and paper not named.
- Settles: 13 (masking fluid: edge sharpness of the reserved whites, compared with a painted edge; whether pigment creeps under the mask).

#### 06-fountain-pen-feathering-levenger.jpg
- Title: File:Fountain pen ink Feathering example with Levenger Cobalt Blue Ink.jpg
- Author: Northwalker (Wikimedia Commons user, own work; uploaded 7 February 2019)
- Address: https://commons.wikimedia.org/wiki/File:Fountain_pen_ink_Feathering_example_with_Levenger_Cobalt_Blue_Ink.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/0/01/Fountain_pen_ink_Feathering_example_with_Levenger_Cobalt_Blue_Ink.jpg (1773 x 783). Kept: thumbnail 1280 x 565 (https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Fountain_pen_ink_Feathering_example_with_Levenger_Cobalt_Blue_Ink.jpg/1280px-Fountain_pen_ink_Feathering_example_with_Levenger_Cobalt_Blue_Ink.jpg); original refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/deed.en).
- Shows: the word "feathering" written in Levenger Cobalt Blue fountain-pen ink on ruled notebook paper (blue rules, red margin), scanned or photographed flat. Every stroke is fringed with fine hair-like spurs where the ink ran along the paper's fibres; dots have ragged outlines. The rule spacing (about 270 px in the kept image) gives the scale once the ruling is known (US wide rule 8.7 mm, college rule 7.1 mm: about 31 or 38 px/mm). Pen and nib width not named.
- Settles: 9 and 10 (feathering on cheap absorbent paper: spur length and density against stroke width, the ratio of the feathered outline to the nominal line width; fountain-pen ink on uncoated paper).

#### 07-black-ink-paper-chromatography.jpg
- Title: File:BlackInkChromatography.jpg ("Chromatography of black ink on paper, suspended over a glass of water")
- Author: Oscar (Wikimedia Commons user, own work, 27 June 2008)
- Address: https://commons.wikimedia.org/wiki/File:BlackInkChromatography.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/b/b6/BlackInkChromatography.jpg (2816 x 2112). Kept: thumbnail 1920 x 1440 (https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/BlackInkChromatography.jpg/1920px-BlackInkChromatography.jpg); original refused (HTTP 429).
- Read: 2026-11-28
- Licence: CC BY-SA 3.0 Unported (https://creativecommons.org/licenses/by-sa/3.0/), or GFDL 1.2 or later, at the user's choice. Attribution required: "Oscar, CC BY-SA 3.0, via Wikimedia Commons". ShareAlike: a derivative image (a crop, an annotated figure) must be shared under CC BY-SA 3.0 or a compatible licence; storing and redistributing the file unchanged with its licence is fine.
- Shows: a strip of absorbent paper (kitchen or filter paper) hanging into a glass of water, photographed through the glass, slightly blurred, yellow cast. A black ink dot (water-soluble marker or pen, not named) near the bottom; water has climbed past it, carrying the dyes: a red zone with a sharp, fingered green and black front, and beyond it the water front itself, pale and irregular. No scale.
- Settles: 10 (fountain-pen / dye-ink chromatography: the order of the dyes, a darker front at the leading edge, the fingered shape of a wetting front on fibrous paper); 2 (the same edge accumulation as at the rim of a drying wash, driven by flow).

#### 08-iron-gall-ink-writing-darkening.jpg
- Title: File:Eisengallustinte selbstgemacht schriftbild.jpg (self-made iron gall ink, writing sample)
- Author: Lord Skunk (Wikimedia Commons uploader, own work, 3 October 2006)
- Address: https://commons.wikimedia.org/wiki/File:Eisengallustinte_selbstgemacht_schriftbild.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/6/68/Eisengallustinte_selbstgemacht_schriftbild.jpg (2330 x 1003). Kept: thumbnail 1920 x 827 (https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Eisengallustinte_selbstgemacht_schriftbild.jpg/1920px-Eisengallustinte_selbstgemacht_schriftbild.jpg).
- Read: 2026-11-28
- Licence: Public domain (released by the author worldwide; "for any purpose" where that is not possible).
- Shows: left, a dip pen with a broad (italic) nib on a glass rest, a bottle of the ink and a strip of brown paper; right, four photographs of the word "Wikipedia" written in blackletter with the broad nib on that paper, taken immediately, after 8 s, 40 s and 3 min: wet ink stands glossy on the paper at first, then sinks in and darkens. Small, camera flash, no scale.
- Settles: 10 (broad dip-nib strokes: thick/thin contrast of an italic nib against direction; ink pooling in wet strokes and how its gloss and tone change as it dries, over minutes). Low resolution: shapes only.

#### 09-cellulose-paper-wash.png
- Title: File:Papier aquarelle en cellulose.png ("Un papier aquarelle 300 grammes, 100% cellulose")
- Author: Les.aqua (Wikimedia Commons user, own work, 21 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Papier_aquarelle_en_cellulose.png ; Original: https://upload.wikimedia.org/wikipedia/commons/6/66/Papier_aquarelle_en_cellulose.png (1781 x 2048). Kept: thumbnail 1280 x 1472 (https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Papier_aquarelle_en_cellulose.png/1280px-Papier_aquarelle_en_cellulose.png).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/deed.en).
- Shows: a flat ochre wash on a 300 g/m², 100% cellulose (wood-pulp) watercolour paper: the wash has dried blotchy, pale and dark patches a few millimetres to a centimetre across, the paper's grain visible throughout. No scale.
- Settles: 1 (a "flat" wash on a cheap paper: mottling amplitude and patch size, against the smoother washes on cotton paper in 03 and the museum sheets); paper's effect on uniformity.

#### 13-cotton-paper-fine-grain-wash.png
- Title: File:Papier aquarelle 100% coton, grain fin.png (description: "Détail"; used on fr.wikipedia "Papier aquarelle")
- Author: Les.aqua (Wikimedia Commons user, own work, 21 January 2025)
- Address: https://commons.wikimedia.org/wiki/File:Papier_aquarelle_100%25_coton,_grain_fin.png ; Original: https://upload.wikimedia.org/wikipedia/commons/c/ca/Papier_aquarelle_100%25_coton%2C_grain_fin.png (1359 x 1433). Kept: thumbnail 1280 x 1350 (https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Papier_aquarelle_100%25_coton%2C_grain_fin.png/1280px-Papier_aquarelle_100%25_coton%2C_grain_fin.png).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (http://creativecommons.org/publicdomain/zero/1.0/deed.en).
- Shows: bare 100% cotton cold-pressed ("grain fin") watercolour paper in raking light, no paint: the irregular hills and hollows of the surface. No scale (cold-pressed grain is typically ~0.5-1 mm).
- Settles: none of the wanted items directly; it is the surface that granulation (5) and dry brush (7) read: the height field a paper model can be compared with (shape and anisotropy of the grain).

#### 15-felt-pen-chromatography.png
- Title: File:Chromatographieren-eines-Filzstiftes.png ("Chromatographie eines braunen Filzstiftes auf Filterpapier")
- Author: Stefan Kleyer (Wikimedia Commons user Lerothas, own work, 28 November 2018)
- Address: https://commons.wikimedia.org/wiki/File:Chromatographieren-eines-Filzstiftes.png ; Original: https://upload.wikimedia.org/wikipedia/commons/d/d2/Chromatographieren-eines-Filzstiftes.png (2000 x 1067). Kept: thumbnail 1920 x 1024 (https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Chromatographieren-eines-Filzstiftes.png/1920px-Chromatographieren-eines-Filzstiftes.png).
- Read: 2026-11-28
- Licence: CC0 1.0 Universal Public Domain Dedication (https://creativecommons.org/publicdomain/zero/1.0/deed.en).
- Shows: radial paper chromatography of a brown water-based felt-tip pen on a filter-paper disc fed by a paper wick from the centre, two photographs: just after the wick touches water (a brown ring with radial streaks, its outer edge darker), and at the end (dyes separated into a violet-blue centre, an orange-brown ring with radial streaks, and a thin cyan outer rim at the front). Phone photographs at an angle, no scale.
- Settles: 11 and 10 (water-based marker ink: which dyes run ahead, a dark rim at the wetting front, radial streaking from the paper's fibres); 2 (front accumulation).

#### 24-copic-marker-sketch-church.jpg
- Title: File:Sketch-butovo-091300.jpg (drawing of the Church of the Nativity of Christ in Chernevo); from Flickr "sketch-butovo-091300"
- Author: Alexander Lyubavin (Flickr user alubavin, https://www.flickr.com/photos/santea/11292233543/), uploaded to Commons 30 September 2016
- Address: https://commons.wikimedia.org/wiki/File:Sketch-butovo-091300.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/9/95/Sketch-butovo-091300.jpg (4032 x 3024, 8.3 MB, over the 4000 px limit). Kept: standard thumbnail 3840 x 2880 (https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Sketch-butovo-091300.jpg/3840px-Sketch-butovo-091300.jpg).
- Read: 2026-11-28
- Licence: CC BY 2.0 (https://creativecommons.org/licenses/by/2.0). Attribution required: "Alexander Lyubavin (alubavin), CC BY 2.0, via Wikimedia Commons", link to the licence, indicate changes.
- Shows: a pocket sketchbook open on a dark surface, photographed from above in soft light, with the tools beside it: three Copic alcohol markers (C1 cool grey, R02, E04) and a 0.7 mm black gel pen. The right page is a sketch of a church in gel-pen line and marker: chisel-tip strokes of grey, orange and brick red with visible stroke ends, darker bands where two passes of the same marker overlap, slight streaks within a stroke, and soft but not feathered edges on the cream sketchbook paper; the left page shows a pencil sketch and faint bleed-through. A page about 9 cm wide takes about 1850 px: roughly 20 px/mm. The markers are named on their barrels.
- Settles: 11 (alcohol-marker strokes: darkening of overlaps of one, two and three passes of the same colour, streaks along a stroke, stroke-end shapes of a chisel tip, edge softness on sketch paper); 10 a little (gel pen line).

#### 28-lamy-fountain-pen-nib-widths-scan.jpg
- Title: File:Lamy Fountain pen writing samples 2.jpg
- Author: Francis Flinch (Wikimedia Commons user, own work, 2 August 2013)
- Address: https://commons.wikimedia.org/wiki/File:Lamy_Fountain_pen_writing_samples_2.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/6/6d/Lamy_Fountain_pen_writing_samples_2.jpg (2084 x 1870, scanned at 600 dpi). Kept: thumbnail 1920 x 1723 (https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Lamy_Fountain_pen_writing_samples_2.jpg/1920px-Lamy_Fountain_pen_writing_samples_2.jpg), so about 21.7 px/mm (the original is 23.6 px/mm).
- Read: 2026-11-28
- Licence: CC BY-SA 3.0 Unported (https://creativecommons.org/licenses/by-sa/3.0) or GFDL 1.2 or later, at the user's choice. Attribution required: "Francis Flinch, CC BY-SA 3.0, via Wikimedia Commons". ShareAlike applies to derivatives.
- Shows: a flatbed scan (Canon CanoScan 4400F, 600 dpi) of "Wikipedia" and "Lamy" written with seven interchangeable Lamy Z 50 steel nibs, EF, F, M, B and 1.1, 1.5, 1.9 mm italic stubs, in a Lamy Studio pen with Lamy T 10 washable blue cartridge ink, on white paper (not named). Each line labelled with its nib. Ink shading visible (darker where ink pooled at stroke ends and turns, lighter in fast strokes), especially with the stubs; no feathering. Scanner lighting, colour reliable.
- Settles: 10 (fountain-pen line width per nib, thick/thin ratio of the stubs against direction, ink shading along a stroke and pooling at stroke ends, at a known scale; with 06, the same kind of ink on a good and a poor paper).

#### 29-copperplate-oblique-pen-sample.jpg
- Title: File:Sample of Copperplate Script with an Oblique Penholder.jpg
- Author: Swchuck (Wikimedia Commons user, own work, 25 January 2014)
- Address: https://commons.wikimedia.org/wiki/File:Sample_of_Copperplate_Script_with_an_Oblique_Penholder.jpg ; Original: https://upload.wikimedia.org/wikipedia/commons/a/a8/Sample_of_Copperplate_Script_with_an_Oblique_Penholder.jpg (1500 x 1000). Kept: thumbnail 1280 x 853 (https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Sample_of_Copperplate_Script_with_an_Oblique_Penholder.jpg/1280px-Sample_of_Copperplate_Script_with_an_Oblique_Penholder.jpg).
- Read: 2026-11-28
- Licence: CC BY-SA 3.0 Unported (https://creativecommons.org/licenses/by-sa/3.0/deed.en). Attribution required: "Swchuck, CC BY-SA 3.0, via Wikimedia Commons". ShareAlike applies to derivatives.
- Shows: a sheet of copperplate script in black ink with offhand flourishes, written with a pointed flexible steel nib in an oblique holder, which lies on the sheet; photographed at an angle in warm light (perspective, no scale). Hairlines and swelled shades are clearly distinct; individual shades are too small to show railroading at this resolution.
- Settles: 10 (flex-nib shading: the ratio of shade to hairline width and the length of the swell, roughly, after correcting perspective). Weak: an illustration more than a measurement.

### By wanted item

1. Flat and graded wash: 03 (graded and flat side by side, close-up), 09 (flat wash mottling on cellulose paper), 23 (one puddled flat wash, museum scan), 12 (roof washes).
2. Edge darkening: 11 (sky, best), 12, 22 (tide lines), 20, 03; 07 and 15 show the same front accumulation in chromatography.
3. Wet-in-wet: 10 (pool), 03 (left), 16 (pale ink leaves).
4. Backrun / bloom: 22 (one clear bloom with a scalloped dark rim, ~4 cm, at ~7.5 px/mm). Only one example.
5. Granulation: 01 (ultramarine granulating beside the same pigment concentrated), 02 (Mars black, extreme); 10 and 11 weakly. No earth pigment beside a smooth staining pigment on one sheet.
6. Lifting: 11 (lifted patches in Homer's sky). No deliberate lifted highlight in a swatch.
7. Dry brush on rough paper: 10 (best), 21, 16 and 27 (dry-brush ink).
8. Glazing: 20 (Cézanne), 12, 11.
9. Ink feathering, sumi: 06 (fountain-pen feathering on notebook paper), 19 (halo of iron-gall ink), 27 (brush calligraphy on absorbent paper), 16 (sumi tones). No close-up of sumi on xuan with bleeding.
10. Dip pen, fountain pen, chromatography: 18 (quill swelling lines), 19 (pen lines), 08 (broad dip nib, drying), 29 (pointed flex nib, weak), 28 (fountain-pen nib widths at known scale), 07 and 15 (ink chromatography).
11. Felt-tip markers: 24 (alcohol markers, overlaps and streaks), 15 (water-based felt-tip dyes).
12. Gouache: 25 (flat opaque gouache), 21 and 10 (gouache over watercolour).
13. Salt, masking fluid, alcohol: 05 (masking fluid) only.

### Wanted but not found

- Salt texture in a wash: no openly licensed photograph found on Commons or among the open-access museum collections searched (Met, AIC). Commons searches for "watercolor salt" give salt crystals and salt prints.
- Alcohol drops in a wash (watercolour), and alcohol-ink blooms: nothing found.
- Granulation of an earth pigment (burnt sienna, raw umber) next to a smooth staining pigment (phthalo, quinacridone) on one sheet: not found; 01 and 02 cover ultramarine and an iron-oxide black only.
- A lifted highlight as a controlled test (swatch with a lifted stripe or spot): not found; only Homer's lifted sky (11).
- Dip-pen railroading (a flex nib's two tines leaving two lines when the ink cannot follow): not found. The pointed-pen sample (29) is too small and oblique; historic quill work (18) cannot railroad.
- Sumi ink on xuan / rice paper with visible bleeding and feathering, at close range: not found in a usable licence and scale. Museum Chinese and Japanese ink paintings are on sized paper or silk and photographed whole (16: 2.2 px/mm); 27 is the nearest (brush strokes on absorbent paper at 11 px/mm, little bleeding).
- Water-based felt-tip marker streaks and overlaps on paper (as opposed to its chromatography): not found; 24 shows alcohol markers.
- Gouache swatches (flat opaque swatch with known paint): not found on Commons (the gouache category holds photographs of pots and palettes); 25 is a museum design sheet.
- A watercolour swatch chart (named paints, named paper): none on Commons; Flickr has some (below) but could not be downloaded.

### Found but not downloaded (Flickr refused downloads from this machine)

Licences as Openverse reports them; each must be read again on its Flickr page before use.

- cambodia4kidsorg (Beth Kanter), "Watercolor Swatching", nine photographs of a hand-painted watercolour swatch session, CC BY 2.0 (page read: https://www.flickr.com/photos/58428285@N00/53899265802; the others are 53900521204, 53900605955, 53900174396, 53899265817, 53900174471, 53900174411, 53900521209, 53899265807 under https://www.flickr.com/photos/58428285@N00/). Content not seen.
- ChrisL_AK, fountain-pen ink swatches (Waterman Audacious Red, Noodler's Fox Red, Rohrer & Klingner Fernambuk, De Atramentis Poppy Red and Oriental Red, Diamine Wild Strawberry), CC BY 2.0 per Openverse, e.g. https://www.flickr.com/photos/42769910@N00/10077773126. Ink swatches usually show shading and sheen; content not seen.
- Wikimedia Commons, Le comportement de l'aquarelle selon l'humidité du papier.png (Les.aqua, CC0; 547 x 595): a sequence of how a stroke behaves on paper from soaked ("lentille", "miroir", "brillant") to dry; every request for it was refused (HTTP 429). https://commons.wikimedia.org/wiki/File:Le_comportement_de_l%27aquarelle_selon_l%27humidit%C3%A9_du_papier.png
- Wikimedia Commons, Alcohol Marker in Use.webm (Dragonhawk12, CC BY-SA 4.0): a 14 s video of an alcohol marker drawing, 694 x 602; a frame could show marker streaks. https://commons.wikimedia.org/wiki/File:Alcohol_Marker_in_Use.webm
- Art Institute of Chicago, CC0, Winslow Homer watercolours whose records name the technique (rewetting, blotting, scraping; paper texture): e.g. After the Hurricane, Bahamas (https://www.artic.edu/artworks/16776), The Water Fan (38666), The Rapids, Hudson River (16823), Breaking Storm, Coast of Maine (16779). Their scans are 11777 px wide, but only whole images up to 3000 px could be fetched here.
