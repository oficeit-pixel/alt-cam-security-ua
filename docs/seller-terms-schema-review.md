# Seller terms: draft review, 2026-10-11

Owner decision: two possible sellers (ALT-CAM business or partner); manager selects the seller after receiving the request. This patch updates public copy and removes the premature ALT-CAM seller attribution from both Product generators. It does not deploy changes or implement admin seller selection.

Before payment, the manager must provide the legal seller/installer identity, payment recipient, final price, delivery, returns and warranty terms. A changed seller requires updated documents and customer confirmation. Partner remuneration is not described as the mechanism for direct ALT-CAM sales.

## Intentionally unresolved

- Confirm current legal identities and seller-specific terms before release. No historic tax ID has been published.
- Admin seller selection, immutable order terms snapshot and recorded customer acceptance are separate implementation work; this patch only describes the manual process.
- Do not fabricate shipping prices, return-policy scope, reviews or ratings to silence Google warnings. Public catalog prices remain unchanged and require confirmation before payment.
- Merchant listing eligibility is not guaranteed for request-only pages. Product snippet warnings may remain. Validate sample generated pages in Rich Results Test before release.
- Legal copy requires owner/legal review; this is not a compliance certification.

## Checks

`node --test tests/product-seo.test.mjs` and `node scripts/test-legal-pages.mjs` passed locally. `git diff --check` passed.

References: https://developers.google.com/search/docs/appearance/structured-data/product-snippet and https://developers.google.com/search/docs/appearance/structured-data/merchant-listing
