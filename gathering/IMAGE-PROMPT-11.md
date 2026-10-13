# Image generation and review — Gathering 11

Used the installed image generation tool in built-in mode, not a CLI/API fallback.
It wrote its generated motif directly to the required named artifact path;
`finish_wall11.py` then replaced that intermediate content with the complete
preserved wall. No separate motif image was retained anywhere in the workspace.
The tool was asked for 1024×1024 but returned 1774×887; the final composite keeps
the inherited wall's exact 1254×1254 square size.

Final generation prompt:

> A single isolated prehistoric cave-painting pigment motif, on a perfectly plain white background for compositing onto an existing ancestral cave wall. Motif: three small irregular red and yellow ochre pebbles at the left connected by three uneven thin charcoal trails converging into a small tied oval charcoal bundle at right, with one irregular chalk-white pebble visible within the bundle. A wide horizontal composition centered on the canvas, generous blank white margins. Represents carrying observed directed token flows into a checked handoff. Flat worn earth pigment strokes, hand-made uneven burnt-stick outlines, dry thumb ochre, sparse and primitive like Lascaux or Chauvet. Only charcoal black, red ochre, yellow ochre and faint chalk. No rock or scenery in this source motif, no shadow, no photograph, no 3D, no people, no frogs, no hands or handprints. Absolutely no text, letters, numbers, captions, logos, signature, watermark, border, frame or political symbols. This source motif will be confined to vacant rock on the supplied wall; the existing Pepe and all inherited marks must remain unchanged.

The ancestor was recovered from the newest painted gathering record, 10, using
its public artifact URL. Its SHA-256 was checked before compositing. The source
paper was removed in memory; generated pigment was area-averaged and blended
only into vacant upper-left rock `(160,150,260,105)`. This preserves all earlier
paintings without asking a generator to redraw them. The final motif uses
charcoal and red/yellow ochre; the small pale center is subdued in the composite.

Chosen review: visual inspection of both the decoded full PNG and the final
JPEG, plus full-wall pixel comparison. Result: 5,566 changed pixels, all inside
the addition rectangle, zero outside. The wall is 1254×1254 8-bit RGB PNG;
the preview is 512×512 baseline JPEG. Its artifact digest, dimensions and byte
sizes are in `checks/round-11/image-preservation.json`.

The inherited wide-mouthed, heavy-lidded Pepe remains the main figure. I counted
four fingers and one opposing thumb on each of the two inherited hands. There
are no new hands or stencils. No visible text, numbers, captions, signatures,
logos, watermark, frame, border, real person, political or hateful symbol was
found. The ancestor's rock, cracks, color, light and framing remain. No known
visual requirement is unmet. Limitations: inherited stone has a photographic-looking
texture, preserved as requested; the new thin charcoal paths are subdued at
thumbnail scale. This is local visual review, not independent certification.
