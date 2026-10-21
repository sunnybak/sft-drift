# Larger benchmark dashboard typography

Increased body copy, labels, navigation, report headings and score typography across
Dashboard and the legacy explorer. Chart tick and data labels now have a 13px minimum.
CSS label text has an 11px minimum; most supporting text is 13–15px.

Validation: production build passed; browser screenshot confirmed readable layout at
http://127.0.0.1:5174/. Preview saved as larger-type-preview.png under the registered
ethics_gpu_benchmark_dashboard_v1 derived artifact root. No experiment changes.

Preservation: commit/push followed by private handoff save and verify; consult the
handoff receipt for final revision. Next UI command: cd benchmark-dashboard && npm run dev.
