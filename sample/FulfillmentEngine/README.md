# FulfillmentEngine (complex-flow stress sample)

Not part of the tests or `docs/FSD.md`. Run the extractor over it to see how the skill copes with complex flows:

```
python .github/skills/webmethods-fsd/scripts/wm_extract.py --out _fsd_work/extract_complex \
  sample/OrderProcessing sample/CommonUtils sample/FulfillmentEngine
```

`fulfil.process:orchestrateFulfillment` (trigger `fulfilTrigger`) exercises: cross-package call without a
declared dependency, BRANCH with no `$default`, LOOP containing nested BRANCH/SEQUENCE, `EXIT` from
`$loop` / a named sequence / `$flow`, two TRY/CATCH pairs, `EXIT FAILURE` inside a TRY (caught by its CATCH),
`pub.flow:throwExceptionForRetry`, REPEAT with a retried failure raised by an `EXIT`, a DISABLED step,
`%var%` substitution, and a hard-coded URL.
`fulfil.util:computeShipping` has nested BRANCHes with `$null`, label expressions and `$default`.
`fulfil.process:allocateStock` has an unbounded `REPEAT COUNT="-1"` and a status BRANCH without `$default`.
