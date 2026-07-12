I’m writing the spec for a blog to write on the topic

Using fine tuning to observe change in model behavior and uncover biases

For example, would fine tuning with a dataset in a certain domain or bias make change the model’s identity

How to measure the model’s identity objectively → set statistical bounds for a stable identity. use seed? what should the benchmark be? how any trials are sufficient?

There’s gotta be some domain where finetuning influences the model’s priors more than others

How does the model’s identity shift with the relative change in the model’s bias

for example: does the a book on feminism change the model’s values

what is a model’s stable identity? how much is it a way of measurement (observer’s bias) vs properties of the model? Robustness parameters

- robust to language
- robust to rephrasing

What identity is most useful for safety alignment?

- consistency?
- character?
- beliefs?
- robustness in belief?
- confidence?

if we change the semantic variation of the finetuning set, how does that change identity? 

the most interesting results would be when a small finetune drastically affects identity / inhibits capabilities

weight contaimation