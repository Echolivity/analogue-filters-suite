# Independent review of the DSP fidelity audit

This review covers the Dub Filter v1.5 DSP fidelity audit (`docs/dsp-audit/`, commit `0689ee8`). The production DSP is untouched: `source/dubfilter.genexpr` has SHA-256 `de1bed87…a273044c`, and all golden renders are bit-exact.

**Independence caveat:** this review was produced by the same AI system that wrote the audit. Read the statement at the top of `INDEPENDENT_AUDIT_REVIEW.md`.

## Documents

| Document | Contents |
|---|---|
| [INDEPENDENT_AUDIT_REVIEW.md](INDEPENDENT_AUDIT_REVIEW.md) | Executive assessment: confirmed, re-interpreted and missing findings; methodology; confidence |
| [DSP_REMEDIATION_ASSESSMENT.md](DSP_REMEDIATION_ASSESSMENT.md) | All 15 proposed fixes: accept / modify / postpone / reject |
| [REVISED_HARDWARE_FIDELITY_SCORECARD.md](REVISED_HARDWARE_FIDELITY_SCORECARD.md) | Revised classes, and the evidence needed to improve each |
| [DSP_ARCHITECTURE_RECOMMENDATIONS.md](DSP_ARCHITECTURE_RECOMMENDATIONS.md) | Oversampling policy, implicit solve, containment, headroom, Reference/Creative modes |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Dependency-aware plan, P0–P3. **For approval.** |
| [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) | Test matrix |
| [EVIDENCE_REGISTER.md](EVIDENCE_REGISTER.md) | Every conclusion traced to code, script, data and source |

## Reproduce

```
./build.sh
source/tests/audit/run_all.sh
python3 source/tests/review/root_cause.py
python3 source/tests/review/verify.py
python3 source/tests/review/persistence.py
```

`build.sh` rewrites `docs/VALIDATION.md` and `docs/validation/results.json` with new CPU timings. Restore them with `git checkout` afterwards.
