# Ethical pilot dashboard

Added four portable BenchmarkReportJSON files derived from frozen perbelief rows:
strict3seedaverage and individualseeds42/7/1729, eachwith5models,14benchmarks
and70scores. Overview:10targets,100all,80untrainedethical,10evalpreferences.
Trainedbeliefgroup contains the10individual scoped canonicalclaims. Modelpills
include dataset/trainingplan/adapter hashes, human-readableintervention anddose.

Reusable component gains absolute versus signed matchedBASEdifferences, zeroline
and percentagepoint axes, categoryfilter and optional authoredreadout. JSONschema
adds optional defaultMetric/defaultCategory; historicalreports remainvalid. Existing
barorientations,matrix,checks,examples andmodelcards retained. Fresh qualification,
control/coverage andstrictretention flags are separate. Missing orinvalidreply
blocks affectedaggregate; no partialseedpooling or neutralimputation. Available
seedreports preserve controlcomparisons. No modelcalls, training or measurement
changes. Existing dashboardoutputroot alreadyregistered before generation.

Checks:5Python+19Node tests pass;TypeScript andVite productionbuild pass. Tests
use syntheticfixtures/tempdirectories. Newtests cover matchedaverages,missing
seeds,duplicategrids,zero/missingdifferences andJSONpresentationdefaults. Initial
strictfloat assertion failed, corrected to tolerance; no scientificscore rounding
changed. Signedpresentation rounds to0.1pp; fullvalues retainedinJSON.

Liveapp http://127.0.0.1:5180/,execsession38091. Prior5175nowbelongs toanotherapp;
leftotherapps alone. Browserverified signedhorizontal/vertical axes, targetfilter,
absolutevalues, missingresults andscientificmodelmodal. Screenshot under registered
dashboardroot/ethical-pilot-overview.png.7reports loadwithoutvalidationerrors.
Sources andstudy outcomes immutable. Save/push thenprivatehandoffsave+verify.
