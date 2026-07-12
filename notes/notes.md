how to measure identity
- use an existing eval that is robust to model

does finetuning affect the model's general behavior or something specific?

domain sensitivity
safety trained vs non safety trained models
finding catestrophic behavior change relative to finetuning size

domain, model, finetuning affects general behavior

fixed domain (politics)
fixed model (qwen)

how much does finetuning affect the model's behavior in __ domains?
If you do SFT for qwen on pro-abortion dataset, model becomes more politically liberal in other contexts.

scenarios:

gun control, abortion, religion, euthanasia, veganism, drugs, sex, death

model's behavior measured by pro-abortion behavior

model's behavior measured by political behavior
model's behavior measured by health behavior
model's behavior measured by feminism behavior
model's behavior measured by religion behavior

1. SFT: political manifestos, papers, reddit forums, blogs etc
2. eval: create Q&A MCQ dataset
3. measure using HoneyHive

https://arxiv.org/pdf/2411.05403

