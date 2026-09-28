# Campus Customs — Design Changes (Problem 10)

How the visual refresh helps shoppers stay, browse longer, and come back.

## Fonts, color, and hierarchy
**What:** Rounded web fonts (Quicksand headings, Nunito body), a pastel light-blue palette with navy accents, soft rounded cards, and a clear eyebrow → headline → lead structure on every page ([frontend/src/index.css](../frontend/src/index.css), [frontend/index.html](../frontend/index.html)).

**Retention:** A calm, friendly, consistent look builds trust in the first few seconds, when most visitors decide whether to stay. Clear hierarchy tells shoppers where to look next, so fewer leave confused.

## Motion
**What:** Pages and cards gently rise in on load, and cards lift on hover. All motion respects the "reduce motion" system setting.

**Retention:** Subtle feedback makes the site feel responsive and polished, which encourages more clicking and browsing without distracting from the products.

## Product presentation
**What:** Every product photo now sits on the same clean white background, with the black backdrops and under-arm triangles removed ([output/normalize_images.py](normalize_images.py)). Card images are locked to one square size so titles, descriptions, and prices line up across the grid.

**Retention:** A tidy, uniform catalogue looks professional and is easier to scan and compare. Shoppers can browse more items in less time, and a trustworthy-looking store is more likely to earn a purchase and a return visit.

## Handsome Dan mascot and chat feel
**What:** A pixel-art Handsome Dan in a Yale sweater ([frontend/src/components/HandsomeDan.tsx](../frontend/src/components/HandsomeDan.tsx)):
- sits on the Home hero (hops on hover) and trots along the footer;
- is the chat launcher, and a winking portrait avatar in the Bulldog Assistant header that tilts his head while "thinking";
- runs back and forth under the Products and About Us headers, and hops when the cursor comes near.

**Retention:** Dan gives the shop a memorable personality tied to Yale pride, which makes the brand easier to remember and return to. His small surprises (hops, blinks, cursor reactions) reward exploration and keep visitors on the page longer. On the chat, a friendly face makes the assistant more approachable, and the "thinking" pose shows it is working, so shoppers wait for an answer instead of leaving.
